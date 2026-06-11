#include "mem/c2c_interposer.hh"

#include "base/logging.hh"
#include "base/trace.hh"
#include "base/types.hh"
#include "debug/C2CInterposer.hh"
#include "mem/ruby/protocol/C2cMsg.hh"
#include "mem/ruby/protocol/C2cRequestType.hh"

#include <iomanip>
#include <iostream>
#include <sstream>

#include <set>
#include <deque>
#include <tuple>

namespace gem5 {

/*Variables globales de bloqueo (de colas) y paquetes pendientes, de forma que se gestione el backpressure y el retry*/

//chips que estan bloqueados porque intentaron enviar una Request hacia un destino (dst) pero estaba lleno (interposer lleno)
static std::vector<std::set<int>> blockedReqSrcByDst;
//chips que estan bloqueados porque intentaron enviar una Response hacia un destino (dst) pero estaba lleno (interposer lleno)
static std::vector<std::set<int>> blockedRespSrcByDst;

//paquete de Request pendiente porque el destino no lo aceptó 
static std::vector<PacketPtr> pendingReqPktByDst;

static std::vector<int> pendingReqSrcByDst;

//paquete de Response pendiente porque el destino no lo aceptó 
static std::vector<PacketPtr> pendingRespPktByDst;

static std::vector<int> pendingRespSrcByDst;

//Flags sencillas para saber si el chip está bloqueado por 
//Request
std::vector<bool> blockedReqFrom;
//Response
std::vector<bool> blockedRespFrom;


/*Clasifica el tipo de Snoop. Un snoop puede ser una request (ejemplo SnpShared, SnpUnique, SnpSharedFwd) pero otras 
son la respuesta generada por un chip/nodo snoopeado ej SnpResp...

Hay que distinguir, porque usualmente estas respuestas vuelven al request owner, pero en el caso de SnpResp_SC_Fwded_SC no?*/
static bool
isSnoopResponseToHome(ruby::C2cRequestType type)
{
    using namespace ruby;

    switch (type) {
      case C2cRequestType_SnpResp_I:
      case C2cRequestType_SnpResp_I_Fwded_UD_PD:
      case C2cRequestType_SnpResp_I_Fwded_UC:
      case C2cRequestType_SnpResp_SC_Fwded_SC: 
      case C2cRequestType_SnpResp_SC_Fwded_SD_PD:
      case C2cRequestType_SnpResp_SD_Fwded_I:
      case C2cRequestType_SnpResp_SC_Fwded_I:
      case C2cRequestType_SnpResp_UD_Fwded_I:
      case C2cRequestType_SnpResp_UC_Fwded_I:
        return true;

      default:
        return false;
    }
}

static bool
isSnoopResponseDataToHome(ruby::C2cRequestType type)
{
    using namespace ruby;

    switch (type) {
      case C2cRequestType_SnpRespData_I_PD:
      case C2cRequestType_SnpRespData_I:
      case C2cRequestType_SnpRespData_SC_PD:
      case C2cRequestType_SnpRespData_SC:
      case C2cRequestType_SnpRespData_SD:
      case C2cRequestType_SnpRespData_UC:
      case C2cRequestType_SnpRespData_UD:
      case C2cRequestType_SnpRespData_SC_Fwded_SD_PD:
      case C2cRequestType_SnpRespData_SC_Fwded_SC:
      case C2cRequestType_SnpRespData_SC_PD_Fwded_SC:
      case C2cRequestType_SnpRespData_I_Fwded_SD_PD:
      case C2cRequestType_SnpRespData_I_PD_Fwded_SC:
      case C2cRequestType_SnpRespData_I_Fwded_SC:
        return true;

      default:
        return false;
    }
}


/*Inicializa el tamaño de los vectores de bloqueo y paquetes pendientes al numero de interfaces y 
en el caso de si hay paquetes pendientes, tambien pone el puntero a un paquete null*/
static void
ensureBlockedVectors(unsigned numInterfaces)
{
    if (blockedReqSrcByDst.size() != numInterfaces) {
        blockedReqSrcByDst.clear();
        blockedReqSrcByDst.resize(numInterfaces);
    }

    if (blockedRespSrcByDst.size() != numInterfaces) {
        blockedRespSrcByDst.clear();
        blockedRespSrcByDst.resize(numInterfaces);
    }

    if (pendingReqPktByDst.size() != numInterfaces) {
        pendingReqPktByDst.clear();
        pendingReqPktByDst.resize(numInterfaces, nullptr);

        pendingReqSrcByDst.clear();
        pendingReqSrcByDst.resize(numInterfaces, -1);
    }

    if (pendingRespPktByDst.size() != numInterfaces) {
        pendingRespPktByDst.clear();
        pendingRespPktByDst.resize(numInterfaces, nullptr);

        pendingRespSrcByDst.clear();
        pendingRespSrcByDst.resize(numInterfaces, -1);
    }
}

/*Función auxiliar para saber si un paquete existe y si tiene un mensaje de ruby asociado. 
Asi evito acceder a campos de un mensaje de ruby si no los tiene el paquete*/
static bool
hasC2cMsg(PacketPtr pkt)
{
    return pkt && pkt->c2c_msg;
}

/*Hace un casting para devolver el tipo del paquete de gem5 como un numero entero y luego 
poderlo clasificar en otra funcion*/
static int
getC2cTypeId(PacketPtr pkt)
{
    assert(pkt && pkt->c2c_msg);
    return static_cast<int>(pkt->c2c_msg->m_Type);
}

/*Devuelve el tipo del paquete de gem5 pero en texto*/
static std::string
getC2cTypeName(PacketPtr pkt)
{
    if (!pkt || !pkt->c2c_msg) {
        return "NO_C2C_MSG";
    }

    return ruby::C2cRequestType_to_string(pkt->c2c_msg->m_Type);
}

/*Funcion de depuracion para devolver TODA la informacion basica del paquete*/
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

/*Esta funcion siver para imprimir el "MachineID" de Ruby a un texto un legible 
Ej: Cache-14
Interface-2
INVALID_MACHINE_TYPE(21)-0

He agregado mas comprobaciones, porque puede que algunos campos del C2cMsg no este inicializados 
o no sean validos para todos los tipos de mensaje*/

static std::string
machineIdToString(const ruby::MachineID &mach)
{
    std::ostringstream oss;

    const int typeInt = static_cast<int>(mach.type);

    if (typeInt < 0 || typeInt >= static_cast<int>(ruby::MachineType_NUM)) {
        oss << "INVALID_MACHINE_TYPE("
            << typeInt
            << ")-"
            << mach.num;
        return oss.str();
    }

    oss << ruby::MachineType_to_string(mach.type)
        << "-"
        << mach.num;

    return oss.str();
}

/*Es otra funcion de depuracion que imprime aun mas campos del paquete*/
static void
printC2cMsgDebug(PacketPtr pkt, const char *tag, int srcSide, int dstSide)
{
    std::cout << "[C2C DBG " << tag << "]"
              << " tick=" << curTick()
              << " src=" << srcSide
              << " dst=" << dstSide;

    if (!pkt) {
        std::cout << " pkt=null\n";
        return;
    }

    std::cout << " pkt=" << pkt
              << " req=" << pkt->req
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " cmd=" << pkt->cmdString()
              << " isReq=" << pkt->isRequest()
              << " isResp=" << pkt->isResponse()
              << " needsResp=" << pkt->needsResponse()
              << " headerDelay=" << pkt->headerDelay
              << " payloadDelay=" << pkt->payloadDelay;

    if (!pkt->c2c_msg) {
        std::cout << " type=NO_C2C_MSG\n";
        return;
    }

    const auto *msg = pkt->c2c_msg;

    std::cout << " type=" << getC2cTypeName(pkt)
              << " sender=" << machineIdToString(msg->m_Sender)
              << " requestor=" << machineIdToString(msg->m_Requestor)
              << " originalRequestor=" << machineIdToString(msg->m_OriginalRequestor)
              << " responder=" << machineIdToString(msg->m_Responder)
              << " originalResponder=" << machineIdToString(msg->m_OriginalResponder)
              << " localRequestor=" << machineIdToString(msg->m_LocalRequestor)
              << "\n";
}

/*------------------------------------------------------------*/
/* FromInterfacePort                                          */
/*------------------------------------------------------------*/

/*Representa el puerto por donde se reciben Requests/Snoops en el interposer*/
C2CInterposer::FromInterfacePort::FromInterfacePort(
    const std::string &name,
    C2CInterposer *owner,
    int side //el indice logico del lado del chip
) : ResponsePort(name, owner), owner(owner), side(side)
{
}

AddrRangeList
C2CInterposer::FromInterfacePort::getAddrRanges() const
{
    // El MUX acepta todos los rangos C2C desde cualquier chip.
    // Devuelvo la unión de los rangos configurados.
    AddrRangeList ranges;
    //Al hacer esto permito que el interporse acepte trafico de todos los rangos remotos
    for (const auto &r : owner->c2cMemRanges) {
        ranges.push_back(r);
    }
    return ranges;
}

/*No implementado pero al heredad del puerto hay que incluirla*/
void
C2CInterposer::FromInterfacePort::recvFunctional(PacketPtr pkt)
{
    panic("C2CInterposer::FromInterfacePort::recvFunctional not implemented");
}

/*Es una de las entradas de las Request/Snoop del interposer desde una interfaz C2C. 
Osea, si un chip quiere enviar una request/snoop hacia otro lado, debe entrar aqui*/
bool
C2CInterposer::FromInterfacePort::recvTimingReq(PacketPtr pkt)
{
    std::cout << "[PORT ENTER] FromInterfacePort::recvTimingReq"
              << " side=" << side
              << " " << pktToString(pkt)
              << " type=" << getC2cTypeName(pkt)
              << "\n";
    //owner es el puntero al interposer y side el índice lógico de la interfaz C2C
    //luego se llama a la funcon que decide el routing y encola la request
    return owner->recvReqFromInterface(pkt, side);
}

/*Funcion auxiliar que sirve para que un chip al recibir una response avise que ya no puede aceptar otra*/
void
C2CInterposer::FromInterfacePort::recvRespRetry()
{
    owner->recvRespRetryFromInterface(side);
}

/*Hay que meter las atomic por herencia pero todas solo se trabaja con Timing*/
Tick
C2CInterposer::FromInterfacePort::recvAtomic(PacketPtr pkt)
{
    return owner->recvAtomicFromInterface(pkt, side);
}

/*------------------------------------------------------------*/
/* ToInterfacePort                                            */
/*------------------------------------------------------------*/

/*Representa el puerto del interposer por donde salen las Request/Snoops y tambien por donde vuelven 
las responses de estas mismas (recuerda, las request y responses van y vuelven de la C2C interface)*/
C2CInterposer::ToInterfacePort::ToInterfacePort(
    const std::string &name,
    C2CInterposer *owner,
    int side
) : RequestPort(name, owner), owner(owner), side(side)
{
}


/*Es la entrada principal del interposer de las Responses. Cuando el chip 
de destino responde a una request o snoop, la respuesta viene por aquí*/
bool
C2CInterposer::ToInterfacePort::recvTimingResp(PacketPtr pkt)
{
    std::cout << "[PORT ENTER] ToInterfacePort::recvTimingResp"
              << " side=" << side
              << " " << pktToString(pkt)
              << " type=" << getC2cTypeName(pkt)
              << "\n";

    return owner->recvRespFromInterface(pkt, side);
}

/*Funcion auxiliar para avisar que el destino de una request que estaba bloqueado ahora puede aceptar mas*/
void
C2CInterposer::ToInterfacePort::recvReqRetry()
{
    owner->recvReqRetryToInterface(side);
}

/*------------------------------------------------------------*/
/* Constructor / destructor / getPort  del interposer                       */
/*------------------------------------------------------------*/

C2CInterposer::C2CInterposer(const C2CInterposerParams &params)
    : ClockedObject(params),
      numInterfaces(params.num_interfaces),
      reqLatency(params.req_latency),
      respLatency(params.resp_latency),
      reqBufferSize(params.req_buffer_size),
      respBufferSize(params.resp_buffer_size),
      c2cMemRanges(params.c2c_mem_ranges.begin(), params.c2c_mem_ranges.end()),
      cacheChipIDList(params.cache_chip_id_list.begin(), params.cache_chip_id_list.end()),
      interfaceChipIDList(params.interface_chip_id_list.begin(), params.interface_chip_id_list.end())
{
    std::cout << "[Interposer] constructor called, numInterfaces="
              << numInterfaces << "\n";

    if (numInterfaces == 0) {
        panic("C2CInterposer requires num_interfaces > 0");
    }

    ensureBlockedVectors(numInterfaces);

    toInterfacePorts.resize(numInterfaces, nullptr);
    fromInterfacePorts.resize(numInterfaces, nullptr);
    reqTo.resize(numInterfaces); //cola de requests/snoops cuyo destino es el chip i
    respTo.resize(numInterfaces); //cola de responses cuyo destino es el chip i 
    blockedReqFrom.resize(numInterfaces, false);
    blockedRespFrom.resize(numInterfaces, false);

    for (unsigned i = 0; i < numInterfaces; ++i) {
        fromInterfacePorts[i] = new FromInterfacePort(
            csprintf("%s.from_interfaces[%u]", name(), i), this, i);

        toInterfacePorts[i] = new ToInterfacePort(
            csprintf("%s.to_interfaces[%u]", name(), i), this, i);

        reqTo[i] = std::make_unique<DirBuffer>(EventFunctionWrapper(
            [this, i] { processReqTo(i); },
            csprintf("%s.processReqTo%u", name(), i)));

        respTo[i] = std::make_unique<DirBuffer>(EventFunctionWrapper(
            [this, i] { processRespTo(i); },
            csprintf("%s.processRespTo%u", name(), i)));
    }
}

//Destructor. 
C2CInterposer::~C2CInterposer()
{
    dumpC2cTypeStats();

    for (auto *p : fromInterfacePorts) {
        delete p;
    }
    for (auto *p : toInterfacePorts) {
        delete p;
    }
}

/*Permite conectar con los puertos definidos en python*/
Port &
C2CInterposer::getPort(const std::string &if_name, PortID idx)
{
    // 
    // Estos nombres deben coincidir exactamente con los VectorPort definidos
    // en c2c_interposer.py: from_interfaces y to_interfaces.
    if (if_name == "from_interfaces") {
        if (idx == InvalidPortID || idx >= fromInterfacePorts.size()) {
            panic("Invalid from_interfaces index %d", idx);
        }
        return *fromInterfacePorts[idx];
    }

    if (if_name == "to_interfaces") {
        if (idx == InvalidPortID || idx >= toInterfacePorts.size()) {
            panic("Invalid to_interfaces index %d", idx);
        }
        return *toInterfacePorts[idx];
    }

    return ClockedObject::getPort(if_name, idx);
}

/*------------------------------------------------------------*/
/* Clasificación Request/Snoop/Response/Data                  */
/*------------------------------------------------------------*/

//Devuelve en texto el tipo de mensaje del paquete
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

//Clasificacion del tipo de mensaje del paquete en 4 categorias. Igual al codigo de ruby 
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
    }

    if (type == C2cRequestType_SnpCleanInvalid ||
        type == C2cRequestType_SnpUnique ||
        type == C2cRequestType_SnpSharedFwd ||
        type == C2cRequestType_SnpUniqueFwd ||
        type == C2cRequestType_SnpOnceFwd) {
        return C2cMsgClass::Snoop;
    }

    if (type == C2cRequestType_CompData_UC ||
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
    }

    if (type == C2cRequestType_CompAck ||
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
    }

    panic("Invalid C2c request type in C2CInterposer classification: %s",
          ruby::C2cRequestType_to_string(type).c_str());
}

