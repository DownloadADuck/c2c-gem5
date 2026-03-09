#ifndef __MEM_C2C_INTERPOSER_HH__
#define __MEM_C2C_INTERPOSER_HH__

//incluyo el fichero de cabecera con el tipo struct para los parámetros del componente 
//(el que se autogenera el compilar gem5)
#include "params/C2CInterposer.hh"
//hay que incluir este fichero de cabecera porque el componente hereda de SimObject
#include "sim/sim_object.hh"

//el namespace debe ser el mismo que utilizé al definir el componente en el .py "cxx_class = "gem5::C2CInterposer""
namespace gem5 {

/*Pongo la definición de la clase y pongo que hereda de SimbObject*/
class C2CInterposer : public SimObject
{
    //atributos privados de la clase, aqui se guarda el parametro enviado desde python
  private:

    Cycles latency;

  public:
    //declaro el constructor de la clase, el cual implemento en el .cc
    C2CInterposer(const C2CInterposerParams &params);
};

}

#endif