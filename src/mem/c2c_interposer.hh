#ifndef __MEM_C2C_INTERPOSER_HH__
#define __MEM_C2C_INTERPOSER_HH__

// Incluyo el fichero de cabecera con el tipo struct para los parámetros del componente
// que se autogenera al compilar gem5 a partir de c2c_interposer.py.
#include "params/C2CInterposer.hh"

// C2CInterposer hereda de ClockedObject para poder convertir ciclos a ticks
// y programar eventos internos en el event queue de gem5.
#include "sim/clocked_object.hh"
#include "sim/eventq.hh"

// Incluye Packet y PacketPtr.
#include "mem/packet.hh"

// Incluye RequestPort y ResponsePort.
#include "mem/port.hh"

// Para AddrRange y AddrRangeList.
#include "base/addr_range.hh"

#include <algorithm>
#include <cstdint>
#include <deque>
#include <map>
#include <memory>
#include <string>
#include <utility>
#include <vector>
#include <cstdint>

#include "mem/ruby/common/MachineID.hh"
#include "mem/ruby/protocol/C2cRequestType.hh"

namespace gem5 {

/*
 * C2CInterposer
 * -------------
 * NUEVA IDEA:
 * Antes este SimObject modelaba un enlace punto a punto:
 *     Interface0 <-> Interposer <-> Interface1
 *
 * Ahora modela una única entidad central tipo MUX/interposer:
 *
 *     Chip 0 Interface ----\
 *     Chip 1 Interface ----- C2CInterposer ---- routing interno
 *     Chip 2 Interface ----/
 *
 * Cada chip se conecta al MUX mediante dos puertos:
 *   - from_interfaces[i]: por aquí el MUX recibe timing requests desde el chip i.
 *   - to_interfaces[i]:   por aquí el MUX envía timing requests hacia el chip i.
 *
 * Las respuestas siguen el protocolo normal de gem5:
 *   - Si el MUX manda una request por to_interfaces[dest], recibirá la response
 *     de ese destino por ToInterfacePort::recvTimingResp().
 *   - Luego el MUX reenvía esa response al chip correspondiente usando
 *     from_interfaces[src].sendTimingResp().
 */
class C2CInterposer : public ClockedObject
{
  private:
    class ToInterfacePort;
    class FromInterfacePort;

    /*
     * Puerto de salida hacia un chip.
     * Hereda de RequestPort porque el MUX inicia el envío hacia la interfaz C2C
     * del chip destino.
     */
    class ToInterfacePort : public RequestPort
    {
      private:
        C2CInterposer *owner;
        int side; // chipID asociado a este puerto

      public:
        ToInterfacePort(const std::string &name, C2CInterposer *owner, int side);

        // Cuando el chip destino responde a una request enviada por este puerto,
        // la respuesta entra aquí y el MUX decide a qué chip devolverla.
        bool recvTimingResp(PacketPtr pkt) override;

        // Backpressure: el chip destino avisa que ya puede aceptar otra request.
        void recvReqRetry() override;
    };

    /*
     * Puerto de entrada desde un chip.
     * Hereda de ResponsePort porque desde el punto de vista del chip origen,
     * el MUX es el receptor de sus requests C2C.
     */
    class FromInterfacePort : public ResponsePort
    {
      private:
        C2CInterposer *owner;
        int side; // chipID asociado a este puerto

      public:
        FromInterfacePort(const std::string &name, C2CInterposer *owner, int side);

        AddrRangeList getAddrRanges() const override;
        void recvFunctional(PacketPtr pkt) override;
        bool recvTimingReq(PacketPtr pkt) override;
        void recvRespRetry() override;
        Tick recvAtomic(PacketPtr pkt) override;
    };

    // NUEVO:
    // Puertos vectoriales. El índice coincide con el chipID.
    std::vector<ToInterfacePort *> toInterfacePorts;
    std::vector<FromInterfacePort *> fromInterfacePorts;

    const unsigned numInterfaces;
    const Cycles reqLatency;
    const Cycles respLatency;
    const unsigned reqBufferSize;
    const unsigned respBufferSize;

    std::vector<AddrRange> c2cMemRanges;
    std::vector<int> cacheChipIDList;
    std::vector<int> interfaceChipIDList;

    struct BufferedPkt
    {
        PacketPtr pkt;
        Tick readyTick;
        int srcSide;
        int dstSide;
    };

