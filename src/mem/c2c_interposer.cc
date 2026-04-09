/*Incluimos el fichero de cabecera que creamos antes.*/
#include "mem/c2c_interposer.hh"
//incluye panic()
#include "base/logging.hh"
#include "base/trace.hh"

#include <sstream>
#include "debug/C2CInterposer.hh"

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

/*Usamos el operador de resolución de ámbito "::" en "C2CInterposer::FromInterfacePort(...)"
para indicar que vamos a acceder a la clase privada que está dentro de C2CInterposer y luego
volvemos a usar el operador de ámbito "::" para definir el constructor de esa clase
así "FromInterfacePort::FromInterfacePort(...)". Resto lo hacemos porque en el fichero de cabecera del componente declaré la clase así:
class C2CInterposer la cual dentro tiene como miembro privado la clase "FromInterfacePort"
Y ahora en este .cc lo estoy definiendo, por eso uso el "::", porque
estoy fuera del cuerpo de la clase.
C2CInterposer::FromInterfacePort::FromInterfacePort(
    const std::string &name,
    C2CInterposer *owner,
    int side
)
Una vez definido el constructor de "FromInterfacePort" al poner los ":" 
pasamos a definir la lista de inicialización de éste mismo, ósea, les damos
valores de golpe.
Recuerda, FromInterfacePort hereda de RespondePort
*/
C2CInterposer::FromInterfacePort::FromInterfacePort(
    const std::string &name, //nombre del puerto
    C2CInterposer *owner, //puntero al interposer dueño
    int side //el lado del interposer (0 o 1)
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
    const std::string &name, //nombre del puerto
    C2CInterposer *owner, //puntero al interposer dueño
    int side //el lado del interposer (0 o 1)
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
    [this] { processResp1to0(); }, name() + ".processResp1to0"))) /*Se usa la lista de inicialización 
    para construir el objeto base SimbOject y luego dentro de las 
    llaves "{}" se ejecuta el código del constructor 
    de C2CInterposer para crear dinámicamente 4 objetos que van a ser 
    los puertos y se guardan como atributos de la clase C2CInterface*/
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
        csprintf("%s.from_interface0_port", name()), /*le damos el nombre al puerto:
        name() devuelve el nombre del objeto Interposer y "csprint" formatea el texto, 
        de forma que el resultado quedaría algo así: interposer0.from_interface0_port*/
        this, //le damos la dirección del Interposer como owner, como estamos 
        //dentro de su constructor "this" es el puntero a la C2CInterposer objeto
        0 //el lado
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

/*-----------------------------------------------------------*/
//                 Lógica de reenvío de Request (bridge de Request)    
//                  cualquier duda de esta zona, ver apuntes sobre la latencia           
/*------------------------------------------------------------*/

/*Si llega una request desde la interfaz 0 lo reenvío a la 1 inmediatamente*/
bool
C2CInterposer::recvReqFromInterface0(PacketPtr pkt)
{
    // Interfaz0 -> Interfaz1
    Tick delay = cyclesToTicks(reqLatency);

    if (req0to1.q.size() >= reqBufferSize) {
        std::cout << "[Interposer] REQ 0->1 BUFFER FULL addr=0x"
                  << std::hex << pkt->getAddr()
                  << std::dec << " occ=" << req0to1.q.size()
                  << "/" << reqBufferSize << "\n";
        return false;
    }

    pkt->headerDelay += delay;

    req0to1.q.push_back({pkt, curTick() + delay});

    std::cout << "[Interposer] REQ 0->1 addr=0x"
              << std::hex << pkt->getAddr()
              << std::dec << " add_delay=" << delay
              << " occ=" << req0to1.q.size() << "/" << reqBufferSize << "\n";

    scheduleBufferEvent(req0to1, req0to1.q.front().readyTick);

    return true;
}

/*Si llega una request desde la interfaz 1 lo reenvío a la 0 inmediatamente*/
bool
C2CInterposer::recvReqFromInterface1(PacketPtr pkt)
{
    // Interfaz1 -> Interfaz0
    Tick delay = cyclesToTicks(reqLatency);

    if (req1to0.q.size() >= reqBufferSize) {
        std::cout << "[Interposer] REQ 1->0 BUFFER FULL addr=0x"
                  << std::hex << pkt->getAddr()
                  << std::dec << " occ=" << req1to0.q.size()
                  << "/" << reqBufferSize << "\n";
        return false;
    }

    pkt->headerDelay += delay;

    req1to0.q.push_back({pkt, curTick() + delay});

    std::cout << "[Interposer] REQ 1->0 addr=0x"
              << std::hex << pkt->getAddr()
              << std::dec << " add_delay=" << delay
              << " occ=" << req1to0.q.size() << "/" << reqBufferSize << "\n";

    scheduleBufferEvent(req1to0, req1to0.q.front().readyTick);

    return true;
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
    Tick delay = cyclesToTicks(respLatency);

    if (resp0to1.q.size() >= respBufferSize) {
        std::cout << "[Interposer] RESP 0->1 BUFFER FULL addr=0x"
                  << std::hex << pkt->getAddr()
                  << std::dec << " occ=" << resp0to1.q.size()
                  << "/" << respBufferSize << "\n";
        return false;
    }

    pkt->headerDelay += delay;

    resp0to1.q.push_back({pkt, curTick() + delay});

    std::cout << "[Interposer] RESP 0->1 addr=0x"
              << std::hex << pkt->getAddr()
              << std::dec << " add_delay=" << delay
              << " occ=" << resp0to1.q.size() << "/" << respBufferSize << "\n";

    scheduleBufferEvent(resp0to1, resp0to1.q.front().readyTick);

    return true;
}

