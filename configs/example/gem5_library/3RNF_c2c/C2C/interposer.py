#importamos todos los objetos de gem5 que se pueden usar en el entorno de 
#configuración (CPUs, caches, buses, controladores de memoria y nuestro C2CInterposer, 
#pero solo si lo hemos registrado en el árbol de gem5).
#si quisieramos solo nuestro C2CInterposer podríamos hacer:
#from m5.objects.C2CInterposer import C2CInterposer.
#además, el módulo "m5" contiene funciones que controlan el simulador, como:
#m5.instantiate() -> para crear los objetos de c++ reales
#m5.simulate() -> para empezar la simulación
from m5.objects import *

#se crea el objeto raíz de la simulación y ponemos que la simulación se a través de 
#"sycall emulation", es decir, gem5 intercepta syscalls, por lo que no hay kernel ni SO completo
root = Root(full_system=False)

#Instanciamos el componente en python y le damos un valor para no usar el que
#trae por defecto (latency = 10). Esto hará que python cree un objeto de configuración
#y luego gem5 al construir el sistema traducirá este objeto a c++:
#Crerará el fichero de cabecera con el struct "C2CInterposerParams" y luego 
#llamará al constructor de c++ de este objeto para pasarlo al dominio de c++
#además, aquí hacemos:
#Primero creo un objeto de configuración con "C2CInterposer(latency=10)", esto solo crea una estructura en python
#que guarda "tipo = C2CInterposer y param latency = 10", y luego debemos hacer que este componente cuelgue del root
#con "root.interposer = ..." y esto implica que root----->interposer, y así construyo la jerarquía. Hasta aquí todavía
#NO existe el objeto real de c++, solo la estructura de python para almacenar la información, para crear el objeto real 
#hay que instanciarlo
root.interposer = C2CInterposer(latency=10)

#Al hacer esta llamada se crean los objetos de c++ reales. El proceso sería 
# primero creamos el Python SimObject tree ----> gem5 genera los Params ----> luego se llama a los constructores de c++
m5.instantiate()
print("C2CInterposer instantiated OK, latency =", root.interposer.latency)

#inicio la simulación y como argumento pongo "1" de forma que solo ocurra 1 tick
m5.simulate(1)