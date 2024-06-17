from gem5.utils.requires import requires
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.memory.multi_channel import (
    DualChannelDDR3_1600,
    DualChannelDDR3_1600_C2C,
)
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.coherence_protocol import CoherenceProtocol
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent
from gem5.resources.workload import Workload

requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
    kvm_required=True,
)

from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)

# Cache hierarchy
cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="16kB",
    l1d_assoc=8,
    l1i_size="16kB",
    l1i_assoc=8,
    l2_size="256kB",
    l2_assoc=16,
    num_l2_banks=1,
)

# Memory
#memory = SingleChannelDDR3_1600(size="3GB")
#memory = DualChannelDDR3_1600(size="3GB")
#memory = DualChannelDDR3_1600_C2C(size="3GB", range_size="1500MB")
memory = DualChannelDDR3_1600_C2C(size="3GB", range_size="1610612736")

# CPU
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.KVM,
    #starting_core_type=CPUTypes.TIMING,
    switch_core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=2,
)

# Board
board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Workload command
command = (
    "m5 exit;"
    + "echo 'This is running on Timing CPU cores.';"
    + "sleep 1;"
    + "m5 exit;"
)

workload = Workload("x86-ubuntu-18.04-boot")
workload.set_parameter("readfile_contents", command)
board.set_workload(workload)

max_ticks = 23000000000000

def exit_switch_cpu_event():
    processor.switch()
    yield False
    while True:
        yield False

simulator = Simulator(
    board=board,
    on_exit_event={
        # Here we want override the default behavior for the first m5 exit
        # exit event. Instead of exiting the simulator, we just want to
        # switch the processor. The 2nd m5 exit after will revert to using
        # default behavior where the simulator run will exit.
        ExitEvent.EXIT: (func() for func in [processor.switch])
    },
    #on_exit_event={
    #    ExitEvent.MAX_TICK : exit_switch_cpu_event(),
    #},
)
#simulator.run(max_ticks=max_ticks)
simulator.run()