/*Comprueba que el paquete tenga una mensaje de ruby asociado*/
C2CInterposer::C2cMsgClass
C2CInterposer::getPacketClass(PacketPtr pkt) const
{
    if (!hasC2cMsg(pkt)) {
        panic("Packet without c2c_msg in C2CInterposer");
    }
    return classifyC2cType(pkt->c2c_msg->m_Type);
}

/*------------------------------------------------------------*/
/* Routing                                                     */
/*------------------------------------------------------------*/

//Comrpueba que el destino sea una interfaz (que en este caso se corresponde con un chip) valido
bool 
C2CInterposer::validSide(int side) const
{
    return side >= 0 && side < static_cast<int>(numInterfaces);
}

/*Routinga para las responses: Se hace en base al machineId, para ello convierte "MachieID" en una interfaz/chip
de destino valido*/
int
C2CInterposer::routeByMachineID(const ruby::MachineID &mach, int fallback) const
{
    /*
     
     Algunos campos MachineID dentro de C2cMsg pueden no ser válidos para
      todos los tipos de mensaje.
     
     Por ejemplo, en algunas trazas he visto visto que al imprimir m_Requestor
     gem5 abortaba porque mach.type estaba fuera del rango válido del enum
      MachineType.
     
     Por eso compruebo primero el valor numérico del tipo antes de usarlo.
     */
    const int typeInt = static_cast<int>(mach.type);

    if (typeInt < 0 || typeInt >= static_cast<int>(ruby::MachineType_NUM)) {
        return fallback;
    }

    // MachineType_NUM se usa como valor nulo/no válido en muchos mensajes.
    // Si aparece, no puedo enrutar usando este MachineID.
    if (mach.type == ruby::MachineType_NUM) {
        return fallback;
    }

    /* Si el MachineID es de tipo Cache, mach.num es el número/version
     del controlador de cache Ruby.
    
     cacheChipIDList[mach.num]  dice en que chip esta esa cache.
     Ej: Cache-14 -> chip0 donde vive Cache-14 osea Interface-2 -> chip0 asociado a Interface-2
    
     mach.num es unsigned, por eso no hago mach.num >= 0.*/
    if (mach.type == ruby::MachineType_Cache) {
        if (mach.num < cacheChipIDList.size()) {
            return cacheChipIDList[mach.num];
        }

        return fallback;
    }

    // Si el MachineID es de tipo Interface, mach.num es el número/version
    // de la interfaz C2C.
    //
    // interfaceChipIDList[mach.num] nos dice qué chip representa esa interfaz.
    if (mach.type == ruby::MachineType_Interface) {
        if (mach.num < interfaceChipIDList.size()) {
            return interfaceChipIDList[mach.num];
        }

        return fallback;
    }

    return fallback;
}


