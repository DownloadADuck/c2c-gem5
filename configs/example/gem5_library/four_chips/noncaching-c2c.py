# C2c architecture booting and exiting ubuntu with KVM enabled CPUs
# Uses X86 and CHI
import m5
import argparse
import time 

from gem5.utils.requires import requires
from gem5.components.boards.x86_3C_board import X863CBoard
from gem5.components.memory.multi_channel import DualChannelDDR3_1600_4C
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.components.cachehierarchies.chi.fourc_cache_hierarchy import (
    FourCCacheHierarchy,
)
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.coherence_protocol import CoherenceProtocol
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent
from gem5.resources.workload import (
    Workload,
    CustomWorkload,
)
from gem5.resources.resource import Resource, CustomDiskImageResource

# This runs a check to ensure the gem5 binary is compiled to X86 and to the
# CHI coherence protocol.
requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.CHI,
    kvm_required=False,
)

# Parsec benchmarks
benchmark_choices = [
    "blackscholes",
    "bodytrack",
    "canneal",
    "dedup",
    "facesim",
    "ferret",
    "fluidanimate",
    "freqmine",
    "raytrace",
    "streamcluster",
    "swaptions",
    "vips",
    "x264",
]

# Following are the input size.
size_choices = ["test", "simsmall", "simmedium", "simlarge"]

parser = argparse.ArgumentParser(
    description="An example configuration script to run the npb benchmarks."
)

# The arguments accepted are the benchmark name and the simulation size.
parser.add_argument(
    "--benchmark",
    type=str,
    required=True,
    help="Input the benchmark program to execute.",
    choices=benchmark_choices,
)

parser.add_argument(
    "--size",
    type=str,
    required=True,
    help="Simulation size the benchmark program.",
    choices=size_choices,
)
args = parser.parse_args()

# Here we setup a MESI Two Level Cache Hierarchy.
cache_hierarchy = FourCCacheHierarchy(
    l1_size="64kB",
    l1_assoc=4,
    l2_size="1MB",
    l2_assoc=8,
)

# System memory
# 4 DRAMS of 768MB that form a non-interleaved 3GB address range
memory = DualChannelDDR3_1600_4C(size="3GB", range_size="805306368")

# Switchable KVM -> timing
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.NONCACHING_SIMPLE,
    switch_core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=8,
)

# Board setup
board = X863CBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Full System workload setup
# The X86Board takes a kernel, a disk image and an optional command to run
command = (
    "cd /home/gem5/parsec-benchmark;".format(args.benchmark)
    + "source env.sh;"
    + "parsecmgmt -a run -p {} -c gcc-hooks -i {} \
        -n {};".format(
            args.benchmark, args.size, "8"
    )
    + "sleep 5;"
    + "m5 exit;"
)

#workload = Workload("x86-ubuntu-18.04-boot")
#workload.set_parameter("readfile_contents", command)
#board.set_workload(workload)

# Custom disk image setup 
board.set_kernel_disk_workload(
    kernel = Resource("x86-linux-kernel-5.4.49"),
    disk_image = Resource("x86-parsec"),
    readfile_contents=command,
)

# Custom exit events
def handle_workbegin():
    print("Done booting Linux")
    print("Resetting stats at the start of the ROI!")
    m5.stats.reset()
    processor.switch()
    yield False

def handle_workend():
    print("Dump stats at the end of the ROI!")
    m5.stats.dump()
    yield True

# Regular sim
simulator = Simulator(
    board=board,
    #on_exit_event={
    #    # Overriding the default behavior for the first m5 exit event. instead
    #    # of exiting the simulator we want to switch processor. 
    #    ExitEvent.EXIT: (func() for func in [processor.switch])
    #}
    on_exit_event={
        ExitEvent.WORKBEGIN: handle_workbegin(),
        ExitEvent.WORKEND: handle_workend(),
    },
)

# Wall clock time
globalStart = time.time()

print("Running the simulation")
print("Using KVM cpu")

m5.stats.reset()
simulator.run()

print("All simulation events were successful.")

# Simulation statistics
print("Done with the simulation")
print()
print("Performance statistics:")

print("Simulated time in ROI: " + ((str(simulator.get_roi_ticks()[0]))))
print(
    "Ran a total of", simulator.get_current_tick() / 1e12, "simulated seconds"
)
print(
    "Total wallclock time: %.2fs %.2f min"
    % (time.time() - globalStart, (time.time() - globalStart) / 60)
)
