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

from m5.objects import NULL, RubySystem, RubySequencer, RubyPortProxy

class C2cCacheHierarchy(AbstractCacheHierarchy):
    