    // Clase lógica del mensaje C2C. Es la agrupación que ya estabas usando
    // para separar los 4 canales virtuales lógicos del tráfico CHI/C2C.
    enum class C2cMsgClass
    {
        Request = 0,
        Snoop = 1,
        Response = 2,
        Data = 3
    };

    /*
     * Buffer de salida hacia un chip concreto.
     *
     * Hay dos familias de buffers:
     *   - reqTo[chip]:  tráfico Request/Snoop que saldrá hacia chip.
     *   - respTo[chip]: tráfico Response/Data que saldrá hacia chip.
     *
     * Dentro de cada DirBuffer hay una cola por clase lógica:
     *   Request, Snoop, Response, Data.
     *
     * El Round Robin se aplica entre esas clases dentro del mismo destino.
     */
    struct DirBuffer
    {
        std::map<C2cMsgClass, std::deque<BufferedPkt>> queues;
        bool waitingRetry = false;
        int lastServedClass = -1;
        EventFunctionWrapper processEvent;

        DirBuffer(EventFunctionWrapper&& ev) : processEvent(std::move(ev)) {}

        bool empty() const
        {
            for (const auto &entry : queues) {
                if (!entry.second.empty()) {
                    return false;
                }
            }
            return true;
        }

        size_t totalSize() const
        {
            size_t total = 0;
            for (const auto &entry : queues) {
                total += entry.second.size();
            }
            return total;
        }
    };

    std::vector<std::unique_ptr<DirBuffer>> reqTo;
    std::vector<std::unique_ptr<DirBuffer>> respTo;

    //componentes 
    std::vector<std::string> cacheComponentNameList;

    std::string machineIdToDebugString(const ruby::MachineID &mach) const;

    void printC2cMsgDebug(PacketPtr pkt,
                      const char *tag,
                      int srcSide,
                      int dstSide) const;
                      
    /*
    * Identificador único de cada intento físico de envío de una response.
    * Sirve solo para depuración.
    */
    uint64_t responseSendSequence = 0;

    // Entrada principal para timing requests desde un chip.
    bool recvReqFromInterface(PacketPtr pkt, int srcSide);

    // Entrada principal para timing responses recibidas desde un chip.
    bool recvRespFromInterface(PacketPtr pkt, int responderSide);

    // Retry recibido desde un chip destino para requests.
    void recvReqRetryToInterface(int dstSide);

    // Retry recibido desde un chip origen para responses.
    void recvRespRetryFromInterface(int srcSide);

    Tick recvAtomicFromInterface(PacketPtr pkt, int srcSide);

    void processReqTo(int dstSide);
    void processRespTo(int dstSide);
    void trySendReqTo(int dstSide);
    void trySendRespTo(int dstSide);

    void scheduleBufferEvent(DirBuffer &buf, Tick when);

    C2cMsgClass classifyC2cType(ruby::C2cRequestType type) const;
    C2cMsgClass getPacketClass(PacketPtr pkt) const;
    const char* getClassName(C2cMsgClass msgClass) const;

    bool enqueuePacket(DirBuffer &buf, PacketPtr pkt, Tick delay,
                       unsigned maxSize, const char *path,
                       int srcSide, int dstSide);

    int selectNextTypeRR(DirBuffer &buf, Tick now);
    Tick nextReadyTick(const DirBuffer &buf) const;

    // Routing.
    int routeRequest(PacketPtr pkt, int srcSide) const;
    int routeResponse(PacketPtr pkt, int responderSide) const;
    int routeByDestinationField(PacketPtr pkt, int incomingSide) const;
    int routeByAddress(PacketPtr pkt, int incomingSide) const;
    int routeByC2cDestination(PacketPtr pkt, int srcSide) const;
    // En Ruby, MachineID vive dentro del namespace gem5::ruby.
    // Lo usamos para saber a qué chip pertenece un controlador Cache o Interface.
    int routeByMachineID(const ruby::MachineID &mach, int fallback) const;
    bool validSide(int side) const;

    void printRoutingInfo(PacketPtr pkt, const char *where, int srcSide, int dstSide) const;

    struct TypeStats
    {
        uint64_t reqFrom[16] = {0};
        uint64_t respFrom[16] = {0};
    };

    std::map<int, TypeStats> c2cTypeStats;
    void recordC2cType(PacketPtr pkt, const char* path, int srcSide);
    void dumpC2cTypeStats() const;

  public:
    C2CInterposer(const C2CInterposerParams &params);
    ~C2CInterposer() override;

    Port &getPort(const std::string &if_name, PortID idx = InvalidPortID) override;
};

} // namespace gem5

#endif