/*Politica de enrutamiento para las request/snoop: en base a la direccion del paquete. 
Para ello se busca que rango de c2cMemRanges contiene esa direccion y en base a eso enviarla ahi.
Ej: addr 0xbc829000 pertenece al rango del chip 0 ENTONCES routeByAddress() devuelve 0*/
int
C2CInterposer::routeByAddress(PacketPtr pkt, int incomingSide) const
{
    const Addr addr = pkt->getAddr();

    for (int chip = 0; chip < static_cast<int>(c2cMemRanges.size()); ++chip) {
        if (c2cMemRanges[chip].contains(addr)) {
            return chip;
        }
    }

    return -1;
}

/*Este se utiliza como fallback para snoops donde la direccion no basta. 
Entonces lo que se hace es que se intenta leer explicitamente el destino desde un campo del paquete 
msg->m_C2c_destination
Y para cada interfaz/chip lo que hace es 
msg->m_C2c_destination.extractNetDest(chip)
osea, si se encuentra un netdest no vacio para ese chip, pues se devuelve ese chip para enrutar*/
int
C2CInterposer::routeByC2cDestination(PacketPtr pkt, int srcSide) const
{
    if (!hasC2cMsg(pkt)) {
        return -1;
    }

    const auto *msg = pkt->c2c_msg;

    /*
     * m_C2c_destination es un MegaNetDest.
     *
     * Importante:
     * MegaNetDest indexa chips reales, no puertos del interposer.
     *
     * En la versión de 3 interfaces:
     *
     *   chip 0 -> side 0
     *   chip 1 -> side 1
     *   chip 2 -> side 2
     *
     * Por tanto, aquí podemos devolver directamente el chip destino como
     * side destino.
     *
     * No usamos numInterfaces como "número de chips" por concepto.
     * Usamos c2cMemRanges.size(), porque esa lista representa los chips reales.
     */
    const int numChips = static_cast<int>(c2cMemRanges.size());

    int foundChip = -1;
    int foundCount = 0;

    for (int chip = 0; chip < numChips; ++chip) {
        ruby::NetDest nd = msg->m_C2c_destination.extractNetDest(chip);

        if (!nd.isEmpty()) {
            foundChip = chip;
            foundCount++;

            std::cout << "[C2C DEST MATCH]"
                      << " srcSide=" << srcSide
                      << " chip=" << chip
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << " type=" << getC2cTypeName(pkt)
                      << " nd=" << nd
                      << "\n";
        }
    }

    if (foundCount == 1) {
        return foundChip;
    }

    if (foundCount > 1) {
        std::cout << "[C2C DEST MULTI]"
                  << " srcSide=" << srcSide
                  << " foundCount=" << foundCount
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << " sender=" << machineIdToString(msg->m_Sender)
                  << " requestor=" << machineIdToString(msg->m_Requestor)
                  << " originalRequestor=" << machineIdToString(msg->m_OriginalRequestor)
                  << " localRequestor=" << machineIdToString(msg->m_LocalRequestor)
                  << " responder=" << machineIdToString(msg->m_Responder)
                  << " originalResponder=" << machineIdToString(msg->m_OriginalResponder)
                  << "\n";

        /*
         * Si hay más de un destino C2C, no elegimos arbitrariamente.
         * Esto indicaría que el protocolo quiere multicast/broadcast C2C,
         * y el interposer actual, que devuelve un único dstSide, no puede
         * representarlo correctamente.
         */
        return -1;
    }

    return -1;
}

