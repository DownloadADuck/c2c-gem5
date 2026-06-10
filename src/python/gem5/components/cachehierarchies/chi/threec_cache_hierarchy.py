import sys
from itertools import chain
from typing import List

from m5.objects.SubSystem import SubSystem
from gem5.components.cachehierarchies.ruby.abstract_ruby_cache_hierarchy import (
    AbstractRubyCacheHierarchy,
)
from gem5.components.cachehierarchies.abstract_cache_hierarchy import (
    AbstractCacheHierarchy,
)
from gem5.coherence_protocol import CoherenceProtocol
from gem5.isas import ISA
from gem5.utils.requires import requires
from gem5.utils.override import overrides
from gem5.components.boards.abstract_board import AbstractBoard
from gem5.components.processors.abstract_core import AbstractCore

from gem5.components.cachehierarchies.ruby.topologies.simple_pt2pt import (
    SimplePt2Pt,
)

from .nodes.private_l1_moesi_cache import PrivateL1MOESICache
from .nodes.shared_l2_moesi_cache import SharedL2MOESICache
from .nodes.dma_requestor import DMARequestor
from .nodes.directory import SimpleDirectory
from .nodes.memory_controller import MemoryController
from .nodes.interface import Interface

# ---------------- NUEVO ----------------
# Añadimos C2CInterposer al import de m5.objects para poder instanciar
# nuestro SimObject desde esta jerarquía Ruby.
#
# Antes solo se conectaban las interfaces C2C directamente entre ellas.
# Ahora vamos a colocar una única entidad central tipo mux/router.
from m5.objects import NULL, RubySystem, RubySequencer, RubyPortProxy, C2CInterposer
# ---------------- FIN NUEVO ----------------


