/*Incluimos el fichero de cabecera que creamos antes.*/
#include "mem/c2c_interposer.hh"

/*Vamos a realizar 2 cosas
1. Definir un constructor
2. Definir una lista de inicialización ( : ... , ...) que es una forma 
de realizar la asignación/incialización de variables de una clase den c++*/

//usamos el namespace de gem5 (debe coincidir con el que usamos 
//en python: cxx_class = "gem5::C2CInterposer")
namespace gem5 {

/*Usamos el operador de resolución de ámbito "::" en "C2CInterposer::C2CInterposer(...)"
para indicar que estamos definiendo el constructor de una clase declarada en otro fichero 
(definiendo el constructor C2CInterposer de la clase C2CInterposer).
Recuerda, en el fichero de cabecera del componente declaré la clase así:
class C2CInterposer {
public:
    C2CInterposer(const C2CInterposerParams &params);
};
Y ahora en este .cc lo estoy definiendo, por eso uso el "::", porque
estoy fuera del cuerpo de la clase

El "const C2CInterposerParams &params" significa:
- C2CInterposerParams es el tipo struct generado automaticamente por el build system de
    de gem5
- &params es la referencia, ósea la variable donde recibiré el paquete de parámetros struct
- const significa que es solo lectura, por lo que dentro del constructo no se puede modificar
la variable "params" 

La lista de inicialización: 
: SimObject(params),
  latency(params.latency)
*/
C2CInterposer::C2CInterposer(const C2CInterposerParams &params)
    : SimObject(params),
      latency(params.latency)
    {
    }

}