int
C2CInterposer::routeByDestinationField(PacketPtr pkt, int fallback) const
{
    /*
     *
     * Antes aquí usaba:
     *
     *     msg->getDestination()
     *
     * para leer el NetDest del mensaje Ruby. Eso NO es seguro en este path
     * C2C, porque no todos los C2cMsg tienen un campo Destination válido.
     *
     * Si llamo a getDestination() sobre un mensaje que no soporta ese
     * campo, gem5 aborta con:
     *
     *     panic: getDestination() called on wrong message!
     *
     * Por eso esta función queda como fallback neutro. La mantengo para no
     * romper la estructura del código, pero ya no consulta getDestination().
     *
     * El routing real queda así:
     *
     *   - Requests/Snoops:
     *       se enrutan por dirección de memoria usando routeByAddress().
     *
     *   - Responses/Data:
     *       se enrutan por MachineID usando routeByMachineID() sobre campos
     *       como m_OriginalRequestor, m_Requestor y m_LocalRequestor.
     */
    return fallback;
}


/*Verdadera funcion de routing para las request que llama a las otras funciones auxiliares dependiendo
del tipo de Request que sea*/
int
C2CInterposer::routeRequest(PacketPtr pkt, int srcSide) const
{
    if (!hasC2cMsg(pkt)) {
        panic("C2CInterposer cannot route request without c2c_msg");
    }

    const auto *msg = pkt->c2c_msg;
    const C2cMsgClass msgClass = getPacketClass(pkt);

    int dst = -1;

    /*
     * Regla principal:
     *
     * Si el protocolo SLICC ya puso un destino C2C explícito,
     * el interposer debe respetarlo.
     *
     * Esto es especialmente importante para SnpSharedFwd, SnpUniqueFwd,
     * SnpOnceFwd, etc.
     *
     * Un snoop forwarded puede tener una dirección perteneciente al chip 0,
     * pero su destino real puede ser un sharer remoto. Por eso para snoops
     * NO debemos decidir por dirección como primera opción.
     */
    dst = routeByC2cDestination(pkt, srcSide);
    if (validSide(dst) && dst != srcSide) {
        std::cout << "[C2C ROUTE DECISION]"
                  << " kind=REQ_OR_SNOOP"
                  << " reason=c2c_destination"
                  << " src=" << srcSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << "\n";
        return dst;
    }

    /*
     * Si es un Snoop y no tiene c2c_destination utilizable, entonces intentamos
     * MachineID como fallback.
     *
     * Pero no usamos dirección para snoops como criterio principal, porque eso
     * puede devolver el chip propietario de la línea, no el chip que debe
     * recibir el snoop.
     */
    if (msgClass == C2cMsgClass::Snoop) {
        dst = routeByMachineID(msg->m_OriginalRequestor, -1);
        if (validSide(dst) && dst != srcSide) {
            std::cout << "[C2C ROUTE DECISION]"
                      << " kind=SNOOP"
                      << " reason=originalRequestor"
                      << " src=" << srcSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << " type=" << getC2cTypeName(pkt)
                      << "\n";
            return dst;
        }

        dst = routeByMachineID(msg->m_Requestor, -1);
        if (validSide(dst) && dst != srcSide) {
            std::cout << "[C2C ROUTE DECISION]"
                      << " kind=SNOOP"
                      << " reason=requestor"
                      << " src=" << srcSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << " type=" << getC2cTypeName(pkt)
                      << "\n";
            return dst;
        }

        dst = routeByMachineID(msg->m_LocalRequestor, -1);
        if (validSide(dst) && dst != srcSide) {
            std::cout << "[C2C ROUTE DECISION]"
                      << " kind=SNOOP"
                      << " reason=localRequestor"
                      << " src=" << srcSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << " type=" << getC2cTypeName(pkt)
                      << "\n";
            return dst;
        }

        std::cout << "[C2C ROUTE ERROR] cannot route SNOOP"
                  << " src=" << srcSide
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << " sender=" << machineIdToString(msg->m_Sender)
                  << " requestor=" << machineIdToString(msg->m_Requestor)
                  << " originalRequestor=" << machineIdToString(msg->m_OriginalRequestor)
                  << " localRequestor=" << machineIdToString(msg->m_LocalRequestor)
                  << " responder=" << machineIdToString(msg->m_Responder)
                  << " originalResponder=" << machineIdToString(msg->m_OriginalResponder)
                  << "\n";

        panic("C2CInterposer cannot route snoop from side %d: %s",
              srcSide, pktToString(pkt).c_str());

        return srcSide;
    }

    /*
     * Requests normales:
     *
     * Para ReadShared, ReadUnique, CleanUnique, WriteBackFull, etc.,
     * si no había c2c_destination explícito, usamos la dirección.
     *
     * Esto conserva la política:
     *
     *   Requests normales -> dirección
     *   Responses/Data    -> MachineID
     */
    dst = routeByAddress(pkt, srcSide);
    if (validSide(dst) && dst != srcSide) {
        std::cout << "[C2C ROUTE DECISION]"
                  << " kind=REQUEST"
                  << " reason=address"
                  << " src=" << srcSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << "\n";
        return dst;
    }

    /*
     * Último fallback por MachineID.
     */
    dst = routeByMachineID(msg->m_OriginalRequestor, -1);
    if (validSide(dst) && dst != srcSide) {
        std::cout << "[C2C ROUTE DECISION]"
                  << " kind=REQUEST"
                  << " reason=originalRequestor_fallback"
                  << " src=" << srcSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << "\n";
        return dst;
    }

    dst = routeByMachineID(msg->m_Requestor, -1);
    if (validSide(dst) && dst != srcSide) {
        std::cout << "[C2C ROUTE DECISION]"
                  << " kind=REQUEST"
                  << " reason=requestor_fallback"
                  << " src=" << srcSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << "\n";
        return dst;
    }

    std::cout << "[C2C ROUTE ERROR] cannot route REQUEST"
              << " src=" << srcSide
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " type=" << getC2cTypeName(pkt)
              << " sender=" << machineIdToString(msg->m_Sender)
              << " requestor=" << machineIdToString(msg->m_Requestor)
              << " originalRequestor=" << machineIdToString(msg->m_OriginalRequestor)
              << " localRequestor=" << machineIdToString(msg->m_LocalRequestor)
              << " responder=" << machineIdToString(msg->m_Responder)
              << " originalResponder=" << machineIdToString(msg->m_OriginalResponder)
              << "\n";

    panic("C2CInterposer cannot route request from side %d: %s",
          srcSide, pktToString(pkt).c_str());

    return srcSide;
}

