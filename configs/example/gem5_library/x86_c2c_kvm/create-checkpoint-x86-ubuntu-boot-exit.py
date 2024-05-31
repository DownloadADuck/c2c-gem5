# C2c architecture booting and exiting ubuntu with KVM enabled CPUs
# Uses X86 and CHI
from gem5.utils.requires import requires
from gem5.components.boards.x86_c2c_board import X86C2cBoard
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.memory.multi_channel import (
    DualChannelDDR3_1600,
    DualChannelDDR3_1600_C2C,
)
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
# Using a non-switch processor to generate the checkpoints
from gem5.components.processors.simple_processor import SimpleProcessor

from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.coherence_protocol import CoherenceProtocol
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.exit_event_generators import (
    save_checkpoint_generator,
    warn_default_decorator,
)
from gem5.resources.workload import Workload

# This runs a check to ensure the gem5 binary is compiled to X86 and to the
# CHI coherence protocol.
requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.CHI,
    kvm_required=True,
)

from gem5.components.cachehierarchies.chi.private_l1_cache_hierarchy import (
    PrivateL1CacheHierarchy,
)
from gem5.components.cachehierarchies.chi.c2c_cache_hierarchy import (
    C2cCacheHierarchy,
)

# Here we setup a MESI Two Level Cache Hierarchy.
cache_hierarchy = C2cCacheHierarchy(
    l1_size="32kB",
    l1_assoc=8,
    l2_size="64kB",
    l2_assoc=8,
)

# System memory
memory = DualChannelDDR3_1600_C2C(size="2GB", range_size="1GB")

# Switchable KVM -> timing
#processor = SimpleSwitchableProcessor(
#    starting_core_type=CPUTypes.KVM,
#    switch_core_type=CPUTypes.TIMING,
#    isa=ISA.X86,
#    num_cores=1,
#)
#processor = SimpleSwitchableProcessor(
#    starting_core_type=CPUTypes.TIMING,
#    switch_core_type=CPUTypes.TIMING,
#    isa=ISA.X86,
#    num_cores=2,
#)
processor = SimpleProcessor(
    #cpu_type=CPUTypes.NONCACHING_SIMPLE,
    cpu_type=CPUTypes.KVM,
    isa=ISA.X86,
    num_cores=2,
)

# Board setup
board = X86C2cBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Full System workload setup
# The X86Board takes a kernel, a disk image and an optional command to run
command = (
    "m5 exit;"
    + "echo 'This is running on Timing CPU cores.';"
    + "sleep 1;"
    + "m5 exit;"
)

workload = Workload("x86-ubuntu-18.04-boot")
workload.set_parameter("readfile_contents", command)
board.set_workload(workload)

# Regular sim
#simulator = Simulator(
#    board=board,
#    on_exit_event={
#        # Overriding the default behavior for the first m5 exit event. instead
#        # of exiting the simulator we want to switch processor. 
#        ExitEvent.EXIT: (func() for func in [processor.switch])
#    }
#)
#simulator.run()

# Ckeckpointing setup
max_ticks = 865950000000
checkpoint_path = "/home/lbertranalvarez/Work/gem5/checkpoints/"
simulator = Simulator(
    board=board,
    #on_exit_event={
    #    #ExitEvent.CHECKPOINT: (func() for func in [processor.switch])
    #    ExitEvent.CHECKPOINT: warn_default_decorator(
    #        save_checkpoint_generator,
    #        "checkpoint",
    #        "creating a checkpoint and continuing",
    #    )(),
    #}
)
simulator.run(max_ticks=max_ticks)

print(
    "Exiting @ tick {} because {}.".format(
        simulator.get_current_tick(), simulator.get_last_exit_event_cause()
    )
)

print("Checkpointing at", checkpoint_path)
simulator.save_checkpoint(checkpoint_path)
print("Checkpointing done")
