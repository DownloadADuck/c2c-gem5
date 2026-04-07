#ifndef __MEM_C2C_INTERPOSER_HH__
#define __MEM_C2C_INTERPOSER_HH__

//incluyo el fichero de cabecera con el tipo struct para los parámetros del componente 
//(el que se autogenera el compilar gem5)
#include "params/C2CInterposer.hh"
//hay que incluir este fichero de cabecera porque el componente hereda de SimObject
#include "sim/sim_object.hh"
//Incluye la definición de "Packet" y "PacketPtr"
#include "mem/packet.hh"
//incluímos las clases base de "RequestPort" y "ResponsePort"
#include "mem/port.hh"
using namespace std;
//así evitamos usar std::string y solo hacemos string
#include <string>

#include "sim/clocked_object.hh"

#include <deque>
#include "sim/eventq.hh"

//el namespace debe ser el mismo que utilizé al definir el componente en el .py "cxx_class = "gem5::C2CInterposer""
namespace gem5 {

/*Pongo la definición de la clase y pongo que hereda de SimbObject*/
class C2CInterposer : public ClockedObject
{
    //atributos privados de la clase, aqui se guarda el parametro enviado desde python
  private:

    //declaro los puertos donde se heredarán las clases abstractas RequesPort y ResponsePort
    //la herencia la haré después de declarar todos los atributos y algunos metodos
    class ToInterfacePort : public RequestPort //Hereda de RequestPort (inicia peticiones)
    {
        private:
            /*estoy dentro de una clase anidada (esto es diferente a clase hija ya que no hay herencia)
            por lo que para saber quién es el componente externo, es decir, el que contiene al puerto, 
            le indico quién es el dueño, que sería la instancia concreta del interposer, ya que
            de otra forma no se podría saber*/
            C2CInterposer * owner;

            //indico el lado de la interfaz al que se refiere (interfaz 0 o 1)
            int side;

        public:
            //constrctor del puerto de Request
            ToInterfacePort( 
                const string &name, //no lo pongo como atributo porque va a ser una constante
                C2CInterposer * owner,
                int side
            );

            //sobrescribo los métodos de RequestPort no implementados 
            bool recvTimingResp(PacketPtr pkt) override;
            void recvReqRetry() override;
            
    };
    class FromInterfacePort : public ResponsePort //Hereda de ResponsePort (responde peticiones)
    {
        private:
            //atributos iguales al de Request
            C2CInterposer * owner;

            int side;
        public:
            //constructo del puerto de Response
            FromInterfacePort( 
                const string &name, //no lo pongo como atributo porque va a ser una constante
                C2CInterposer * owner,
                int side
            );

        //sobrescribo los métodos de ResponsePort no implementados 

            //Devuelve los rangos de direcciones que acepta este puerto
            AddrRangeList getAddrRanges() const override;
            void recvFunctional(PacketPtr pkt) override;
            bool recvTimingReq(PacketPtr pkt) override;
            void recvRespRetry() override;
            Tick recvAtomic(PacketPtr pkt) override;
    };
    
    //declaro los punteros a los puertos (de las clases de arriba)
    //que van a ser atributos de la clase C2CInterface

    /*-------------------------------------*/
    //puerto de Request de la interface0
    ToInterfacePort * toInterface0Port;
    //puerto de Response de la interface0
    FromInterfacePort * fromInterface0Port;
    /*-------------------------------------*/
    //puerto de Request de la interface1
    ToInterfacePort * toInterface1Port;
    //puerto de Response de la interface1
    FromInterfacePort * fromInterface1Port;
    /*-------------------------------------*/

    //declaración métodos para procesar Request y Responses de los puertos 

    /*-------------------------------------*/
    //declaro método para procesar Request interface0
    bool recvReqFromInterface0(PacketPtr pkt); //el argumento es un Packet (ver apuntes)
    //declaro método para procesar Responses interface0
    bool recvRespFromInterface0(PacketPtr pkt);
    /*-------------------------------------*/
    //declaro método para procesar Request interface1
    bool recvReqFromInterface1(PacketPtr pkt); //el argumento es un Packet (ver apuntes)
    //declaro método para procesar Responses interface1
    bool recvRespFromInterface1(PacketPtr pkt);
    /*-------------------------------------*/

    //declaración de métodos para procesar señales de retry de Request y de Response de los puertos

    /*-------------------------------------*/
    //declaro método para procesar retry de request interface0
    void recvReqRetryToInterface0(); 
    //declaro método para procesar retry de response interface0
    void recvRespRetryFromInterface0();
    /*-------------------------------------*/
    //declaro método para procesar retry de request interface1
    void recvReqRetryToInterface1(); 
    //declaro método para procesar retry de response interface1
    void recvRespRetryFromInterface1();
    /*-------------------------------------*/

    /*-------------------------------*/
    //metodos para manejar request atomicas 
    Tick recvAtomicFromInterface0(PacketPtr pkt);
    Tick recvAtomicFromInterface1(PacketPtr pkt);

    //latencias 
    const Cycles reqLatency;
    const Cycles respLatency;

     // Tamaños máximos de buffer abstracto
    const unsigned reqBufferSize;
    const unsigned respBufferSize;

    // Ocupación actual por dirección/tipo
    unsigned occReq0to1 = 0;
    unsigned occReq1to0 = 0;
    unsigned occResp0to1 = 0;
    unsigned occResp1to0 = 0;

    // Flags: hubo un bloqueo por "buffer lleno"
    bool bufBlockedReq0to1 = false;
    bool bufBlockedReq1to0 = false;
    bool bufBlockedResp0to1 = false;
    bool bufBlockedResp1to0 = false;

    // Ticks futuros de liberación de slots
    std::deque<Tick> relReq0to1;
    std::deque<Tick> relReq1to0;
    std::deque<Tick> relResp0to1;
    std::deque<Tick> relResp1to0;

    // Eventos de liberación
    EventFunctionWrapper releaseReq0to1Event;
    EventFunctionWrapper releaseReq1to0Event;
    EventFunctionWrapper releaseResp0to1Event;
    EventFunctionWrapper releaseResp1to0Event;

    // Helpers para programar y ejecutar liberaciones
    void schedReleaseReq0to1();
    void schedReleaseReq1to0();
    void schedReleaseResp0to1();
    void schedReleaseResp1to0();

    void releaseReq0to1();
    void releaseReq1to0();
    void releaseResp0to1();
    void releaseResp1to0();

  public:
    //declaro el constructor de la clase, el cual implemento en el .cc
    C2CInterposer(const C2CInterposerParams &params);

    //a través de este método de la clase C2CInterposer 
    //se va a permitir acceder a gem5 a los puertos mandado como 
    //argumento su nombre (del puerto)
    Port &getPort(
        const std::string &if_name,
        PortID idx = InvalidPortID
    ) override;
};

}

#endif