/*Verdadera funcion para el routing de respuestas, esta se encarga de llamar a las demas funciones auxiliares*/
int
C2CInterposer::routeResponse(PacketPtr pkt, int responderSide) const
{
    if (!hasC2cMsg(pkt)) {
        panic("C2CInterposer cannot route response without c2c_msg");
    }

    const auto *msg = pkt->c2c_msg;
    const auto type = msg->m_Type;

    int dst = -1;

    if (type == ruby::C2cRequestType_CompData_SC) {
        const int byOriginalRequestor =
            routeByMachineID(msg->m_OriginalRequestor, -1);

        const int byRequestor =
            routeByMachineID(msg->m_Requestor, -1);

        const int byLocalRequestor =
            routeByMachineID(msg->m_LocalRequestor, -1);

        const int byResponder =
            routeByMachineID(msg->m_Responder, -1);

        const int byOriginalResponder =
            routeByMachineID(msg->m_OriginalResponder, -1);

        const int byC2cDest =
            routeByC2cDestination(pkt, responderSide);

        const int byAddr =
            routeByAddress(pkt, responderSide);

        std::cout << "[C2C RESP CANDIDATES COMPDATA_SC]"
                << " tick=" << curTick()
                << " src=" << responderSide
                << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                << " pkt=" << pkt
                << " req=" << pkt->req
                << " sender=" << machineIdToString(msg->m_Sender)
                << " requestor=" << machineIdToString(msg->m_Requestor)
                << " originalRequestor="
                << machineIdToString(msg->m_OriginalRequestor)
                << " localRequestor="
                << machineIdToString(msg->m_LocalRequestor)
                << " responder=" << machineIdToString(msg->m_Responder)
                << " originalResponder="
                << machineIdToString(msg->m_OriginalResponder)
                << " byOriginalRequestor=" << byOriginalRequestor
                << " byRequestor=" << byRequestor
                << " byLocalRequestor=" << byLocalRequestor
                << " byResponder=" << byResponder
                << " byOriginalResponder=" << byOriginalResponder
                << " byC2cDest=" << byC2cDest
                << " byAddr=" << byAddr
                << "\n";
    }

    /*
     * CASO 1:
     * Respuestas de snoop:
     *
     *   - SnpResp_*
     *   - SnpRespData_*
     *
     * Comparación con SLICC:
     *
     *   Send_FwdSnpResp:
     *      out_msg.Destination.add(tbe.requestor);
     *      out_msg.localRequestor := tbe.localRequestor;
     *      out_msg.originalRequestor := tbe.originalRequestor;
     *      out_msg.originalResponder := machineID;
     *
     *   Send_SnpRespDataFwded:
     *      tbe.snd_destination := tbe.requestor;
     *      setupPendingSend(tbe);
     *
     *   Send_Data:
     *      out_msg.Destination.add(tbe.snd_destination);
     *      out_msg.localRequestor := tbe.localRequestor;
     *      out_msg.originalRequestor := tbe.originalRequestor;
     *      out_msg.originalResponder := machineID;
     *
     * Por tanto, para SnpResp* no debo empezar por:
     *
     *   - OriginalResponder
     *   - Responder
     *   - Dirección
     *
     * porque eso no imita Destination.add(tbe.requestor).
     *
     * En los logs, m_Requestor muchas veces viene INVALID para SnpResp_*,
     * así que el mejor proxy disponible del contexto SLICC suele ser
     * m_LocalRequestor.
     */
    if (isSnoopResponseToHome(type) || isSnoopResponseDataToHome(type)) {
        /*
         * 1) Primer candidato: localRequestor.
         *
         * En los logs del fallo, para SnpResp_SC_Fwded_SC aparecía algo tipo:
         *
         *   localRequestor=Cache-2
         *   requestor=INVALID_MACHINE_TYPE(21)-0
         *
         * Por eso localRequestor debe probarse antes que requestor.
         */
        dst = routeByMachineID(msg->m_LocalRequestor, -1);
        if (validSide(dst) && dst != responderSide) {
            std::cout << "[C2C RESP CHOSEN]"
                      << " type=" << getC2cTypeName(pkt)
                      << " rule=SNPRESP_LOCAL_REQUESTOR"
                      << " src=" << responderSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << "\n";
            return dst;
        }

        /*
         * 2) Segundo candidato: requestor.
         *
         * Este sería el más parecido a:
         *
         *   Destination.add(tbe.requestor)
         *
         * si el campo viene válido en C2cMsg.
         */
        dst = routeByMachineID(msg->m_Requestor, -1);
        if (validSide(dst) && dst != responderSide) {
            std::cout << "[C2C RESP CHOSEN]"
                      << " type=" << getC2cTypeName(pkt)
                      << " rule=SNPRESP_REQUESTOR"
                      << " src=" << responderSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << "\n";
            return dst;
        }

        /*
         * 3) Tercer candidato: destino C2C explícito.
         *
         * Si SLICC dejó información explícita de c2c_destination, respetarla
         * antes de caer a dirección.
         */
        dst = routeByC2cDestination(pkt, responderSide);
        if (validSide(dst) && dst != responderSide) {
            std::cout << "[C2C RESP CHOSEN]"
                      << " type=" << getC2cTypeName(pkt)
                      << " rule=SNPRESP_C2C_DEST"
                      << " src=" << responderSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << "\n";
            return dst;
        }

        /*
         * 4) Fallback controlado: originalRequestor.
         *
         * OJO: Para SnpResp*_Fwded_* puede representar al requestor final de
         * datos, no necesariamente al home/requestor del snoop response.
         * Por eso no va primero.
         */
        dst = routeByMachineID(msg->m_OriginalRequestor, -1);
        if (validSide(dst) && dst != responderSide) {
            std::cout << "[C2C RESP CHOSEN]"
                      << " type=" << getC2cTypeName(pkt)
                      << " rule=SNPRESP_ORIGINAL_REQUESTOR_FALLBACK"
                      << " src=" << responderSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << "\n";
            return dst;
        }

        /*
         * 5) Último recurso: dirección.
         *
         * Si para la dirección que peta, por ejemplo 0xbfff7000, sigues viendo:
         *
         *   rule=SNPRESP_ADDR_LAST_RESORT
         *
         * entonces seguimos perdiendo el contexto que SLICC tenía en
         * Destination/tbe.requestor.
         */
        dst = routeByAddress(pkt, responderSide);
        if (validSide(dst) && dst != responderSide) {
            std::cout << "[C2C RESP WARNING]"
                      << " type=" << getC2cTypeName(pkt)
                      << " rule=SNPRESP_ADDR_LAST_RESORT"
                      << " src=" << responderSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << " sender=" << machineIdToString(msg->m_Sender)
                      << " requestor=" << machineIdToString(msg->m_Requestor)
                      << " originalRequestor="
                      << machineIdToString(msg->m_OriginalRequestor)
                      << " localRequestor="
                      << machineIdToString(msg->m_LocalRequestor)
                      << " responder=" << machineIdToString(msg->m_Responder)
                      << " originalResponder="
                      << machineIdToString(msg->m_OriginalResponder)
                      << "\n";
            return dst;
        }

        std::cout << "[C2C ROUTE ERROR] cannot route SNPRESP"
                  << " src=" << responderSide
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << " sender=" << machineIdToString(msg->m_Sender)
                  << " requestor=" << machineIdToString(msg->m_Requestor)
                  << " originalRequestor="
                  << machineIdToString(msg->m_OriginalRequestor)
                  << " localRequestor="
                  << machineIdToString(msg->m_LocalRequestor)
                  << " responder=" << machineIdToString(msg->m_Responder)
                  << " originalResponder="
                  << machineIdToString(msg->m_OriginalResponder)
                  << "\n";

        panic("C2CInterposer cannot route SnpResp from side %d: %s",
              responderSide, pktToString(pkt).c_str());

        return responderSide;
    }

    /*
     * CASO 2:
     * CompAck / ReqAck.
     *
     * Aquí lo dejamos como lo tenías conceptualmente: por dirección primero.
     *
     * Esto sí encaja mejor con SLICC, porque Send_CompAck hace:
     *
     *   out_msg.Destination.add(mapAddressToDownstreamMachine(tbe.addr));
     */
    if (type == ruby::C2cRequestType_CompAck ||
        type == ruby::C2cRequestType_ReqAck) {

        dst = routeByAddress(pkt, responderSide);
        if (validSide(dst) && dst != responderSide) {
            std::cout << "[C2C RESP CHOSEN]"
                      << " type=" << getC2cTypeName(pkt)
                      << " rule=ACK_ADDR"
                      << " src=" << responderSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << "\n";
            return dst;
        }

        dst = routeByC2cDestination(pkt, responderSide);
        if (validSide(dst) && dst != responderSide) {
            std::cout << "[C2C RESP CHOSEN]"
                      << " type=" << getC2cTypeName(pkt)
                      << " rule=ACK_C2CDEST"
                      << " src=" << responderSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << "\n";
            return dst;
        }

        dst = routeByMachineID(msg->m_OriginalResponder, -1);
        if (validSide(dst) && dst != responderSide) {
            std::cout << "[C2C RESP CHOSEN]"
                      << " type=" << getC2cTypeName(pkt)
                      << " rule=ACK_ORIGINAL_RESPONDER"
                      << " src=" << responderSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << "\n";
            return dst;
        }

        dst = routeByMachineID(msg->m_Responder, -1);
        if (validSide(dst) && dst != responderSide) {
            std::cout << "[C2C RESP CHOSEN]"
                      << " type=" << getC2cTypeName(pkt)
                      << " rule=ACK_RESPONDER"
                      << " src=" << responderSide
                      << " dst=" << dst
                      << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                      << "\n";
            return dst;
        }

        std::cout << "[C2C ROUTE ERROR] cannot route ACK"
                  << " src=" << responderSide
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << " sender=" << machineIdToString(msg->m_Sender)
                  << " requestor=" << machineIdToString(msg->m_Requestor)
                  << " originalRequestor="
                  << machineIdToString(msg->m_OriginalRequestor)
                  << " localRequestor="
                  << machineIdToString(msg->m_LocalRequestor)
                  << " responder=" << machineIdToString(msg->m_Responder)
                  << " originalResponder="
                  << machineIdToString(msg->m_OriginalResponder)
                  << "\n";

        panic("C2CInterposer cannot route ACK from side %d: %s",
              responderSide, pktToString(pkt).c_str());

        return responderSide;
    }

    /*
     * CASO 3:
     * Responses/Data normales.
     *
     * Ejemplos:
     *
     *   CompData_UC
     *   CompData_SC
     *   CompData_I
     *
     * Estos sí deben volver normalmente al originalRequestor.
     */
    dst = routeByMachineID(msg->m_OriginalRequestor, -1);
    if (validSide(dst) && dst != responderSide) {
        std::cout << "[C2C RESP CHOSEN]"
                  << " type=" << getC2cTypeName(pkt)
                  << " rule=ORIGINAL_REQUESTOR"
                  << " src=" << responderSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << "\n";
        return dst;
    }

    dst = routeByMachineID(msg->m_Requestor, -1);
    if (validSide(dst) && dst != responderSide) {
        std::cout << "[C2C RESP CHOSEN]"
                  << " type=" << getC2cTypeName(pkt)
                  << " rule=REQUESTOR"
                  << " src=" << responderSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << "\n";
        return dst;
    }

    dst = routeByMachineID(msg->m_LocalRequestor, -1);
    if (validSide(dst) && dst != responderSide) {
        std::cout << "[C2C RESP CHOSEN]"
                  << " type=" << getC2cTypeName(pkt)
                  << " rule=LOCAL_REQUESTOR"
                  << " src=" << responderSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << "\n";
        return dst;
    }

    dst = routeByC2cDestination(pkt, responderSide);
    if (validSide(dst) && dst != responderSide) {
        std::cout << "[C2C RESP CHOSEN]"
                  << " type=" << getC2cTypeName(pkt)
                  << " rule=C2C_DEST"
                  << " src=" << responderSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << "\n";
        return dst;
    }

    dst = routeByAddress(pkt, responderSide);
    if (validSide(dst) && dst != responderSide) {
        std::cout << "[C2C RESP CHOSEN]"
                  << " type=" << getC2cTypeName(pkt)
                  << " rule=ADDR_FALLBACK"
                  << " src=" << responderSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << "\n";
        return dst;
    }

    dst = routeByMachineID(msg->m_Responder, -1);
    if (validSide(dst) && dst != responderSide) {
        std::cout << "[C2C RESP CHOSEN]"
                  << " type=" << getC2cTypeName(pkt)
                  << " rule=RESPONDER_FALLBACK"
                  << " src=" << responderSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << "\n";
        return dst;
    }

    dst = routeByMachineID(msg->m_OriginalResponder, -1);
    if (validSide(dst) && dst != responderSide) {
        std::cout << "[C2C RESP CHOSEN]"
                  << " type=" << getC2cTypeName(pkt)
                  << " rule=ORIGINAL_RESPONDER_FALLBACK"
                  << " src=" << responderSide
                  << " dst=" << dst
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << "\n";
        return dst;
    }

    std::cout << "[C2C ROUTE ERROR] cannot route RESPONSE"
              << " src=" << responderSide
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " type=" << getC2cTypeName(pkt)
              << " sender=" << machineIdToString(msg->m_Sender)
              << " requestor=" << machineIdToString(msg->m_Requestor)
              << " originalRequestor="
              << machineIdToString(msg->m_OriginalRequestor)
              << " localRequestor="
              << machineIdToString(msg->m_LocalRequestor)
              << " responder=" << machineIdToString(msg->m_Responder)
              << " originalResponder="
              << machineIdToString(msg->m_OriginalResponder)
              << "\n";

    panic("C2CInterposer cannot route response from side %d: %s",
          responderSide, pktToString(pkt).c_str());

    return responderSide;
}