class ThreeCCacheHierarchy(AbstractRubyCacheHierarchy):
    """ Three-Chip coherent chiplet-based architecture
    
    Each chips has two L1s, one shared L2 and one RNF.
     
    The network is a simple point-to-point between all of the controllers.
    Connection between chips is also point-to-point. 
    """

    def __init__(
        self,
        l1_size: str, 
        l1_assoc: int,
        l2_size: str, 
        l2_assoc: int,
        ) -> None:
        super().__init__() 

        self._l1_size = l1_size
        self._l1_assoc = l1_assoc
        self._l2_size = l2_size
        self._l2_assoc = l2_assoc

    @overrides(AbstractCacheHierarchy)
    def incorporate_cache(self, board: AbstractBoard) -> None:
        
        requires(coherence_protocol_required=CoherenceProtocol.CHI)

        self.ruby_system = RubySystem()

        cluster0_dest = []
        cluster1_dest = []
        cluster2_dest = []
        mem_ranges = []

        # C2c specific list
        # Allows to build the machineID -> ChipID LUT
        cacheChipIDList = []
    
        for rng, port in board.get_mem_ports():
            mem_ranges.append(rng)

        # Three networks, one Ruby network per chip
        self.ruby_system.network0 = SimplePt2Pt(self.ruby_system)
        self.ruby_system.network1 = SimplePt2Pt(self.ruby_system)
        self.ruby_system.network2 = SimplePt2Pt(self.ruby_system)

        # Network configuration
        # virtual networks: 0=requests, 1=snoops, 2=responses, 3=data
        self.ruby_system.number_of_virtual_networks = 4
        self.ruby_system.network0.number_of_virtual_networks = 4
        self.ruby_system.network1.number_of_virtual_networks = 4
        self.ruby_system.network2.number_of_virtual_networks = 4

        # Create a single HNF per chip
        self.hnf0 = SimpleDirectory(
            self.ruby_system.network0,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[0]],
            chipID=0,
            cacheChipIDList=cacheChipIDList,
        )
        self.hnf1 = SimpleDirectory(
            self.ruby_system.network1,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[1]],
            chipID=1,
            cacheChipIDList=cacheChipIDList,
        )
        self.hnf2 = SimpleDirectory(
            self.ruby_system.network2,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[2]],
            chipID=2,
            cacheChipIDList=cacheChipIDList,
        )
        
        self.hnf0.ruby_system = self.ruby_system
        self.hnf1.ruby_system = self.ruby_system
        self.hnf2.ruby_system = self.ruby_system
        
        # Add to the RNF destinations
        cluster0_dest.append(self.hnf0)
        cluster1_dest.append(self.hnf1)

        # ---------------- NUEVO ----------------
        # En tu fichero original aquí tenías:
        #
        #   cluster2_dest.append(self.hnf1)
        #
        # Eso estaba mal porque el chip 2 debe tener como destino local su HNF
        # local, es decir, hnf2. Si dejábamos hnf1, el chip 2 quedaba asociado
        # incorrectamente al HNF del chip 1.
        cluster2_dest.append(self.hnf2)
        # ---------------- FIN NUEVO ----------------

        # ---------------- NUEVO ----------------
        # Create one C2C Interface per chip.
        #
        # Antes esta topología tenía una Interface por enlace punto a punto:
        #
        #   chip 0 -> chip 1
        #   chip 0 -> chip 2
        #   chip 1 -> chip 0
        #   chip 1 -> chip 2
        #   chip 2 -> chip 0
        #   chip 2 -> chip 1
        #
        # Es decir, 6 interfaces:
        #
        #   interface00, interface01,
        #   interface10, interface11,
        #   interface20, interface21.
        #
        # Ahora queremos una única entidad central, C2CInterposer, que funcione
        # como multiplexor/router. Por eso cada chip solo necesita una interface
        # C2C local hacia el mux.
        #
        # Cada Interface anuncia los rangos remotos que puede alcanzar a través
        # del mux. Por ejemplo, el chip 0 puede alcanzar los rangos de memoria
        # del chip 1 y del chip 2.
        # ---------------- FIN NUEVO ----------------

        # Chip 0: puede alcanzar memoria remota de chip 1 y chip 2.
        self.interface0 = Interface(
            self.ruby_system.network0,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[1], mem_ranges[2]],
            chipID=0,
        )

        # Chip 1: puede alcanzar memoria remota de chip 0 y chip 2.
        self.interface1 = Interface(
            self.ruby_system.network1,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[0], mem_ranges[2]],
            chipID=1,
        )

        # Chip 2: puede alcanzar memoria remota de chip 0 y chip 1.
        self.interface2 = Interface(
            self.ruby_system.network2,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[0], mem_ranges[1]],
            chipID=2,
        )

        self.interface0.ruby_system = self.ruby_system
        self.interface1.ruby_system = self.ruby_system
        self.interface2.ruby_system = self.ruby_system

                # ---------------- NUEVO ----------------
        # Instanciamos el interposer/mux central.
        #
        # IMPORTANTE:
        # Lo colgamos de ruby_system para que gem5 lo considere parte del
        # árbol de SimObjects que debe construir.
        #
        # Además usamos una variable local llamada c2c_interposer para no crear
        # un atributo nuevo en ThreeCCacheHierarchy. Crear self.c2c_interposer
        # puede dar problemas porque ThreeCCacheHierarchy no declara ese atributo
        # como parámetro SimObject.
        # ---------------- FIN NUEVO ----------------
        self.ruby_system.c2c_interposer = C2CInterposer(
            clk_domain=board.get_clock_domain(),
            num_interfaces=3,
            req_latency=5,
            resp_latency=5,
            req_buffer_size=64,
            resp_buffer_size=64,
            c2c_mem_ranges=[
                mem_ranges[0],
                mem_ranges[1],
                mem_ranges[2],
            ],
            interface_chip_id_list=[
                0,
                1,
                2,
            ],
        )
        
        # Variable local para escribir el cableado de forma más limpia.
        c2c_interposer = self.ruby_system.c2c_interposer

                # ---------------- NUEVO ----------------
        # C2C wiring through the central mux.
        #
        # El interposer nuevo usa puertos vectoriales:
        #
        #   from_interfaces:
        #       entradas hacia el interposer.
        #       Aquí conectamos las salidas C2C de cada chip.
        #
        #   to_interfaces:
        #       salidas desde el interposer.
        #       Aquí conectamos las entradas C2C de cada chip.
        #
        # El orden de estas conexiones es importante porque define el índice
        # interno del puerto vectorial:
        #
        #   from_interfaces[0] / to_interfaces[0] -> chip 0
        #   from_interfaces[1] / to_interfaces[1] -> chip 1
        #   from_interfaces[2] / to_interfaces[2] -> chip 2
        #
        # Esos índices deben coincidir con chipID.
        # ---------------- FIN NUEVO ----------------

        # Chip 0 -> Interposer
        self.interface0.c2c_out_port = c2c_interposer.from_interfaces

        # Chip 1 -> Interposer
        self.interface1.c2c_out_port = c2c_interposer.from_interfaces

        # Chip 2 -> Interposer
        self.interface2.c2c_out_port = c2c_interposer.from_interfaces

        # Interposer -> Chip 0
        c2c_interposer.to_interfaces = self.interface0.c2c_in_port

        # Interposer -> Chip 1
        c2c_interposer.to_interfaces = self.interface1.c2c_in_port

        # Interposer -> Chip 2
        c2c_interposer.to_interfaces = self.interface2.c2c_in_port

        # Downstream destinations
        # ---------------- NUEVO ----------------
        # Cada interface C2C pertenece a un chip local.
        #
        # Cuando un paquete entra desde el interposer hacia un chip, la interface
        # C2C de ese chip debe poder reenviarlo hacia el HNF local.
        #
        # Antes había dos interfaces por chip y ambas apuntaban al mismo HNF
        # local. Ahora solo hay una interface por chip.
        # ---------------- FIN NUEVO ----------------
        self.interface0.downstream_destinations = self.hnf0
        self.interface1.downstream_destinations = self.hnf1
        self.interface2.downstream_destinations = self.hnf2

        # Add to the RNF destinations
        # ---------------- NUEVO ----------------
        # Añadimos la interface C2C local de cada chip a sus destinos.
        #
        # Así, si una L2/RNF local quiere acceder a memoria remota, no elige
        # directamente un enlace punto a punto. Simplemente envía hacia su
        # interface C2C local, y el interposer central decide a qué chip mandar
        # el paquete.
        # ---------------- FIN NUEVO ----------------
        cluster0_dest.append(self.interface0)
        cluster1_dest.append(self.interface1)
        cluster2_dest.append(self.interface2)
        
        # Create two core cluster with split I/D cache for each core
        self.core_cluster0 = [
            self._create_core_cluster(
                (board.get_processor().get_cores())[0],
                0,
                board,
                self.ruby_system.network0,
                cluster0_dest,
                chipID=0,
                cacheChipIDList=cacheChipIDList,
            ),
            self._create_core_cluster(
                (board.get_processor().get_cores())[1],
                1,
                board,
                self.ruby_system.network0,
                cluster0_dest,
                chipID=0,
                cacheChipIDList=cacheChipIDList,
            )
        ]
        self.core_cluster1 = [
            self._create_core_cluster(
                (board.get_processor().get_cores())[2],
                2,
                board,
                self.ruby_system.network1,
                cluster1_dest,
                chipID=1,
                cacheChipIDList=cacheChipIDList,
            )
        ]

        # ---------------- NUEVO ----------------
        # En el fichero original, core_cluster2 usaba network1 y cluster1_dest.
        # Eso hacía que el chip 2 quedara conectado lógicamente a la red y
        # destinos del chip 1.
        #
        # El chip 2 debe usar:
        #
        #   - network2
        #   - cluster2_dest
        #   - chipID=2
        # ---------------- FIN NUEVO ----------------
        self.core_cluster2 = [
            self._create_core_cluster(
                (board.get_processor().get_cores())[3],
                3,
                board,
                self.ruby_system.network2,
                cluster2_dest,
                chipID=2,
                cacheChipIDList=cacheChipIDList,
            )
        ]

        # Create the coherent side of the memory controllers
        self.memory_controllers0 = self._create_memory_controllers(
                board,
                self.ruby_system.network0, 
                rng_idx=0, 
            )
        self.hnf0.downstream_destinations = self.memory_controllers0

        self.memory_controllers1 = self._create_memory_controllers(
                board,
                self.ruby_system.network1, 
                rng_idx=1, 
            )
        self.hnf1.downstream_destinations = self.memory_controllers1
        
        self.memory_controllers2 = self._create_memory_controllers(
                board,
                self.ruby_system.network2, 
                rng_idx=2, 
            )
        self.hnf2.downstream_destinations = self.memory_controllers2

        # Create the DMA Controllers, if required.
        if board.has_dma_ports():
            self.dma_controllers0 = self._create_dma_controllers(
                board, 
                network=self.ruby_system.network0,
                cluster_dest=cluster0_dest,
                chipID=0,
                cacheChipIDList=cacheChipIDList,
            )

            # ---------------- NUEVO ----------------
            # El cálculo original no incluía core_cluster2.
            #
            # Cada core tiene dos sequencers en esta jerarquía:
            #
            #   - icache sequencer
            #   - dcache sequencer
            #
            # Por eso multiplicamos por 2.
            # ---------------- FIN NUEVO ----------------
            self.ruby_system.num_of_sequencers = (
                len(self.core_cluster0) +
                len(self.core_cluster1) +
                len(self.core_cluster2)
            ) * 2 + len(self.dma_controllers0)

        else:
            # ---------------- NUEVO ----------------
            # El cálculo original solo sumaba core_cluster0 y core_cluster1.
            # Añadimos core_cluster2 para que Ruby conozca el número correcto
            # de sequencers del sistema completo de 3 chips.
            # ---------------- FIN NUEVO ----------------
            self.ruby_system.num_of_sequencers = (
                len(self.core_cluster0) +
                len(self.core_cluster1) +
                len(self.core_cluster2)
            ) * 2

        ############################# C2C SETUP #############

        def set_c2c_routes(ctrl, local_chip: int):
            """
            Topología C2C actual: 3 chips, 1 Interface C2C por chip.

            Cada controlador de un chip debe saber qué Interface local usar para
            llegar a los otros chips.

            Chip 0:
              chip remoto 1 -> Interface-0
              chip remoto 2 -> Interface-0

            Chip 1:
              chip remoto 0 -> Interface-1
              chip remoto 2 -> Interface-1

            Chip 2:
              chip remoto 0 -> Interface-2
              chip remoto 1 -> Interface-2
            """
            remote_chips = [chip for chip in [0, 1, 2] if chip != local_chip]

            ctrl.chipIDList = remote_chips
            ctrl.c2cHopList = [local_chip for _ in remote_chips]
            ctrl.cacheChipIDList = cacheChipIDList

        # HNF / directories
        set_c2c_routes(self.hnf0, 0)
        set_c2c_routes(self.hnf1, 1)
        set_c2c_routes(self.hnf2, 2)

        # C2C interfaces
        set_c2c_routes(self.interface0, 0)
        set_c2c_routes(self.interface1, 1)
        set_c2c_routes(self.interface2, 2)

        # Cache controllers del chip 0
        for cluster in self.core_cluster0:
            set_c2c_routes(cluster.icache, 0)
            set_c2c_routes(cluster.dcache, 0)
            set_c2c_routes(cluster.l2cache, 0)

        # Cache controllers del chip 1
        for cluster in self.core_cluster1:
            set_c2c_routes(cluster.icache, 1)
            set_c2c_routes(cluster.dcache, 1)
            set_c2c_routes(cluster.l2cache, 1)

        # Cache controllers del chip 2
        for cluster in self.core_cluster2:
            set_c2c_routes(cluster.icache, 2)
            set_c2c_routes(cluster.dcache, 2)
            set_c2c_routes(cluster.l2cache, 2)

                # ---------------- NUEVO: DMA controllers ----------------
        #
        # Los DMA controllers también pueden generar tráfico C2C.
        # En el log actual falla:
        #
        #   board.cache_hierarchy.dma_controllers00:
        #   mapChipIDToC2CI missing chipID 2
        #
        # Eso significa que el DMA controller llamó a mapChipIDToC2CI(2),
        # pero no tenía inicializada su tabla chipIDList/c2cHopList.
        #
        # En esta topología, los DMA controllers creados por board.has_dma_ports()
        # están conectados en network0, así que pertenecen al chip 0 y deben usar
        # Interface-0 para llegar a chips remotos 1 y 2.
        # --------------------------------------------------------
        if board.has_dma_ports():
            for dma in self.dma_controllers0:
                set_c2c_routes(dma, 0)
        # ---------------- FIN NUEVO -----------------------------

        # Setting up the MachineID -> ChipID LUT
        # Lists are automatically set up
        # Position in the vector is the version number of the controller
        # cacheChipIDList -> [0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1] ChipID
        # ex: Cache_Controller 0 -> chip 0
        self.hnf0.cacheChipIDList = cacheChipIDList
        self.hnf1.cacheChipIDList = cacheChipIDList
        self.hnf2.cacheChipIDList = cacheChipIDList

        # ---------------- NUEVO ----------------
        # Antes se asignaba cacheChipIDList a las 6 interfaces antiguas.
        # Ahora solo hay una interface C2C por chip.
        # ---------------- FIN NUEVO ----------------
        self.interface0.cacheChipIDList = cacheChipIDList
        self.interface1.cacheChipIDList = cacheChipIDList
        self.interface2.cacheChipIDList = cacheChipIDList

        # ---------------- NUEVO ----------------
        # También pasamos la LUT al interposer.
        #
        # cacheChipIDList:
        #   Permite traducir MachineID de tipo Cache a chipID.
        #
        # interfaceChipIDList:
        #   Permite traducir MachineID de tipo Interface a chipID.
        #
        # Esto es importante para enrutar responses, porque una response no
        # siempre se puede enrutar solo por dirección. Muchas veces conviene
        # mirar campos como:
        #
        #   m_OriginalRequestor
        #   m_Requestor
        #   m_LocalRequestor
        #   m_Responder
        #   m_OriginalResponder
        #
        # y traducir esos MachineID al chip correspondiente.
        # ---------------- FIN NUEVO ----------------
        # ---------------- NUEVO ----------------
        # Pasamos al interposer la tabla que traduce:
        #
        #   Cache_Controller.version -> chipID
        #
        # Esta lista se rellena mientras se crean los controladores de cache.
        # El interposer la usa para enrutar respuestas mirando campos MachineID
        # como m_OriginalRequestor, m_Requestor, m_LocalRequestor, etc.
        # ---------------- FIN NUEVO ----------------
        c2c_interposer.cache_chip_id_list = cacheChipIDList

        # ---------------- NUEVO ----------------
        # Con una Interface C2C por chip:
        #
        #   Interface-0 -> chip 0
        #   Interface-1 -> chip 1
        #   Interface-2 -> chip 2
        #
        # Esta tabla permite al interposer traducir MachineID de tipo Interface
        # a chipID.
        # ---------------- FIN NUEVO ----------------
        c2c_interposer.interface_chip_id_list = [0, 1, 2]

        #####################################################
        
        self.ruby_system.network0.connectControllers(
            list(
                chain.from_iterable(
                    [
                        (cluster.dcache, cluster.icache, cluster.l2cache)
                        for cluster in self.core_cluster0
                    ]
                )
            )
            + self.memory_controllers0
            + [self.hnf0]
            + (self.dma_controllers0 if board.has_dma_ports() else [])

            # ---------------- NUEVO ----------------
            # Antes aquí se conectaban interface00 e interface01.
            # Ahora el chip 0 solo tiene una interface C2C local.
            # ---------------- FIN NUEVO ----------------
            + [self.interface0]
        )

        self.ruby_system.network1.connectControllers(
            list(
                chain.from_iterable(
                    [
                        (cluster.dcache, cluster.icache, cluster.l2cache)
                        for cluster in self.core_cluster1
                    ]
                )
            )
            + self.memory_controllers1
            + [self.hnf1]
            #+ (self.dma_controllers1 if board.has_dma_ports() else [])

            # ---------------- NUEVO ----------------
            # Antes aquí se conectaban interface10 e interface11.
            # Ahora el chip 1 solo tiene una interface C2C local.
            # ---------------- FIN NUEVO ----------------
            + [self.interface1]
        )

        self.ruby_system.network2.connectControllers(
            list(
                chain.from_iterable(
                    [
                        (cluster.dcache, cluster.icache, cluster.l2cache)
                        for cluster in self.core_cluster2
                    ]
                )
            )
            + self.memory_controllers2
            + [self.hnf2]
            #+ (self.dma_controllers1 if board.has_dma_ports() else [])

            # ---------------- NUEVO ----------------
            # Antes aquí se conectaban interface20 e interface21.
            # Ahora el chip 2 solo tiene una interface C2C local.
            # ---------------- FIN NUEVO ----------------
            + [self.interface2]
        )
         
        self.ruby_system.network0.setup_buffers()
        self.ruby_system.network1.setup_buffers()
        self.ruby_system.network2.setup_buffers()

        self.ruby_system.sys_port_proxy = RubyPortProxy()
        board.connect_system_port(self.ruby_system.sys_port_proxy.in_ports)

    def _create_core_cluster(
        self, 
        core: AbstractCore,
        core_num: int,
        board: AbstractBoard,
        network,
        cluster_dests,
        chipID: int,
        cacheChipIDList,
    ) -> SubSystem:
        """Given the core and the core number this function creates a cluster
        for the core with a split I/D cache
        """
        cluster = SubSystem()
        cluster.dcache = PrivateL1MOESICache(
            size=self._l1_size,
            assoc=self._l1_assoc,
            network=network,
            core=core,
            cache_line_size=board.get_cache_line_size(),
            
            target_isa=board.get_processor().get_isa(),
            clk_domain=board.get_clock_domain(),
            chipID=chipID,
            cacheChipIDList=cacheChipIDList,
        )
        cluster.icache = PrivateL1MOESICache(
            size=self._l1_size,
            assoc=self._l1_assoc,
            network=network,
            core=core,
            cache_line_size=board.get_cache_line_size(),
            target_isa=board.get_processor().get_isa(),
            clk_domain=board.get_clock_domain(),
            chipID=chipID,
            cacheChipIDList=cacheChipIDList,
        )

        cluster.l2cache = SharedL2MOESICache(
            size=self._l2_size,
            assoc=self._l2_assoc,
            network=network,
            core=core,
            cache_line_size=board.get_cache_line_size(),
            target_isa=board.get_processor().get_isa(),
            clk_domain=board.get_clock_domain(),
            chipID=chipID,
            cacheChipIDList=cacheChipIDList,
        )

        cluster.icache.sequencer = RubySequencer(
            version=core_num, dcache=NULL, clk_domain=cluster.icache.clk_domain
        )
        cluster.dcache.sequencer = RubySequencer(
            version=core_num,
            dcache=cluster.dcache.cache,
            clk_domain=cluster.dcache.clk_domain,
        )

        if board.has_io_bus():
            cluster.dcache.sequencer.connectIOPorts(board.get_io_bus())

        cluster.dcache.ruby_system = self.ruby_system
        cluster.icache.ruby_system = self.ruby_system
        cluster.l2cache.ruby_system = self.ruby_system

        core.connect_icache(cluster.icache.sequencer.in_ports)
        core.connect_dcache(cluster.dcache.sequencer.in_ports)

        core.connect_walker_ports(
            cluster.dcache.sequencer.in_ports,
            cluster.icache.sequencer.in_ports,
        )

        # Connect the interrupt ports
        if board.get_processor().get_isa() == ISA.X86:
            int_req_port = cluster.dcache.sequencer.interrupt_out_port
            int_resp_port = cluster.dcache.sequencer.in_ports
            core.connect_interrupt(int_req_port, int_resp_port)
        else:
            core.connect_interrupt()

        cluster.dcache.downstream_destinations = cluster.l2cache
        cluster.icache.downstream_destinations = cluster.l2cache
        cluster.l2cache.downstream_destinations = cluster_dests

        return cluster
    
    def _create_memory_controllers(
        self, 
        board: AbstractBoard,
        network,
        rng_idx,
    ) -> List[MemoryController]:
        memory_controllers = []
        for idx, (rng, port) in enumerate(board.get_mem_ports()):
            if idx == rng_idx:
                mc = MemoryController(network, rng, port)
                mc.ruby_system = self.ruby_system
                memory_controllers.append(mc)
        return memory_controllers
    
    def _create_dma_controllers(
        self, 
        board: AbstractBoard,
        network,
        cluster_dest,
        chipID: int,
        cacheChipIDList,
    ) -> List[DMARequestor]:
        dma_controllers = []
        for i, port in enumerate(board.get_dma_ports()):
            ctrl = DMARequestor(
                network,
                board.get_cache_line_size(),
                board.get_clock_domain(),
                chipID=chipID,
                cacheChipIDList=cacheChipIDList,
            )
            version = len(board.get_processor().get_cores()) + i
            ctrl.sequencer = RubySequencer(version=version, in_ports=port)
            ctrl.sequencer.dcache = NULL

            ctrl.ruby_system = self.ruby_system
            ctrl.sequencer.ruby_system = self.ruby_system

            ctrl.downstream_destinations = cluster_dest
            ctrl.chipID = 0 
            dma_controllers.append(ctrl)

        return dma_controllers