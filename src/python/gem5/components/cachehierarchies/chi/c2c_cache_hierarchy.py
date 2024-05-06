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
from .nodes.dma_requestor import DMARequestor
from .nodes.directory import SimpleDirectory
from .nodes.memory_controller import MemoryController
from .nodes.interface import Interface

from m5.objects import NULL, RubySystem, RubySequencer, RubyPortProxy

class C2cCacheHierarchy(AbstractRubyCacheHierarchy):
    def __init__(self, size: str, assoc: int) -> None:
        super().__init__() 

        self._size = size
        self._assoc = assoc

    @overrides(AbstractCacheHierarchy)
    def incorporate_cache(self, board: AbstractBoard) -> None:
        
        requires(coherence_protocol_required=CoherenceProtocol.CHI)

        self.ruby_system = RubySystem()

        cluster0_dest = []
        cluster1_dest = []

        # Two networks
        self.ruby_system.network0 = SimplePt2Pt(self.ruby_system)
        self.ruby_system.network1 = SimplePt2Pt(self.ruby_system)

        # Network configuration
        # virtual networks: 0=requests, 1=snoops, 2=responses, 3=data
        self.ruby_system.number_of_virtual_networks = 4
        self.ruby_system.network0.number_of_virtual_networks = 4
        self.ruby_system.network1.number_of_virtual_networks = 4

        # Create a single HNF per chip
        self.hnf0 = SimpleDirectory(
            self.ruby_system.network0,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
        )
        self.hnf1 = SimpleDirectory(
            self.ruby_system.network1,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
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
        )
        self.interface1 = Interface(
            self.ruby_system.network1,
            cache_line_size=board.get_cache_line_size(),
            clk_domain=board.get_clock_domain(),
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
                core, 
                i, 
                board,
                self.ruby_system.network0,
                cluster0_dest,
            ) for i, core in enumerate(board.get_processor().get_cores())
        ]
        self.core_cluster1 = [
            self._create_core_cluster(
                core, 
                i, 
                board, 
                self.ruby_system.network1, 
                cluster1_dest,
            ) for i, core in enumerate(board.get_processor().get_cores())
        ]

        # Create the coherent side of the memory controllers
        self.memory_controllers0 = self._create_memory_controllers(board, \
            self.ruby_system.network0)
        self.hnf0.downstream_destinations = self.memory_controllers0

        self.memory_controllers1 = self._create_memory_controllers(board, \
            self.ruby_system.network1)
        self.hnf1.downstream_destinations = self.memory_controllers1

        # We are not supporting DMA controllers now
        if board.has_dma_ports():
            print("We do not support DMA controllers yet!")
            sys.exit()
        
        # Two clusters in total
        self.ruby_system.num_of_sequencers = (len(self.core_cluster0) + \
                                            len(self.core_cluster1)) * 2
        
        self.ruby_system.network0.connectControllers(
            list(
                chain.from_iterable(
                    [
                        (cluster.dcache, cluster.icache)
                        for cluster in self.core_cluster0
                    ]
                )
            )
            + self.memory_controllers0
            + [self.hnf0]
            + (self.dma_controllers if board.has_dma_ports() else [])
        )
        self.ruby_system.network1.connectControllers(
            list(
                chain.from_iterable(
                    [
                        (cluster.dcache, cluster.icache)
                        for cluster in self.core_cluster1
                    ]
                )
            )
            + self.memory_controllers1
            + [self.hnf1]
            + (self.dma_controllers if board.has_dma_ports() else [])
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
        cluster_dests
    ) -> SubSystem:
        """Given the core and the core number this function creates a cluster
        for the core with a split I/D cache
        """
        cluster = SubSystem()
        cluster.dcache = PrivateL1MOESICache(
            size=self._size,
            assoc=self._assoc,
            network=network,
            core=core,
            cache_line_size=board.get_cache_line_size(),
            
            target_isa=board.get_processor().get_isa(),
            clk_domain=board.get_clock_domain(),
        )
        cluster.icache = PrivateL1MOESICache(
            size=self._size,
            assoc=self._assoc,
            network=network,
            core=core,
            cache_line_size=board.get_cache_line_size(),
            target_isa=board.get_processor().get_isa(),
            clk_domain=board.get_clock_domain(),
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

        cluster.dcache.downstream_destinations = cluster_dests
        cluster.icache.downstream_destinations = cluster_dests

        return cluster
    
    def _create_memory_controllers(
        self, 
        board: AbstractBoard,
        network,
    ) -> List[MemoryController]:
        memory_controllers = []
        for rng, port in board.get_mem_ports():
            print("C2cCacheHierarchy create_memory_controllers")
            mc = MemoryController(network, rng, port)
            mc.ruby_system = self.ruby_system
            memory_controllers.append(mc)
        return memory_controllers
    
    def _create_dma_controllers(
        self, board: AbstractBoard
    ) -> List[DMARequestor]:
        print("Need to add support for DMA controllers")
        sys.exit()