//Funcion de debuggeo para imprimir informacino del routing
void
C2CInterposer::printRoutingInfo(PacketPtr pkt, const char *where,
                                int srcSide, int dstSide) const
{
    if (!hasC2cMsg(pkt)) {
        std::cout << "[C2C ROUTE] " << where
                  << " src=" << srcSide << " dst=" << dstSide
                  << " NO_C2C_MSG " << pktToString(pkt) << "\n";
        return;
    }

    const auto *msg = pkt->c2c_msg;

    std::cout << "[C2C ROUTE] " << where
              << " src=" << srcSide
              << " dst=" << dstSide
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " type=" << getC2cTypeName(pkt)
              << " sender=" << machineIdToString(msg->m_Sender)
              << " requestor=" << machineIdToString(msg->m_Requestor)
              << " originalRequestor=" << machineIdToString(msg->m_OriginalRequestor)
              << " responder=" << machineIdToString(msg->m_Responder)
              << " originalResponder=" << machineIdToString(msg->m_OriginalResponder)
              << " localRequestor=" << machineIdToString(msg->m_LocalRequestor)
              << "\n";
}

/*------------------------------------------------------------*/
/* Stats/debug                                                 */
/*------------------------------------------------------------*/

void
C2CInterposer::recordC2cType(PacketPtr pkt, const char* path, int srcSide)
{
    if (!hasC2cMsg(pkt)) {
        std::cout << "[Interposer] " << path
                  << " side=" << srcSide
                  << " type=NO_C2C_MSG " << pktToString(pkt) << "\n";
        return;
    }

    const int typeId = getC2cTypeId(pkt);
    auto &stats = c2cTypeStats[typeId];

    if (srcSide >= 0 && srcSide < 16) {
        if (std::string(path).find("REQ") == 0) {
            stats.reqFrom[srcSide]++;
        } else {
            stats.respFrom[srcSide]++;
        }
    }

    std::cout << "[Interposer] " << path
              << " side=" << srcSide
              << " c2c_type=" << getC2cTypeName(pkt)
              << " type_id=" << typeId
              << " " << pktToString(pkt)
              << "\n";
}

