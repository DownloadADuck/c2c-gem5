from gem5.components.processors.abstract_core import AbstractCore
from gem5.isas import ISA
from python.m5.objects import RubyNetwork

from .abstract_node import AbstractNode

from m5.objects import ClockDomain, RubyCache, RubyNetwork

class SharedL2MOESICache(AbstractNode):
    def __init__(
        self,
        size: str,
        assoc: int,
        network: RubyNetwork, 
        core: AbstractCore,
        cache_line_size,
        target_isa: ISA,
        clk_domain: ClockDomain,
    ):
        super().__init__(network, cache_line_size)

        self.cache = RubyCache(
            size=size, assoc=assoc, start_index_bit=self.getBlockSizeBits()
        )

        self.sequencer = NULL

        self.clk_domain = clk_domain
        self.send_evictions = core.requires_send_evicts()
        self.use_prefetcher = False
        
        # Only applies to home nodes
        self.is_HN = False
        self.enable_DMT = False
        self.enable_DCT = False
        
        # MOESI states fro a 2 level cache
        self.allow_SD = True
        self.alloc_on_seq_acc = False
        self.alloc_on_seq_line_write = False
        self.alloc_on_readshared = True
        self.alloc_on_readunique = True
        self.alloc_on_readonce = True
        self.alloc_on_writeback = True  # Should never happen in an L1
        self.dealloc_on_unique = False
        self.dealloc_on_shared = False
        self.dealloc_backinv_unique = True
        self.dealloc_backinv_shared = True
        # Some reasonable default TBE params
        self.number_of_TBEs = 32
        self.number_of_repl_TBEs = 32
        self.number_of_snoop_TBEs = 16
        self.number_of_DVM_TBEs = 1 # should not receive any dvm
        self.number_of_DVM_snoop_TBEs = # should not receive any dvm
        self.unify_repl_TBEs = False