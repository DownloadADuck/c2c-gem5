from m5.params import *
from m5.proxy import *
from m5.SimObject import SimObject
from m5.objects.ClockedObject import ClockedObject

class C2CInterposer(ClockedObject):
    type = "C2CInterposer"
    cxx_header = "mem/c2c_interposer.hh"
    cxx_class = "gem5::C2CInterposer"

    # NUEVO:
    # Antes el interposer tenía 4 puertos fijos:
    #   from_interface0_port, to_interface0_port,
    #   from_interface1_port, to_interface1_port.
    # Eso solo sirve para una conexión punto a punto entre 2 chips.
    # Ahora lo convertimos en un MUX C2C con puertos vectoriales:
    #   - from_interfaces[i]: puerto ResponsePort por donde entra tráfico desde el chip i.
    #   - to_interfaces[i]:   puerto RequestPort por donde sale tráfico hacia el chip i.
    # Así se pueden conectar 3 chips, o más, a una única entidad central.
    from_interfaces = VectorResponsePort("C2C input ports from chip interfaces")
    to_interfaces = VectorRequestPort("C2C output ports to chip interfaces")

    # Número de chips/interfaces conectadas al MUX.
    # Para tu threec_cache_hierarchy.py debe ser 3.
    num_interfaces = Param.Unsigned(2, "Number of C2C chip interfaces attached to the mux")

    # Latencia que el MUX añade a mensajes que viajan por el canal de request/snoop.
    req_latency = Param.Cycles(1, "Latency added to C2C request/snoop traffic")

    # Latencia que el MUX añade a mensajes que viajan por el canal de response/data.
    resp_latency = Param.Cycles(1, "Latency added to C2C response/data traffic")

    # Tamaño máximo de cada cola por clase lógica y por chip destino.
    # No es un único buffer global: hay una cola por destino y por clase
    # Request/Snoop/Response/Data.
    req_buffer_size = Param.Unsigned(8, "Per-class request/snoop buffer size per destination")
    resp_buffer_size = Param.Unsigned(8, "Per-class response/data buffer size per destination")

    # Rangos de memoria por chip. El índice de la lista es el chipID.
    # Se usa como fallback de routing para requests cuando no basta con m_Destination.
    c2c_mem_ranges = VectorParam.AddrRange([], "Memory ranges owned by each chip")

    # Mapa Cache_Controller.version -> chipID.
    # Es el mismo cacheChipIDList que ya estabas construyendo en la jerarquía.
    # Se usa como fallback para enrutar respuestas mirando MachineID.
    cache_chip_id_list = VectorParam.Int([], "Cache controller version to chipID mapping")

    # Mapa Interface_Controller.version -> chipID.
    # Normalmente, para 3 chips será [0, 1, 2].
    interface_chip_id_list = VectorParam.Int([], "Interface controller version to chipID mapping")