void
C2CInterposer::dumpC2cTypeStats() const
{
    std::cout << "\n========== C2C TYPE STATS ==========" << "\n";

    if (c2cTypeStats.empty()) {
        std::cout << "No C2C packets recorded.\n";
        std::cout << "====================================\n";
        return;
    }

    for (const auto &entry : c2cTypeStats) {
        const int typeId = entry.first;
        const TypeStats &s = entry.second;
        auto type = static_cast<ruby::C2cRequestType>(typeId);

        std::cout << "type_id=" << std::setw(3) << typeId
                  << " type_name=" << ruby::C2cRequestType_to_string(type);

        for (unsigned i = 0; i < numInterfaces && i < 16; ++i) {
            std::cout << " reqFrom" << i << "=" << s.reqFrom[i]
                      << " respFrom" << i << "=" << s.respFrom[i];
        }
        std::cout << "\n";
    }

    std::cout << "====================================\n";
}

/*------------------------------------------------------------*/
/* Buffers + Round Robin                                       */
/*------------------------------------------------------------*/

/*Busca el ready tick más próximo en las colas del interposer*/
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
        return -2;
    }

    std::sort(candidates.begin(), candidates.end());

    if (buf.lastServedClass == -1) {
        return candidates.front();
    }

    for (int c : candidates) {
        if (c > buf.lastServedClass) {
            return c;
        }
    }

    return candidates.front();
}

bool
C2CInterposer::enqueuePacket(DirBuffer &buf, PacketPtr pkt, Tick delay,
                             unsigned maxSize, const char *path,
                             int srcSide, int dstSide)
{
    const int typeId = getC2cTypeId(pkt);
    const std::string typeName = getC2cTypeName(pkt);
    const C2cMsgClass msgClass = getPacketClass(pkt);
    auto &q = buf.queues[msgClass];

    std::cout << "[C2C DBG ENQUEUE_ENTER]"
              << " tick=" << curTick()
              << " path=" << path
              << " src=" << srcSide
              << " dst=" << dstSide
              << " class=" << getClassName(msgClass)
              << " type_id=" << typeId
              << " type_name=" << typeName
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " pkt=" << pkt
              << " req=" << pkt->req
              << " class_occ_before=" << q.size()
              << " total_occ_before=" << buf.totalSize()
              << "\n";

    for (const auto &entry : buf.queues) {
        const C2cMsgClass existingClass = entry.first;
        const auto &existingQ = entry.second;

        unsigned idx = 0;
        for (const auto &queued : existingQ) {
            PacketPtr qpkt = queued.pkt;

            if (qpkt && qpkt->getAddr() == pkt->getAddr()) {
                std::cout << "[C2C DBG SAME_ADDR_ALREADY_QUEUED]"
                          << " tick=" << curTick()
                          << " path=" << path
                          << " dst=" << dstSide
                          << " queued_idx=" << idx
                          << " queued_class=" << getClassName(existingClass)
                          << " queued_src=" << queued.srcSide
                          << " queued_dst=" << queued.dstSide
                          << " queued_readyTick=" << queued.readyTick
                          << " queued_pkt=" << qpkt
                          << " queued_req=" << qpkt->req
                          << " queued_type=" << getC2cTypeName(qpkt)
                          << " new_pkt=" << pkt
                          << " new_req=" << pkt->req
                          << " new_type=" << typeName
                          << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                          << "\n";
            }

            idx++;
        }
    }

    if (q.size() >= maxSize) {
        std::cout << "[Interposer] " << path
                  << " BUFFER FULL"
                  << " src=" << srcSide
                  << " dst=" << dstSide
                  << " class=" << getClassName(msgClass)
                  << " type_id=" << typeId
                  << " type_name=" << typeName
                  << " class_occ=" << q.size() << "/" << maxSize
                  << " total_occ=" << buf.totalSize()
                  << " addr=0x" << std::hex << pkt->getAddr()
                  << std::dec << "\n";
        return false;
    }

    pkt->headerDelay += delay;
    const Tick ready = curTick() + delay;
    q.push_back({pkt, ready, srcSide, dstSide});

    std::cout << "[Interposer] " << path
              << " src=" << srcSide
              << " dst=" << dstSide
              << " class=" << getClassName(msgClass)
              << " type_id=" << typeId
              << " type_name=" << typeName
              << " add_delay=" << delay
              << " readyTick=" << ready
              << " class_occ=" << q.size() << "/" << maxSize
              << " total_occ=" << buf.totalSize()
              << " addr=0x" << std::hex << pkt->getAddr()
              << std::dec << "\n";

    std::cout << "[C2C DBG ENQUEUE_DONE]"
              << " tick=" << curTick()
              << " path=" << path
              << " src=" << srcSide
              << " dst=" << dstSide
              << " class=" << getClassName(msgClass)
              << " type=" << typeName
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " pkt=" << pkt
              << " req=" << pkt->req
              << " readyTick=" << ready
              << "\n";

    Tick when = nextReadyTick(buf);
    if (when != MaxTick) {
        scheduleBufferEvent(buf, when);
    }

    return true;
}

void
C2CInterposer::scheduleBufferEvent(DirBuffer &buf, Tick when)
{
    if (when == MaxTick) {
        return;
    }

    if (!buf.processEvent.scheduled()) {
        schedule(buf.processEvent, when);
    } else if (buf.processEvent.when() > when) {
        reschedule(buf.processEvent, when);
    }
}

/*------------------------------------------------------------*/
/* Entrada de tráfico                                          */
/*------------------------------------------------------------*/

bool
C2CInterposer::recvReqFromInterface(PacketPtr pkt, int srcSide)
{
    const int dstSide = routeRequest(pkt, srcSide);

    printRoutingInfo(pkt, "REQ", srcSide, dstSide);
    recordC2cType(pkt, "REQ enqueue", srcSide);

    const Tick delay = cyclesToTicks(reqLatency);

    const bool ok = enqueuePacket(*reqTo[dstSide],
                                  pkt,
                                  delay,
                                  reqBufferSize,
                                  "REQ",
                                  srcSide,
                                  dstSide);

    if (!ok) {
        blockedReqFrom[srcSide] = true;

        std::cout << "[C2C REQ BACKPRESSURE]"
                  << " src=" << srcSide
                  << " dst=" << dstSide
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << " pkt=" << pkt
                  << "\n";

        return false;
    }

    return true;
}

bool
C2CInterposer::recvRespFromInterface(PacketPtr pkt, int responderSide)
{
    const int dstSide = routeResponse(pkt, responderSide);

    printRoutingInfo(pkt, "RESP", responderSide, dstSide);
    recordC2cType(pkt, "RESP enqueue", responderSide);

    printC2cMsgDebug(pkt, "RESP_RECV_BEFORE_ENQUEUE", responderSide, dstSide);

    const Tick delay = cyclesToTicks(respLatency);

    const bool ok = enqueuePacket(*respTo[dstSide],
                                  pkt,
                                  delay,
                                  respBufferSize,
                                  "RESP",
                                  responderSide,
                                  dstSide);

    std::cout << "[C2C DBG RESP_ENQUEUE_RESULT]"
              << " tick=" << curTick()
              << " ok=" << ok
              << " src=" << responderSide
              << " dst=" << dstSide
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " type=" << getC2cTypeName(pkt)
              << " pkt=" << pkt
              << " req=" << pkt->req
              << "\n";

    if (!ok) {
        blockedRespFrom[responderSide] = true;

        std::cout << "[C2C RESP BACKPRESSURE]"
                  << " src=" << responderSide
                  << " dst=" << dstSide
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " type=" << getC2cTypeName(pkt)
                  << " pkt=" << pkt
                  << "\n";

        return false;
    }

    return true;
}

