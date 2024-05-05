# X86 Board using CHI coherence protocol 
# C2C architecture with two memory regions

from .kernel_disk_workload import KernelDiskWorkload
from ...resources.resource import AbstractResource
from ...utils.override import overrides
from .abstract_system_board import AbstractSystemBoard
from ...isas import ISA

from m5.objects import (
    Pc,
    AddrRange,
    X86FsLinux,
    Addr,
    X86SMBiosBiosInformation,
    X86IntelMPProcessor,
    X86IntelMPIOAPIC,
    X86IntelMPBus,
    X86IntelMPBusHierarchy,
    X86IntelMPIOIntAssignment,
    X86E820Entry,
    Bridge,
    IOXBar,
    IdeDisk,
    CowDiskImage,
    RawDiskImage,
    BaseXBar,
    Port,
)

from m5.util.convert import toMemorySize

from ..processors.abstract_processor import AbstractProcessor
from ..memory.abstract_memory_system import AbstractMemorySystem
from ..cachehierarchies.abstract_cache_hierarchy import AbstractCacheHierarchy

from typing import List, Sequence

class X86C2cBoard(AbstractSystemBoard, KernelDiskWorkload):
    """
    A board capablue of full system simulation for X86.
    
    Used with the CHI coherence protocol.
    Houses two memory regions for two distinct chips.
    """

    def __init__(
        self, 
        clk_freq: str, 
        processor: "AbstractProcessor", 
        memory: "AbstractMemorySystem", 
        cache_hierarchy: "AbstractCacheHierarchy",
        ) -> None:
        super().__init__(
            clk_freq=clk_freq, 
            processor=processor, 
            memory=memory, 
            cache_hierarchy=cache_hierarchy,
        )

        if self.get_processor().get_isa() != ISA.X86:
            raise Exception(
                "The X86C2cBoard requires a processor using X86 "
                f"ISA. Current processor ISA: '{processor.get_isa().name}'."
            )
    
    @overrides(AbstractSystemBoard)
    def _setup_board(self) -> None:
        self.pc = Pc()

        self.workload = X86FsLinux()

        # North Bridge
        self.iobus = IOXBar()

        # Set up all of the I/O.
        self._setup_io_devices()

        self.m5ops_base = 0xFFFF0000
    
    