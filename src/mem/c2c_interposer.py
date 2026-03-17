#importamos todas las clases y helpers de parámetros de gem5:
#Param (que los usamos). También tipos como Cycles, Latency, Bool, etc.
#Param es una clase especial que define parámetros configurables de un SymObject.
#Los tipos de parámetros de Param, gem5 los utiliza para generar código c++ automáticamente
#sobre este componente.
from m5.params import *
#Importa la clase base de python "SimObject", esto es necesario
#porque todos los componentes configurables deben heredar de
# esta clase "SimObject". Cabe mencionar que esta clase evidentemetne
# no implementa el comportamiento del componente, sino que se encarga del
# sistema de configuración y generación de parámetros 
from m5.SimObject import SimObject

#Defino la clase "C2CInterposer" y hacemos que herede de la clase 
#"SimObject". Como mencioné, esto es necesario para que gem5 pueda 
#tratar a esto como un objeto configurable. Entonces va a ser un 
#objeto configurable de gem5 que va a exponer sus puertos
class C2CInterposer(SimObject):

    #"type" es un identificador interno que utiliza gem5 para enlazar 
    # o relacionar esta clase de Python con el fichero de cabecera de c++ 
    # con el struct que contiene los parámetros y la clase de c++ que define el 
    # componente en sí. 
    # Regla: el nombre del tipo de ser el mismo de la clase (por normal general)
    type = "C2CInterposer"

    #indicamos qué clase de C++ implementa el comportamiento

    #en cxx_class guardamos el "nombre fully-qualified" de la clase 
    #de C++ que implementa el objeto/componente, es decir, cuando se instancie
    #este SimObject desde python, el objeto real estará en "gem5::C2CInterposer".
    #Extra:
    #un nombre fully-qualified es aquel que incluye toda la ruta jerárquica necesaria
    #para identificar unívocamente un símbolo (ya sea una función, variable, clase)
    #mediante el operador de ámbito "::". Cada "::" separa un nivel de ámbito 
    # (namespace, clase, struct, enum, etc.).
    cxx_class = "gem5::C2CInterposer"
    #en cxx_header indicamos la ruta del fichero de cabecera de nuestra
    #clase de c++ (aqui ponemos un ruta relativa a src/)
    cxx_header = "mem/c2c_interposer.hh"

    #Se exponen los puertos del Interposer desde python 

    #--------------------------------------------------------
    #puertos interfaz0

    # Declaro un ResponsePort que recibirá Request de la 
    # interface0 (ya que interface0.c2c_out_port es un ResponsePort) y 
    #que las enviará al otro lado
    from_interface0_port = ResponsePort(
        "ResponsePort facing interface0.c2c_out_port"
    )

    # Declaro un RequestPort que reenviará Request de la 
    # interface1 al otro lado, ósea al de inferface0 es por queso que 
    # se conecta al puerto interface0.c2c_in_port
    to_interface0_port = RequestPort(
        "RequestPort facing interface0.c2c_in_port"
    )
    #--------------------------------------------------------
    #puertos interfaz 1

    # Declaro un ResponsePort que recibirá Request de la 
    # interface1 (ya que interface1.c2c_out_port es un ResponsePort) y 
    #que las enviará al otro lado
    from_interface1_port = ResponsePort(
        "ResponsePort facing interface1.c2c_out_port"
    )

    # Declaro un RequestPort que reenviará Request de la 
    # interface0 al otro lado, ósea al de inferface1 es por queso que 
    # se conecta al puerto interface0.c2c_in_port
    to_interface1_port = RequestPort(
        "RequestPort facing interface1.c2c_in_port"
    )