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

from m5.objects import NULL, RubySystem, RubySequencer, RubyPortProxy

class C2cCacheHierarchy(AbstractRubyCacheHierarchy):
    """A single level cache based on CHI for x86

    This hierarchy has a split I/D L1 caches per CPU, two directories (HNF),
    and as many memory controllers (SNF) as memory channels. The directories 
    does not have an associated cache.

    The network is a simple point-to-point between all of the controllers.
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
        mem_ranges = []
        # C2c specific list
        # Allows to build the machineID -> ChipID LUT
        cacheChipIDList = []
    
        for rng, port in board.get_mem_ports():
            mem_ranges.append(rng)

        # Two networks
        self.ruby_system.network0 = SimplePt2Pt(self.ruby_system)
        self.ruby_system.network1 = SimplePt2Pt(self.ruby_system)

        # Network configuration
        # virtual networks: 0=requests, 1=snoops, 2=responses, 3=data
        self.ruby_system.number_of_virtual_networks = 4
        self.ruby_system.network0.number_of_virtual_networks = 4
        self.ruby_system.network1.number_of_virtual_networks = 4

        # Chip-0

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
        
        self.hnf0.ruby_system = self.ruby_system
        self.hnf1.ruby_system = self.ruby_system
        
        # Add to the RNF destinations
        cluster0_dest.append(self.hnf0)
        cluster1_dest.append(self.hnf1)

        # Create one Interface per chip
        self.interface0 = Interface(
            self.ruby_system.network0,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[1]],
            chipID=0,
        )
        self.interface1 = Interface(
            self.ruby_system.network1,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[0]],
            chipID=1,
        )
        self.interface0.ruby_system = self.ruby_system
        self.interface1.ruby_system = self.ruby_system

        self.interface0.c2c_out_port = self.interface1.c2c_in_port
        self.interface1.c2c_out_port = self.interface0.c2c_in_port

        # Downstream destinations
        self.interface0.downstream_destinations = self.hnf0
        self.interface1.downstream_destinations = self.hnf1

        # Add to the RNF destinations
        cluster0_dest.append(self.interface0)
        cluster1_dest.append(self.interface1)
        
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
                0,
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
                1,
                board,
                self.ruby_system.network1,
                cluster1_dest,
                chipID=1,
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

        # Create the DMA Controllers, if required.
        if board.has_dma_ports():
            self.dma_controllers0 = self._create_dma_controllers(
                board, 
                network=self.ruby_system.network0,
                cluster_dest=cluster0_dest,
                chipID=0,
                cacheChipIDList=cacheChipIDList,
            )
            self.ruby_system.num_of_sequencers = (
                len(self.core_cluster0) + 
                len(self.core_cluster1)
            ) * 2 + len(self.dma_controllers0)

        else:
            self.ruby_system.num_of_sequencers = (len(self.core_cluster0) + \
                                                len(self.core_cluster1)) * 2

        ############################# C2C SETUP #############

        self.hnf0.c2cHopList = [0]
        self.hnf0.chipIDList = [1]
        self.hnf1.c2cHopList = [1]
        self.hnf1.chipIDList = [0]

        # Setting up the MachineID -> ChipID LUT
        # Lists are automatically set up
        # Position in the vector is the version number of the controller
        # cacheChipIDList -> [0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1] ChipID
        # ex: Cache_Controller 0 -> chip 0
        self.hnf0.cacheChipIDList = cacheChipIDList
        self.hnf1.cacheChipIDList = cacheChipIDList
        self.interface0.cacheChipIDList = cacheChipIDList 
        self.interface1.cacheChipIDList = cacheChipIDList 

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
            + [self.interface1]
        )
         
        self.ruby_system.network0.setup_buffers()
        self.ruby_system.network1.setup_buffers()

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
