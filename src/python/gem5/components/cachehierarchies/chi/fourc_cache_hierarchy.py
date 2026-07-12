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

class FourCCacheHierarchy(AbstractRubyCacheHierarchy):
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
        cluster3_dest = []
        mem_ranges = []
        # C2c specific list
        # Allows to build the machineID -> ChipID LUT
        cacheChipIDList = []
    
        for rng, port in board.get_mem_ports():
            mem_ranges.append(rng)

        # Two networks
        self.ruby_system.network0 = SimplePt2Pt(self.ruby_system)
        self.ruby_system.network1 = SimplePt2Pt(self.ruby_system)
        self.ruby_system.network2 = SimplePt2Pt(self.ruby_system)
        self.ruby_system.network3 = SimplePt2Pt(self.ruby_system)

        # Network configuration
        # virtual networks: 0=requests, 1=snoops, 2=responses, 3=data
        self.ruby_system.number_of_virtual_networks = 4
        self.ruby_system.network0.number_of_virtual_networks = 4
        self.ruby_system.network1.number_of_virtual_networks = 4
        self.ruby_system.network2.number_of_virtual_networks = 4
        self.ruby_system.network3.number_of_virtual_networks = 4

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
        self.hnf3 = SimpleDirectory(
            self.ruby_system.network3,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[3]],
            chipID=3,
            cacheChipIDList=cacheChipIDList,
        )
        
        self.hnf0.ruby_system = self.ruby_system
        self.hnf1.ruby_system = self.ruby_system
        self.hnf2.ruby_system = self.ruby_system
        self.hnf3.ruby_system = self.ruby_system
        
        # Create one Interface per hop
        # Chip-0
        self.interface00 = Interface(
            self.ruby_system.network0,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[1]], # to reach chip-1 
            chipID=0,
        )
        self.interface01 = Interface(
            self.ruby_system.network0,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[2]], # to reach chip-2
            chipID=0,
        )
        self.interface02 = Interface(
            self.ruby_system.network0,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[3]], # to reach chip-3
            chipID=0,
        )

        # Chip-1
        self.interface10 = Interface(
            self.ruby_system.network1,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[0]], # to reach chip-0
            chipID=1,
        )
        self.interface11 = Interface(
            self.ruby_system.network1,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[2]], # to reach chip-2
            chipID=1,
        )
        self.interface12 = Interface(
            self.ruby_system.network1,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[3]], # to reach chip-3
            chipID=1,
        )

        # Chip-2
        self.interface20 = Interface(
            self.ruby_system.network2,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[0]], # to reach chip-0
            chipID=2,
        )
        self.interface21 = Interface(
            self.ruby_system.network2,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[1]], # to reach chip-1
            chipID=2,
        )
        self.interface22 = Interface(
            self.ruby_system.network2,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[3]], # to reach chip-3
            chipID=2,
        )


        # Chip-3
        self.interface30 = Interface(
            self.ruby_system.network3,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[0]], # to reach chip-0
            chipID=3,
        )
        self.interface31 = Interface(
            self.ruby_system.network3,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[1]], # to reach chip-1
            chipID=3,
        )
        self.interface32 = Interface(
            self.ruby_system.network3,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
            ranges=[mem_ranges[2]], # to reach chip-2
            chipID=3,
        )

        self.interface00.ruby_system = self.ruby_system #0
        self.interface01.ruby_system = self.ruby_system #1
        self.interface02.ruby_system = self.ruby_system #2

        self.interface10.ruby_system = self.ruby_system #3
        self.interface11.ruby_system = self.ruby_system #4
        self.interface12.ruby_system = self.ruby_system #5
        
        self.interface20.ruby_system = self.ruby_system #6
        self.interface21.ruby_system = self.ruby_system #7
        self.interface22.ruby_system = self.ruby_system #8
        
        self.interface30.ruby_system = self.ruby_system #9
        self.interface31.ruby_system = self.ruby_system #10
        self.interface32.ruby_system = self.ruby_system #11

        # C2CI connections
        self.interface00.c2c_out_port = self.interface10.c2c_in_port #C0 -> C1
        self.interface01.c2c_out_port = self.interface20.c2c_in_port #C0 -> C2
        self.interface02.c2c_out_port = self.interface30.c2c_in_port #C0 -> C3

        self.interface10.c2c_out_port = self.interface00.c2c_in_port #C1 -> C0
        self.interface11.c2c_out_port = self.interface21.c2c_in_port #C1 -> C2
        self.interface12.c2c_out_port = self.interface31.c2c_in_port #C1 -> C3

        self.interface20.c2c_out_port = self.interface01.c2c_in_port #C2 -> C0
        self.interface21.c2c_out_port = self.interface11.c2c_in_port #C2 -> C1
        self.interface22.c2c_out_port = self.interface32.c2c_in_port #C2 -> C3

        self.interface30.c2c_out_port = self.interface02.c2c_in_port #C3 -> C0
        self.interface31.c2c_out_port = self.interface12.c2c_in_port #C3 -> C1
        self.interface32.c2c_out_port = self.interface22.c2c_in_port #C3 -> C2

        # Downstream destinations
        self.interface00.downstream_destinations = self.hnf0
        self.interface01.downstream_destinations = self.hnf0
        self.interface02.downstream_destinations = self.hnf0

        self.interface10.downstream_destinations = self.hnf1
        self.interface11.downstream_destinations = self.hnf1
        self.interface12.downstream_destinations = self.hnf1

        self.interface20.downstream_destinations = self.hnf2
        self.interface21.downstream_destinations = self.hnf2
        self.interface22.downstream_destinations = self.hnf2

        self.interface30.downstream_destinations = self.hnf3
        self.interface31.downstream_destinations = self.hnf3
        self.interface32.downstream_destinations = self.hnf3

        # Add to the RNF destinations
        ## C2CIs
        cluster0_dest.append(self.interface00)
        cluster0_dest.append(self.interface01)
        cluster0_dest.append(self.interface02)

        cluster1_dest.append(self.interface10)
        cluster1_dest.append(self.interface11)
        cluster1_dest.append(self.interface12)

        cluster2_dest.append(self.interface20)
        cluster2_dest.append(self.interface21)
        cluster2_dest.append(self.interface22)

        cluster3_dest.append(self.interface30)
        cluster3_dest.append(self.interface31)
        cluster3_dest.append(self.interface32)
        ## HNFs
        cluster0_dest.append(self.hnf0)
        cluster1_dest.append(self.hnf1)
        cluster2_dest.append(self.hnf2)
        cluster3_dest.append(self.hnf3)

        
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
            ),
            self._create_core_cluster(
                (board.get_processor().get_cores())[3],
                1,
                board,
                self.ruby_system.network1,
                cluster1_dest,
                chipID=1,
                cacheChipIDList=cacheChipIDList,
            )
        ]
        self.core_cluster2 = [
            self._create_core_cluster(
                (board.get_processor().get_cores())[4],
                2,
                board,
                self.ruby_system.network2,
                cluster2_dest,
                chipID=2,
                cacheChipIDList=cacheChipIDList,
            ),
            self._create_core_cluster(
                (board.get_processor().get_cores())[5],
                2,
                board,
                self.ruby_system.network2,
                cluster2_dest,
                chipID=2,
                cacheChipIDList=cacheChipIDList,
            )
        ]
        self.core_cluster3 = [
            self._create_core_cluster(
                (board.get_processor().get_cores())[6],
                3,
                board,
                self.ruby_system.network3,
                cluster3_dest,
                chipID=3,
                cacheChipIDList=cacheChipIDList,
            ),
            self._create_core_cluster(
                (board.get_processor().get_cores())[7],
                3,
                board,
                self.ruby_system.network3,
                cluster3_dest,
                chipID=3,
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

        self.memory_controllers3 = self._create_memory_controllers(
                board,
                self.ruby_system.network3, 
                rng_idx=3, 
            )
        self.hnf3.downstream_destinations = self.memory_controllers3

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
                len(self.core_cluster1) +
                len(self.core_cluster2) +
                len(self.core_cluster3) 
            ) * 2 + len(self.dma_controllers0)

        else:
            self.ruby_system.num_of_sequencers = (len(self.core_cluster0) + \
                                                  len(self.core_cluster1) + \
                                                  len(self.core_cluster2) + \
                                                  len(self.core_cluster3)) * 2

        ############################# C2C SETUP #############

        self.hnf0.c2cHopList = [0,1,2] # --> C2CI ID
        self.hnf0.chipIDList = [1,2,3] # Chip that they service 
        self.hnf1.c2cHopList = [3,4,5]
        self.hnf1.chipIDList = [0,2,3]
        self.hnf2.c2cHopList = [6,7,8]
        self.hnf2.chipIDList = [0,1,3]
        self.hnf3.c2cHopList = [9,10,11]
        self.hnf3.chipIDList = [0,1,2]

        self.core_cluster0[0].l2cache.c2cHopList = [0,1,2]
        self.core_cluster0[0].l2cache.chipIDList = [1,2,3]
        self.core_cluster0[1].l2cache.c2cHopList = [0,1,2]
        self.core_cluster0[1].l2cache.chipIDList = [1,2,3]

        self.core_cluster1[0].l2cache.c2cHopList = [3,4,5]
        self.core_cluster1[0].l2cache.chipIDList = [0,2,3]
        self.core_cluster1[1].l2cache.c2cHopList = [3,4,5]
        self.core_cluster1[1].l2cache.chipIDList = [0,2,3]

        self.core_cluster2[0].l2cache.c2cHopList = [6,7,8]
        self.core_cluster2[0].l2cache.chipIDList = [0,1,3]
        self.core_cluster2[1].l2cache.c2cHopList = [6,7,8]
        self.core_cluster2[1].l2cache.chipIDList = [0,1,3]

        self.core_cluster3[0].l2cache.c2cHopList = [9,10,11]
        self.core_cluster3[0].l2cache.chipIDList = [0,1,2]
        self.core_cluster3[1].l2cache.c2cHopList = [9,10,11]
        self.core_cluster3[1].l2cache.chipIDList = [0,1,2]

        # Setting up the MachineID -> ChipID LUT
        # Lists are automatically set up
        # Position in the vector is the version number of the controller
        # cacheChipIDList -> [0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1] ChipID
        # ex: Cache_Controller 0 -> chip 0
        self.hnf0.cacheChipIDList = cacheChipIDList
        self.hnf1.cacheChipIDList = cacheChipIDList
        self.hnf2.cacheChipIDList = cacheChipIDList
        self.hnf3.cacheChipIDList = cacheChipIDList

        self.interface00.cacheChipIDList = cacheChipIDList 
        self.interface01.cacheChipIDList = cacheChipIDList 
        self.interface02.cacheChipIDList = cacheChipIDList 
        self.interface10.cacheChipIDList = cacheChipIDList 
        self.interface11.cacheChipIDList = cacheChipIDList 
        self.interface12.cacheChipIDList = cacheChipIDList 
        self.interface20.cacheChipIDList = cacheChipIDList 
        self.interface21.cacheChipIDList = cacheChipIDList 
        self.interface22.cacheChipIDList = cacheChipIDList 
        self.interface30.cacheChipIDList = cacheChipIDList 
        self.interface31.cacheChipIDList = cacheChipIDList 
        self.interface32.cacheChipIDList = cacheChipIDList 

        self.core_cluster0[0].l2cache.cacheChipIDList = cacheChipIDList
        self.core_cluster0[1].l2cache.cacheChipIDList = cacheChipIDList
        self.core_cluster1[0].l2cache.cacheChipIDList = cacheChipIDList
        self.core_cluster1[1].l2cache.cacheChipIDList = cacheChipIDList
        self.core_cluster2[0].l2cache.cacheChipIDList = cacheChipIDList
        self.core_cluster2[1].l2cache.cacheChipIDList = cacheChipIDList
        self.core_cluster3[0].l2cache.cacheChipIDList = cacheChipIDList
        self.core_cluster3[1].l2cache.cacheChipIDList = cacheChipIDList

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
            + [self.interface00]
            + [self.interface01]
            + [self.interface02]
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
            + [self.interface10]
            + [self.interface11]
            + [self.interface12]
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
            + [self.interface20]
            + [self.interface21]
            + [self.interface22]
        )
        self.ruby_system.network3.connectControllers(
            list(
                chain.from_iterable(
                    [
                        (cluster.dcache, cluster.icache, cluster.l2cache)
                        for cluster in self.core_cluster3
                    ]
                )
            )
            + self.memory_controllers3
            + [self.hnf3]
            + [self.interface30]
            + [self.interface31]
            + [self.interface32]
        )
         
        self.ruby_system.network0.setup_buffers()
        self.ruby_system.network1.setup_buffers()
        self.ruby_system.network2.setup_buffers()
        self.ruby_system.network3.setup_buffers()

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
