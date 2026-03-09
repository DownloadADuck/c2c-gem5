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
#tratar a esto como un objeto configurable
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

    #definimos los parámetros configurables del componente
    #La sintaxis general es: 
    #nombre = Param.Tipo(valor_por_defecto, "descripción")

    #Se define el parámetro "Latency".
    #Utilizamos la clase Param y el tipo Cycles. Cuando se compile esta línea
    #el "build system" va a generar un fichero de cabecera .hh con un struct donde 
    #se encuentren los valores de estos parámetros, es decir, esto sirve para generar 
    #automáticamente código c++.
    #En este caso, si en nuestro fichero de configuración de python no inicializamos 
    #el objeto al instanciarlo "interposer = C2CInterposer()" se usará el valor por defecto
    #de 1.
    #el segundo parámetro (el de la descripción), lo podemos consultar con --help en configuraciones
    latency = Param.Cycles(1, "Latency of the interposer")