/*Si llega una Responset desde la interfaz 1 lo reenvío a la 0 inmediatamente*/
bool
C2CInterposer::recvRespFromInterface1(PacketPtr pkt)
{
    // Respuesta que vuelve desde Interface1 hacia Interfaz0
    Tick delay = cyclesToTicks(respLatency);

    if (resp1to0.q.size() >= respBufferSize) {
        std::cout << "[Interposer] RESP 1->0 BUFFER FULL addr=0x"
                  << std::hex << pkt->getAddr()
                  << std::dec << " occ=" << resp1to0.q.size()
                  << "/" << respBufferSize << "\n";
        return false;
    }

    pkt->headerDelay += delay;

    resp1to0.q.push_back({pkt, curTick() + delay});

    std::cout << "[Interposer] RESP 1->0 addr=0x"
              << std::hex << pkt->getAddr()
              << std::dec << " add_delay=" << delay
              << " occ=" << resp1to0.q.size() << "/" << respBufferSize << "\n";

    scheduleBufferEvent(resp1to0, resp1to0.q.front().readyTick);

    return true;
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
    if (req0to1.q.empty()) {
        return;
    }

    auto &front = req0to1.q.front();

    if (front.readyTick > curTick()) {
    scheduleBufferEvent(req0to1, front.readyTick);
    return;
}

    if (req0to1.waitingRetry) {
        return;
    }

    if (!toInterface1Port->sendTimingReq(front.pkt)) {
        req0to1.waitingRetry = true;
        return;
    }

    req0to1.q.pop_front();

    if (req0to1.q.size() + 1 == reqBufferSize) {
        std::cout << "[Interposer] RELEASE REQ 0->1 -> sendRetryReq to interface0\n";
        fromInterface0Port->sendRetryReq();
    }

    if (!req0to1.q.empty()) {
    scheduleBufferEvent(
        req0to1,
        std::max(curTick(), req0to1.q.front().readyTick)
    );
}
}

void
C2CInterposer::trySendReq1to0()
{
    if (req1to0.q.empty()) {
        return;
    }

    auto &front = req1to0.q.front();

    if (front.readyTick > curTick()) {
    scheduleBufferEvent(req1to0, front.readyTick);
    return;
    }

    if (req1to0.waitingRetry) {
        return;
    }

    if (!toInterface0Port->sendTimingReq(front.pkt)) {
        req1to0.waitingRetry = true;
        return;
    }

    req1to0.q.pop_front();

    if (req1to0.q.size() + 1 == reqBufferSize) {
        std::cout << "[Interposer] RELEASE REQ 1->0 -> sendRetryReq to interface1\n";
        fromInterface1Port->sendRetryReq();
    }

    if (!req1to0.q.empty()) {
    scheduleBufferEvent(
        req1to0,
        std::max(curTick(), req1to0.q.front().readyTick)
        );
    }
}

void
C2CInterposer::trySendResp0to1()
{
    if (resp0to1.q.empty()) {
        return;
    }

    auto &front = resp0to1.q.front();

    if (front.readyTick > curTick()) {
    scheduleBufferEvent(resp0to1, front.readyTick);
    return;
    }

    if (resp0to1.waitingRetry) {
        return;
    }

    if (!fromInterface1Port->sendTimingResp(front.pkt)) {
        resp0to1.waitingRetry = true;
        return;
    }

    resp0to1.q.pop_front();

    if (resp0to1.q.size() + 1 == respBufferSize) {
        std::cout << "[Interposer] RELEASE RESP 0->1 -> sendRetryResp to interface0\n";
        toInterface0Port->sendRetryResp();
    }

    if (!resp0to1.q.empty()) {
    scheduleBufferEvent(
        resp0to1,
        std::max(curTick(), resp0to1.q.front().readyTick)
        );
    }
}

void
C2CInterposer::trySendResp1to0()
{
    if (resp1to0.q.empty()) {
        return;
    }

    auto &front = resp1to0.q.front();

    if (front.readyTick > curTick()) {
    scheduleBufferEvent(resp1to0, front.readyTick);
    return;
    }

    if (resp1to0.waitingRetry) {
        return;
    }

    if (!fromInterface0Port->sendTimingResp(front.pkt)) {
        resp1to0.waitingRetry = true;
        return;
    }

    resp1to0.q.pop_front();

    if (resp1to0.q.size() + 1 == respBufferSize) {
        std::cout << "[Interposer] RELEASE RESP 1->0 -> sendRetryResp to interface1\n";
        toInterface1Port->sendRetryResp();
    }

    if (!resp1to0.q.empty()) {
    scheduleBufferEvent(
        resp1to0,
        std::max(curTick(), resp1to0.q.front().readyTick)
        );
    }
}

//helper 

void
C2CInterposer::scheduleBufferEvent(DirBuffer &buf, Tick when)
{
    if (!buf.processEvent.scheduled()) {
        schedule(buf.processEvent, when);
    }
}



}