Tick
C2CInterposer::recvAtomicFromInterface(PacketPtr pkt, int srcSide)
{
    const int dstSide = routeRequest(pkt, srcSide);
    return toInterfacePorts[dstSide]->sendAtomic(pkt);
}

/*------------------------------------------------------------*/
/* Retry                                                       */
/*------------------------------------------------------------*/

void
C2CInterposer::recvReqRetryToInterface(int dstSide)
{
    std::cout << "[Interposer] RETRY REQ to interface"
              << dstSide << "\n";

    reqTo[dstSide]->waitingRetry = false;
    trySendReqTo(dstSide);
}

void
C2CInterposer::recvRespRetryFromInterface(int srcSide)
{
    std::cout << "[Interposer] RETRY RESP from interface"
              << srcSide << "\n";

    respTo[srcSide]->waitingRetry = false;
    trySendRespTo(srcSide);
}

/*------------------------------------------------------------*/
/* Procesado de eventos                                        */
/*------------------------------------------------------------*/

void
C2CInterposer::processReqTo(int dstSide)
{
    trySendReqTo(dstSide);
}

void
C2CInterposer::processRespTo(int dstSide)
{
    trySendRespTo(dstSide);
}

void
C2CInterposer::trySendReqTo(int dstSide)
{
    DirBuffer &buf = *reqTo[dstSide];

    if (buf.empty() || buf.waitingRetry) {
        return;
    }

    const int classId = selectNextTypeRR(buf, curTick());

    if (classId == -2) {
        Tick when = nextReadyTick(buf);
        if (when != MaxTick) {
            scheduleBufferEvent(buf, when);
        }
        return;
    }

    C2cMsgClass msgClass = static_cast<C2cMsgClass>(classId);
    auto &q = buf.queues[msgClass];
    auto &front = q.front();

    PacketPtr pkt = front.pkt;
    const int srcSide = front.srcSide;

    std::cout << "[C2C REQ DEQUEUE_SEND]"
              << " tick=" << curTick()
              << " src=" << srcSide
              << " dst=" << dstSide
              << " class=" << getClassName(msgClass)
              << " type=" << getC2cTypeName(pkt)
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " pkt=" << pkt
              << " req=" << pkt->req
              << "\n";

    printC2cMsgDebug(pkt, "REQ_DEQUEUE_BEFORE_SEND", srcSide, dstSide);

    const bool accepted = toInterfacePorts[dstSide]->sendTimingReq(pkt);

    std::cout << "[C2C DBG REQ_SEND_RESULT]"
              << " tick=" << curTick()
              << " accepted=" << accepted
              << " src=" << srcSide
              << " dst=" << dstSide
              << " type=" << getC2cTypeName(pkt)
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " pkt=" << pkt
              << " req=" << pkt->req
              << "\n";

    if (!accepted) {
        buf.waitingRetry = true;

        std::cout << "[C2C REQ DOWNSTREAM_BLOCKED]"
                  << " tick=" << curTick()
                  << " dst=" << dstSide
                  << " pkt=" << pkt
                  << "\n";

        return;
    }

    q.pop_front();
    buf.lastServedClass = classId;

    if (q.empty()) {
        buf.queues.erase(msgClass);
    }

    if (validSide(srcSide) && blockedReqFrom[srcSide]) {
        blockedReqFrom[srcSide] = false;

        std::cout << "[Interposer] RELEASE REQ"
                  << " tick=" << curTick()
                  << " src=" << srcSide
                  << " dst=" << dstSide
                  << " class=" << getClassName(msgClass)
                  << " -> sendRetryReq to interface" << srcSide
                  << "\n";

        fromInterfacePorts[srcSide]->sendRetryReq();
    }

    Tick when = nextReadyTick(buf);
    if (when != MaxTick) {
        scheduleBufferEvent(buf, std::max(curTick(), when));
    }
}

void
C2CInterposer::trySendRespTo(int dstSide)
{
    DirBuffer &buf = *respTo[dstSide];

    if (buf.empty() || buf.waitingRetry) {
        return;
    }

    const int classId = selectNextTypeRR(buf, curTick());

    if (classId == -2) {
        Tick when = nextReadyTick(buf);
        if (when != MaxTick) {
            scheduleBufferEvent(buf, when);
        }
        return;
    }

    C2cMsgClass msgClass = static_cast<C2cMsgClass>(classId);
    auto &q = buf.queues[msgClass];
    auto &front = q.front();

    PacketPtr pkt = front.pkt;
    const int responderSide = front.srcSide;

    std::cout << "[C2C RESP DEQUEUE_SEND]"
              << " tick=" << curTick()
              << " src=" << responderSide
              << " dst=" << dstSide
              << " class=" << getClassName(msgClass)
              << " type=" << getC2cTypeName(pkt)
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " pkt=" << pkt
              << " req=" << pkt->req
              << "\n";

    printC2cMsgDebug(pkt, "RESP_DEQUEUE_BEFORE_SEND", responderSide, dstSide);

    if (pkt && pkt->c2c_msg &&
        pkt->c2c_msg->m_Type == ruby::C2cRequestType_SnpResp_SC_Fwded_SC) {
        std::cout << "[C2C DBG TARGET_SNPRESP_SC_FWDED_SC_BEFORE_SEND]"
                  << " tick=" << curTick()
                  << " src=" << responderSide
                  << " dst=" << dstSide
                  << " addr=0x" << std::hex << pkt->getAddr() << std::dec
                  << " pkt=" << pkt
                  << " req=" << pkt->req
                  << "\n";
    }

    const bool accepted = fromInterfacePorts[dstSide]->sendTimingResp(pkt);

    std::cout << "[C2C DBG RESP_SEND_RESULT]"
              << " tick=" << curTick()
              << " accepted=" << accepted
              << " src=" << responderSide
              << " dst=" << dstSide
              << " type=" << getC2cTypeName(pkt)
              << " addr=0x" << std::hex << pkt->getAddr() << std::dec
              << " pkt=" << pkt
              << " req=" << pkt->req
              << "\n";

    if (!accepted) {
        buf.waitingRetry = true;

        std::cout << "[C2C RESP DOWNSTREAM_BLOCKED]"
                  << " tick=" << curTick()
                  << " dst=" << dstSide
                  << " pkt=" << pkt
                  << "\n";

        return;
    }

    q.pop_front();
    buf.lastServedClass = classId;

    if (q.empty()) {
        buf.queues.erase(msgClass);
    }

    if (validSide(responderSide) && blockedRespFrom[responderSide]) {
        blockedRespFrom[responderSide] = false;

        std::cout << "[Interposer] RELEASE RESP"
                  << " tick=" << curTick()
                  << " src=" << responderSide
                  << " dst=" << dstSide
                  << " class=" << getClassName(msgClass)
                  << " -> sendRetryResp to interface" << responderSide
                  << "\n";

        toInterfacePorts[responderSide]->sendRetryResp();
    }

    Tick when = nextReadyTick(buf);
    if (when != MaxTick) {
        scheduleBufferEvent(buf, std::max(curTick(), when));
    }
}

} // namespace gem5
