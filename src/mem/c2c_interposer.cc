/*Incluimos el fichero de cabecera que creamos antes.*/
#include "mem/c2c_interposer.hh"
//incluye panic()
#include "base/logging.hh"
#include "base/trace.hh"

#include <sstream>
#include "debug/C2CInterposer.hh"

#include <iomanip>
#include "mem/ruby/protocol/C2cMsg.hh"
#include "mem/ruby/protocol/C2cRequestType.hh"

/*Vamos a realizar 2 cosas
1. Definir un constructor
2. Definir una lista de inicialización ( : ... , ...) que es una forma 
de realizar la asignación/incialización de variables de una clase den c++*/

//usamos el namespace de gem5 (debe coincidir con el que usamos 
//en python: cxx_class = "gem5::C2CInterposer")
namespace gem5 {

static std::string
pktToString(PacketPtr pkt)
{
    if (!pkt) {
        return "pkt=null";
    }

    std::ostringstream oss;

    oss << "pkt=" << pkt
        << " addr=0x" << std::hex << pkt->getAddr() << std::dec
        << " cmd=" << pkt->cmdString()
        << " size=" << pkt->getSize()
        << " isReq=" << pkt->isRequest()
        << " isResp=" << pkt->isResponse()
        << " needsResp=" << pkt->needsResponse()
        << " cacheResp=" << pkt->cacheResponding()
        << " hasData=" << pkt->hasData()
        << " headerDelay=" << pkt->headerDelay
        << " payloadDelay=" << pkt->payloadDelay
        << " req=" << pkt->req;

    return oss.str();
}

//ver el tipo del paquete 
static bool
hasC2cMsg(PacketPtr pkt)
{
    return pkt && pkt->c2c_msg;
}

static int
getC2cTypeId(PacketPtr pkt)
{
    assert(pkt && pkt->c2c_msg);
    return static_cast<int>(pkt->c2c_msg->m_Type);
}

static std::string
getC2cTypeName(PacketPtr pkt)
{
    if (!pkt || !pkt->c2c_msg) {
        return "NO_C2C_MSG";
    }

    return ruby::C2cRequestType_to_string(pkt->c2c_msg->m_Type);
}

/*Usamos el operador de resolución de ámbito "::" en "C2CInterposer::FromInterfacePort(...)"
para indicar que vamos a acceder a la clase privada que está dentro de C2CInterposer y luego
volvemos a usar el operador de ámbito "::" para definir el constructor de esa clase
así "FromInterfacePort::FromInterfacePort(...)". Resto lo hacemos porque en el fichero de cabecera del componente declaré la clase así:
class C2CInterposer la cual dentro tiene como miembro privado la clase "FromInterfacePort"
Y ahora en este .cc lo estoy definiendo, por eso uso el "::", porque
estoy fuera del cuerpo de la clase.
*/
C2CInterposer::FromInterfacePort::FromInterfacePort(
    const std::string &name,
    C2CInterposer *owner,
    int side
) : ResponsePort(name, owner), //construimos el objeto con la lista de inicialización
    owner(owner),
    side(side)
{
}

//Si se te olvida alguno de estos métodos, tengo su explicaión en el oneNote 
//en "creación interposer"

/*------------------------------------------------------------*/
//        FromInterfacePort métodos: Hereda de RespondePort               
/*------------------------------------------------------------*/

//Devuelve una lista de rangos de memoria 
AddrRangeList C2CInterposer::FromInterfacePort::getAddrRanges() const
{
    std::cerr << "[Interposer] getAddrRanges side=" << side << std::endl;
    
    if (side == 0) {
        return owner->toInterface1Port->getAddrRanges();
    } else {
        return owner->toInterface0Port->getAddrRanges();
    }
}

//no implemento acceso funcionales, si se intentara hacer ocurre un panic
void C2CInterposer::FromInterfacePort::recvFunctional(PacketPtr pkt)
{
    panic("C2CInterposer::FromInterfacePort::recvFunctional not implemented");
}

//Sirve para determinar de qué lado recibo el packet para una Request tipo timing
//una vez determinado el lado, el procesamiento del packet lo hace el interposer 
//accediendo a un método miembro de él a través del "->". Esa función simplemente
//enviará el packet al otro lado del interposer
bool C2CInterposer::FromInterfacePort::recvTimingReq(PacketPtr pkt)
{
    if (side == 0) {
        return owner->recvReqFromInterface0(pkt);
    } else {
        return owner->recvReqFromInterface1(pkt);
    }
}

/*Esta función recibe la señal mandada por el emisor/ResponsePort la cual le 
indica al ResponsePort que puede volver a mandar la Response que fue rechazada 
previamente. Ojo, esta función solo le da el aviso, luego tendrá que ejecutar el
 ReponsePort la función correspondiente para mandar la Response otra vez.
 Dependiendo del lado que reciba la señal, la reenviaré al otro*/
void C2CInterposer::FromInterfacePort::recvRespRetry()
{
    if (side == 0) {
        owner->recvRespRetryFromInterface0();
    } else {
        owner->recvRespRetryFromInterface1();
    }
}

Tick C2CInterposer::FromInterfacePort::recvAtomic(PacketPtr pkt)
{
    if (side == 0) {
        return owner->recvAtomicFromInterface0(pkt);
    } else {
        return owner->recvAtomicFromInterface1(pkt);
    }
}

Tick C2CInterposer::recvAtomicFromInterface0(PacketPtr pkt)
{
    return toInterface1Port->sendAtomic(pkt);
}

Tick C2CInterposer::recvAtomicFromInterface1(PacketPtr pkt)
{
    return toInterface0Port->sendAtomic(pkt);
}

/*------------------------------------------------------------*/
//          ToInterfacePort métodos y definición de su constructor                 
/*------------------------------------------------------------*/

/*Defino el constructor de ToInterfacePort que hereda de RequestPort.
Es basicamente lo mismo que el FromInterfacePort*/
C2CInterposer::ToInterfacePort::ToInterfacePort(
    const std::string &name,
    C2CInterposer *owner,
    int side
) : RequestPort(name, owner), //construimos el objeto con la lista de inicialización
    owner(owner),
    side(side)
{
}

/*Sirve para recibir una Response de una Timing Request, dependiendo 
del lado que reciba la response se tiene que reenviar al otro*/
bool C2CInterposer::ToInterfacePort::recvTimingResp(PacketPtr pkt)
{
    if (side == 0) {
        return owner->recvRespFromInterface0(pkt);
    } else {
        return owner->recvRespFromInterface1(pkt);
    }
}

/*Se usa para avisar al RequestPort del otro lado del C2CI que puede
volver a mandar la Response que antes no se pudo recibir, para que la 
reenvíe. Dependiendo del lado que recibamos esta señal, la reenvíamos al otro*/
void C2CInterposer::ToInterfacePort::recvReqRetry()
{
    if (side == 0) {
        owner->recvReqRetryToInterface0();
    } else {
        owner->recvReqRetryToInterface1();
    }
}

/*-----------------------------------------------------------*/
//               métodos del C2CInterposer                 
/*------------------------------------------------------------*/

/*Constructor de la clase C2CInterposer,si en el fichero 
de creación del SimObject en python hubieramos definido parámetros, 
esto se recibirían en &params, en este caso no se ha hecho pero igual se
pone */
C2CInterposer::C2CInterposer(const C2CInterposerParams &params)
    : ClockedObject(params),
      toInterface0Port(nullptr),
      fromInterface0Port(nullptr),
      toInterface1Port(nullptr),
      fromInterface1Port(nullptr),
      reqLatency(params.req_latency),
      respLatency(params.resp_latency),
      reqBufferSize(params.req_buffer_size),
      respBufferSize(params.resp_buffer_size),
      req0to1(DirBuffer(EventFunctionWrapper(
          [this] { processReq0to1(); }, name() + ".processReq0to1"))),
      req1to0(DirBuffer(EventFunctionWrapper(
          [this] { processReq1to0(); }, name() + ".processReq1to0"))),
      resp0to1(DirBuffer(EventFunctionWrapper(
          [this] { processResp0to1(); }, name() + ".processResp0to1"))),
      resp1to0(DirBuffer(EventFunctionWrapper(
          [this] { processResp1to0(); }, name() + ".processResp1to0")))
{
    //debug
    std::cerr << "[Interposer] constructor called" << std::endl;

    /*Recuerda que el constructor de la clase FromInterfacePort era: 

    C2CInterposer::FromInterfacePort::FromInterfacePort(
    const std::string &name, //nombre del puerto
    C2CInterposer *owner, //puntero al interposer dueño
    int side //el lado del interposer (0 o 1)
    
    y lo que hacemos crear un nuevo objeto de esta
    */

    //puerto de ResponsePort del lado 0
    fromInterface0Port = new FromInterfacePort(
        csprintf("%s.from_interface0_port", name()),
        this,
        0
    );

    //puerto de RequestPort del lado 0
    toInterface0Port = new ToInterfacePort(
        csprintf("%s.to_interface0_port", name()),
        this,
        0
    );

    //puerto de ResponsePort del lado 1
    fromInterface1Port = new FromInterfacePort(
        csprintf("%s.from_interface1_port", name()),
        this,
        1
    );

    //puerto de ResponsePort del lado 1
    toInterface1Port = new ToInterfacePort(
        csprintf("%s.to_interface1_port", name()),
        this,
        1
    );
}

//destructor 
C2CInterposer::~C2CInterposer()
{
    dumpC2cTypeStats();
}

/*Método de la clase C2CInterposer para acceder a los puertos (atributos) de 
este, para ello devuelve el puntero a ese puerto (Port &) al mandarle el nombre*/
Port & C2CInterposer::getPort(const std::string &if_name, PortID idx)
{
    if (if_name == "from_interface0_port") {
        return *fromInterface0Port;
    } else if (if_name == "to_interface0_port") {
        return *toInterface0Port;
    } else if (if_name == "from_interface1_port") {
        return *fromInterface1Port;
    } else if (if_name == "to_interface1_port") {
        return *toInterface1Port;
    }

    /*si no se encuentra ningún puntero con ese nombre, se delega en la clase
    base. Recuerda, C2CInterposer hereda de SimObject, entonces la clase 
    base ya tiene una implementación de ese método!!! pero nosotros 
    hicimos un override de ese método en C2CInterposer, pero al hacer esto 
    llamamos al método "original" que puede tener otros puertos definidos*/
    return ClockedObject::getPort(if_name, idx);
}

//contar el tipo de mensajes que me ha llegado 
void
C2CInterposer::recordC2cType(PacketPtr pkt, const char* path)
{
    if (!hasC2cMsg(pkt)) {
        std::cout << "[Interposer] " << path
                  << " type=NO_C2C_MSG "
                  << pktToString(pkt) << "\n";
        return;
    }

    const int typeId = getC2cTypeId(pkt);
    const std::string typeName = getC2cTypeName(pkt);

    auto &stats = c2cTypeStats[typeId];

    if (std::string(path) == "REQ 0->1 enqueue") {
        stats.reqFrom0++;
    } else if (std::string(path) == "REQ 1->0 enqueue") {
        stats.reqFrom1++;
    } else if (std::string(path) == "RESP 0->1 enqueue") {
        stats.respFrom0++;
    } else if (std::string(path) == "RESP 1->0 enqueue") {
        stats.respFrom1++;
    }

    std::cout << "[Interposer] " << path
              << " c2c_type=" << typeName
              << " type_id=" << typeId
              << " " << pktToString(pkt)
              << "\n";
}

void
C2CInterposer::dumpC2cTypeStats() const
{
    std::cout << "\n========== C2C TYPE STATS ==========\n";

    if (c2cTypeStats.empty()) {
        std::cout << "No C2C packets recorded.\n";
        std::cout << "====================================\n";
        return;
    }

    for (const auto &entry : c2cTypeStats) {
        const int typeId = entry.first;
        const TypeStats &s = entry.second;

        auto type = static_cast<gem5::ruby::C2cRequestType>(typeId);

        std::cout << "type_id=" << std::setw(3) << typeId
                  << " type_name=" << gem5::ruby::C2cRequestType_to_string(type)
                  << " reqFrom0=" << s.reqFrom0
                  << " reqFrom1=" << s.reqFrom1
                  << " respFrom0=" << s.respFrom0
                  << " respFrom1=" << s.respFrom1
                  << "\n";
    }

    std::cout << "====================================\n";
}

// ---------------- NUEVO ----------------
// helper para obtener el tipo del paquete
//para obtener nombre legible de la clase lógica
const char*
C2CInterposer::getClassName(C2cMsgClass msgClass) const
{
    switch (msgClass) {
      case C2cMsgClass::Request:  return "Request";
      case C2cMsgClass::Snoop:    return "Snoop";
      case C2cMsgClass::Response: return "Response";
      case C2cMsgClass::Data:     return "Data";
    }

    return "Unknown";
}

// helper para clasificar el tipo real CHI en una de las 4 clases lógicas
C2CInterposer::C2cMsgClass
C2CInterposer::classifyC2cType(ruby::C2cRequestType type) const
{
    using namespace ruby;

    if (type == C2cRequestType_ReadShared ||
        type == C2cRequestType_ReadOnce ||
        type == C2cRequestType_ReadUnique ||
        type == C2cRequestType_CleanUnique ||
        type == C2cRequestType_Evict ||
        type == C2cRequestType_WriteEvictFull ||
        type == C2cRequestType_WriteUniqueFull ||
        type == C2cRequestType_WriteBackFull) {
        return C2cMsgClass::Request;
    } else if (type == C2cRequestType_SnpCleanInvalid ||
               type == C2cRequestType_SnpUnique ||
               type == C2cRequestType_SnpSharedFwd ||
               type == C2cRequestType_SnpUniqueFwd ||
               type == C2cRequestType_SnpOnceFwd) {
        return C2cMsgClass::Snoop;
    } else if (type == C2cRequestType_CompData_UC ||
               type == C2cRequestType_CompData_I ||
               type == C2cRequestType_CompData_SC ||
               type == C2cRequestType_CompData_SD_PD ||
               type == C2cRequestType_CompData_UD_PD ||
               type == C2cRequestType_NCBWrData ||
               type == C2cRequestType_CBWrData_UC ||
               type == C2cRequestType_CBWrData_SC ||
               type == C2cRequestType_CBWrData_I ||
               type == C2cRequestType_CBWrData_SD_PD ||
               type == C2cRequestType_CBWrData_UD_PD ||
               type == C2cRequestType_SnpRespData_I_PD ||
               type == C2cRequestType_SnpRespData_I ||
               type == C2cRequestType_SnpRespData_SC_PD ||
               type == C2cRequestType_SnpRespData_SC ||
               type == C2cRequestType_SnpRespData_SD ||
               type == C2cRequestType_SnpRespData_UC ||
               type == C2cRequestType_SnpRespData_UD ||
               type == C2cRequestType_SnpRespData_SC_Fwded_SD_PD ||
               type == C2cRequestType_SnpRespData_SC_Fwded_SC ||
               type == C2cRequestType_SnpRespData_SC_PD_Fwded_SC ||
               type == C2cRequestType_SnpRespData_I_Fwded_SD_PD ||
               type == C2cRequestType_SnpRespData_I_PD_Fwded_SC ||
               type == C2cRequestType_SnpRespData_I_Fwded_SC) {
        return C2cMsgClass::Data;
    } else if (type == C2cRequestType_CompAck ||
               type == C2cRequestType_CompDBIDResp ||
               type == C2cRequestType_RetryAck ||
               type == C2cRequestType_PCrdGrant ||
               type == C2cRequestType_Comp_I ||
               type == C2cRequestType_Comp_UC ||
               type == C2cRequestType_SnpResp_I ||
               type == C2cRequestType_SnpResp_I_Fwded_UD_PD ||
               type == C2cRequestType_SnpResp_I_Fwded_UC ||
               type == C2cRequestType_SnpResp_SC_Fwded_SC ||
               type == C2cRequestType_SnpResp_SC_Fwded_SD_PD ||
               type == C2cRequestType_SnpResp_SD_Fwded_I ||
               type == C2cRequestType_SnpResp_SC_Fwded_I ||
               type == C2cRequestType_SnpResp_UD_Fwded_I ||
               type == C2cRequestType_SnpResp_UC_Fwded_I ||
               type == C2cRequestType_ReqAck) {
        return C2cMsgClass::Response;
    } else {
        panic("Invalid C2c request type in C2CInterposer classification: %s",
              ruby::C2cRequestType_to_string(type).c_str());
        return C2cMsgClass::Request;
    }
}

// helper para obtener la clase lógica del paquete
C2CInterposer::C2cMsgClass
C2CInterposer::getPacketClass(PacketPtr pkt) const
{
    if (!hasC2cMsg(pkt)) {
        panic("Packet without c2c_msg in C2CInterposer");
    }

    return classifyC2cType(pkt->c2c_msg->m_Type);
}
// ---------------- FIN NUEVO ----------------

// helper para obtener el menor readyTick entre todas las colas
Tick
C2CInterposer::nextReadyTick(const DirBuffer &buf) const
{
    Tick best = MaxTick;
    bool found = false;

    for (const auto &entry : buf.queues) {
        const auto &q = entry.second;
        if (!q.empty()) {
            best = std::min(best, q.front().readyTick);
            found = true;
        }
    }

    return found ? best : MaxTick;
}

// helper para elegir el siguiente tipo según Round Robin
// El Round Robin, cuando una cola está vacía, pasa a la siguiente.
// Así, si sólo hay una cola ocupada, transmite continuamente desde dicha cola
// (aunque en cada intento revisa las demás, saltándolas).
int
C2CInterposer::selectNextTypeRR(DirBuffer &buf, Tick now)
{
    std::vector<int> candidates;

    for (const auto &entry : buf.queues) {
        const int classId = static_cast<int>(entry.first);
        const auto &q = entry.second;

        if (!q.empty() && q.front().readyTick <= now) {
            candidates.push_back(classId);
        }
    }

    if (candidates.empty()) {
        return -2; // no hay ninguna cola lista todavía
    }

    std::sort(candidates.begin(), candidates.end());

    // si nunca se ha servido nada todavía
    if (buf.lastServedClass == -1) {
        return candidates.front();
    }

    // busco la siguiente cola con classId mayor que la última servida
    for (int c : candidates) {
        if (c > buf.lastServedClass) {
            return c;
        }
    }

    // si no hay ninguna mayor, hago wrap-around
    return candidates.front();
}

// helper para encolar en la cola de la clase correspondiente
bool
C2CInterposer::enqueueTypedPacket(DirBuffer &buf, PacketPtr pkt, Tick delay,
                                  unsigned maxSize, const char *path)
{
    const int typeId = getC2cTypeId(pkt);
    const std::string typeName = getC2cTypeName(pkt);
    const C2cMsgClass msgClass = getPacketClass(pkt);
    auto &q = buf.queues[msgClass];

    // Ahora el tamaño máximo se aplica a la cola de ESTA clase,
    // no al total de colas de la dirección.
    if (q.size() >= maxSize) {
        std::cout << "[Interposer] " << path
                  << " BUFFER FULL"
                  << " class=" << getClassName(msgClass)
                  << " type_id=" << typeId
                  << " type_name=" << typeName
                  << " class_occ=" << q.size()
                  << "/" << maxSize
                  << " total_occ=" << buf.totalSize()
                  << " addr=0x" << std::hex << pkt->getAddr()
                  << std::dec << "\n";
        return false;
    }

    pkt->headerDelay += delay;

    Tick ready = curTick() + delay;
    q.push_back({pkt, ready});

    std::cout << "[Interposer] " << path
              << " class=" << getClassName(msgClass)
              << " type_id=" << typeId
              << " type_name=" << typeName
              << " add_delay=" << delay
              << " class_occ=" << q.size()
              << "/" << maxSize
              << " total_occ=" << buf.totalSize()
              << " addr=0x" << std::hex << pkt->getAddr()
              << std::dec << "\n";

    Tick when = nextReadyTick(buf);
    if (when != MaxTick) {
        scheduleBufferEvent(buf, when);
    }

    return true;
}
// ---------------- FIN NUEVO ----------------

/*-----------------------------------------------------------*/
//                 Lógica de reenvío de Request (bridge de Request)    
//                  cualquier duda de esta zona, ver apuntes sobre la latencia           
/*------------------------------------------------------------*/

/*Si llega una request desde la interfaz 0 lo reenvío a la 1 inmediatamente*/
bool
C2CInterposer::recvReqFromInterface0(PacketPtr pkt)
{
    // Interfaz0 -> Interfaz1

    recordC2cType(pkt, "REQ 0->1 enqueue");

    Tick delay = cyclesToTicks(reqLatency);

    // ---------------- NUEVO ----------------
    return enqueueTypedPacket(req0to1, pkt, delay, reqBufferSize, "REQ 0->1");
    // ---------------- FIN NUEVO ----------------
}

/*Si llega una request desde la interfaz 1 lo reenvío a la 0 inmediatamente*/
bool
C2CInterposer::recvReqFromInterface1(PacketPtr pkt)
{
    // Interfaz1 -> Interfaz0

    recordC2cType(pkt, "REQ 1->0 enqueue");

    Tick delay = cyclesToTicks(reqLatency);

    // ---------------- NUEVO ----------------
    return enqueueTypedPacket(req1to0, pkt, delay, reqBufferSize, "REQ 1->0");
    // ---------------- FIN NUEVO ----------------
}

/*-----------------------------------------------------------*/
//              Lógica de reenvío de Response (bridge de Response)   
//              cualquier duda de esta zona, ver apuntes sobre la latencia             
/*-----------------------------------------------------------*/

/*Si llega una Response desde la interfaz 0 lo reenvío a la 1 inmediatamente*/
bool
C2CInterposer::recvRespFromInterface0(PacketPtr pkt)
{
    // Respuesta que vuelve desde Interface0 hacia Interfaz1

    recordC2cType(pkt, "RESP 0->1 enqueue");

    Tick delay = cyclesToTicks(respLatency);

    // ---------------- NUEVO ----------------
    return enqueueTypedPacket(resp0to1, pkt, delay, respBufferSize, "RESP 0->1");
    // ---------------- FIN NUEVO ----------------
}

/*Si llega una Responset desde la interfaz 1 lo reenvío a la 0 inmediatamente*/
bool
C2CInterposer::recvRespFromInterface1(PacketPtr pkt)
{
    // Respuesta que vuelve desde Interface1 hacia Interfaz0

    recordC2cType(pkt, "RESP 1->0 enqueue");

    Tick delay = cyclesToTicks(respLatency);

    // ---------------- NUEVO ----------------
    return enqueueTypedPacket(resp1to0, pkt, delay, respBufferSize, "RESP 1->0");
    // ---------------- FIN NUEVO ----------------
}

/*-----------------------------------------------------------*/
//                Reenvío de Request de Retry                  
/*--------------------------------------------------------------*/

void
C2CInterposer::recvReqRetryToInterface0()
{
    std::cout << "[Interposer] RETRY REQ to interface0\n";
    req1to0.waitingRetry = false;
    trySendReq1to0();
}

void
C2CInterposer::recvReqRetryToInterface1()
{
    std::cout << "[Interposer] RETRY REQ to interface1\n";
    req0to1.waitingRetry = false;
    trySendReq0to1();
}

void
C2CInterposer::recvRespRetryFromInterface0()
{
    std::cout << "[Interposer] RETRY RESP from interface0\n";
    resp1to0.waitingRetry = false;
    trySendResp1to0();
}

void
C2CInterposer::recvRespRetryFromInterface1()
{
    std::cout << "[Interposer] RETRY RESP from interface1\n";
    resp0to1.waitingRetry = false;
    trySendResp0to1();
}

/*------------------------------------------------------------*/
/* Scheduling helpers                                          */
/*------------------------------------------------------------*/

void
C2CInterposer::processReq0to1()
{
    trySendReq0to1();
}

void
C2CInterposer::processReq1to0()
{
    trySendReq1to0();
}

void
C2CInterposer::processResp0to1()
{
    trySendResp0to1();
}

void
C2CInterposer::processResp1to0()
{
    trySendResp1to0();
}

void
C2CInterposer::trySendReq0to1()
{
    // ---------------- NUEVO ----------------
    if (req0to1.empty()) {
        return;
    }

    if (req0to1.waitingRetry) {
        return;
    }

    int classId = selectNextTypeRR(req0to1, curTick());

    if (classId == -2) {
        Tick when = nextReadyTick(req0to1);
        if (when != MaxTick) {
            scheduleBufferEvent(req0to1, when);
        }
        return;
    }

    C2cMsgClass msgClass = static_cast<C2cMsgClass>(classId);
    auto &q = req0to1.queues[msgClass];
    auto &front = q.front();

    if (!toInterface1Port->sendTimingReq(front.pkt)) {
        req0to1.waitingRetry = true;
        return;
    }

    // Guardo el tamaño anterior para saber si esta cola estaba llena
    size_t oldSize = q.size();

    q.pop_front();
    req0to1.lastServedClass = classId;

    // Si esta cola estaba llena y ahora ya no, aviso al productor
    // de interface0 para que reintente mandar su request.
    if (oldSize == reqBufferSize) {
        std::cout << "[Interposer] RELEASE REQ 0->1"
                  << " class=" << getClassName(msgClass)
                  << " -> sendRetryReq to interface0\n";
        fromInterface0Port->sendRetryReq();
    }

    if (q.empty()) {
        req0to1.queues.erase(msgClass);
    }

    Tick when = nextReadyTick(req0to1);
    if (when != MaxTick) {
        scheduleBufferEvent(req0to1, std::max(curTick(), when));
    }
    // ---------------- FIN NUEVO ----------------
}

void
C2CInterposer::trySendReq1to0()
{
    // ---------------- NUEVO ----------------
    if (req1to0.empty()) {
        return;
    }

    if (req1to0.waitingRetry) {
        return;
    }

    int classId = selectNextTypeRR(req1to0, curTick());

    if (classId == -2) {
        Tick when = nextReadyTick(req1to0);
        if (when != MaxTick) {
            scheduleBufferEvent(req1to0, when);
        }
        return;
    }

    C2cMsgClass msgClass = static_cast<C2cMsgClass>(classId);
    auto &q = req1to0.queues[msgClass];
    auto &front = q.front();

    if (!toInterface0Port->sendTimingReq(front.pkt)) {
        req1to0.waitingRetry = true;
        return;
    }

    // Guardo el tamaño anterior para saber si esta cola estaba llena
    size_t oldSize = q.size();

    q.pop_front();
    req1to0.lastServedClass = classId;

    // Si esta cola estaba llena y ahora ya no, aviso al productor
    // de interface1 para que reintente mandar su request.
    if (oldSize == reqBufferSize) {
        std::cout << "[Interposer] RELEASE REQ 1->0"
                  << " class=" << getClassName(msgClass)
                  << " -> sendRetryReq to interface1\n";
        fromInterface1Port->sendRetryReq();
    }

    if (q.empty()) {
        req1to0.queues.erase(msgClass);
    }

    Tick when = nextReadyTick(req1to0);
    if (when != MaxTick) {
        scheduleBufferEvent(req1to0, std::max(curTick(), when));
    }
    // ---------------- FIN NUEVO ----------------
}

void
C2CInterposer::trySendResp0to1()
{
    // ---------------- NUEVO ----------------
    if (resp0to1.empty()) {
        return;
    }

    if (resp0to1.waitingRetry) {
        return;
    }

    int classId = selectNextTypeRR(resp0to1, curTick());

    if (classId == -2) {
        Tick when = nextReadyTick(resp0to1);
        if (when != MaxTick) {
            scheduleBufferEvent(resp0to1, when);
        }
        return;
    }

    C2cMsgClass msgClass = static_cast<C2cMsgClass>(classId);
    auto &q = resp0to1.queues[msgClass];
    auto &front = q.front();

    if (!fromInterface1Port->sendTimingResp(front.pkt)) {
        resp0to1.waitingRetry = true;
        return;
    }

    // Guardo el tamaño anterior para saber si esta cola estaba llena
    size_t oldSize = q.size();

    q.pop_front();
    resp0to1.lastServedClass = classId;

    // Si esta cola estaba llena y ahora ya no, aviso al productor
    // de la response del lado 0 para que reintente.
    if (oldSize == respBufferSize) {
        std::cout << "[Interposer] RELEASE RESP 0->1"
                  << " class=" << getClassName(msgClass)
                  << " -> sendRetryResp to interface0\n";
        toInterface0Port->sendRetryResp();
    }

    if (q.empty()) {
        resp0to1.queues.erase(msgClass);
    }

    Tick when = nextReadyTick(resp0to1);
    if (when != MaxTick) {
        scheduleBufferEvent(resp0to1, std::max(curTick(), when));
    }
    // ---------------- FIN NUEVO ----------------
}

void
C2CInterposer::trySendResp1to0()
{
    // ---------------- NUEVO ----------------
    if (resp1to0.empty()) {
        return;
    }

    if (resp1to0.waitingRetry) {
        return;
    }

    int classId = selectNextTypeRR(resp1to0, curTick());

    if (classId == -2) {
        Tick when = nextReadyTick(resp1to0);
        if (when != MaxTick) {
            scheduleBufferEvent(resp1to0, when);
        }
        return;
    }

    C2cMsgClass msgClass = static_cast<C2cMsgClass>(classId);
    auto &q = resp1to0.queues[msgClass];
    auto &front = q.front();

    if (!fromInterface0Port->sendTimingResp(front.pkt)) {
        resp1to0.waitingRetry = true;
        return;
    }

    // Guardo el tamaño anterior para saber si esta cola estaba llena
    size_t oldSize = q.size();

    q.pop_front();
    resp1to0.lastServedClass = classId;

    // Si esta cola estaba llena y ahora ya no, aviso al productor
    // de la response del lado 1 para que reintente.
    if (oldSize == respBufferSize) {
        std::cout << "[Interposer] RELEASE RESP 1->0"
                  << " class=" << getClassName(msgClass)
                  << " -> sendRetryResp to interface1\n";
        toInterface1Port->sendRetryResp();
    }

    if (q.empty()) {
        resp1to0.queues.erase(msgClass);
    }

    Tick when = nextReadyTick(resp1to0);
    if (when != MaxTick) {
        scheduleBufferEvent(resp1to0, std::max(curTick(), when));
    }
    // ---------------- FIN NUEVO ----------------
}

//helper 

void
C2CInterposer::scheduleBufferEvent(DirBuffer &buf, Tick when)
{
    // ---------------- NUEVO ----------------
    if (when == MaxTick) {
        return;
    }

    if (!buf.processEvent.scheduled()) {
        schedule(buf.processEvent, when);
    } else if (buf.processEvent.when() > when) {
        reschedule(buf.processEvent, when);
    }
    // ---------------- FIN NUEVO ----------------
}

} // namespace gem5