# C2c architecture restoring from checkpoint and running PARSEC
# Uses X86 and CHI
import m5
import argparse
import time

from gem5.utils.requires import requires
from gem5.components.boards.x86_c2cv2_board import X86C2cBoard
from gem5.components.memory.multi_channel import DualChannelDDR3_1600_C2C
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.components.cachehierarchies.chi.c2cv2_cache_hierarchy import (
    C2cCacheHierarchy,
)
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.coherence_protocol import CoherenceProtocol
from gem5.resources.workload import (
    Workload,
    CustomWorkload,
)
from gem5.resources.resource import Resource, CustomDiskImageResource
from m5.objects import Root

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
    description="Restore from checkpoint and run PARSEC on the C2C X86/CHI system."
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

parser.add_argument(
    "--checkpoint",
    type=str,
    required=True,
    help="Path to the checkpoint directory to restore from.",
)

args = parser.parse_args()

# Here we setup a MESI Two Level Cache Hierarchy.
cache_hierarchy = C2cCacheHierarchy(
    l1_size="64kB",
    l1_assoc=4,
    l2_size="1MB",
    l2_assoc=8,
)

# System memory
memory = DualChannelDDR3_1600_C2C(size="3GB", range_size="1610612736")

# Switchable noncaching -> timing
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.NONCACHING_SIMPLE,
    #starting_core_type=CPUTypes.KVM,
    switch_core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=3,
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
    "cd /home/gem5/parsec-benchmark;"
    + "source env.sh;"
    + "parsecmgmt -a run -p {} -c gcc-hooks -i {} \
        -n {};".format(
            args.benchmark, args.size, "2"
    )
    + "sleep 5;"
    + "m5 exit;"
)

#workload = Workload("x86-ubuntu-18.04-boot")
#workload.set_parameter("readfile_contents", command)
#board.set_workload(workload)

# Custom disk image setup
board.set_kernel_disk_workload(
    kernel=Resource("x86-linux-kernel-5.4.49"),
    #disk_image = CustomDiskImageResource(
    #    "/home/lbertranalvarez/Work/disk-image/images/x86-ubuntu-18.04-img"
    #),
    disk_image=Resource("x86-parsec"),
    readfile_contents=command,
)

# Create root object manually because we restore via m5.instantiate(checkpoint)
root = Root(full_system=True, system=board)

# Wall clock time
globalStart = time.time()

print("Running the simulation")
print("Restoring from checkpoint:", args.checkpoint)
print("Using NONCACHING_SIMPLE cpu for restore")
print("Benchmark:", args.benchmark)
print("Size:", args.size)

# Reset stats before restore/run
m5.stats.reset()

# Instantiate from checkpoint
m5.instantiate(args.checkpoint)

# First simulate call:
# - If the guest workload issues m5_work_begin(), we switch to timing there.
# - If not, we still print the exit cause so you can see what happened.
exit_event = m5.simulate()

if exit_event.getCause() == "workbegin":
    print("Restored checkpoint and reached the start of the ROI!")
    print("Resetting stats at the start of the ROI!")
    m5.stats.reset()
    processor.switch()

    # Simulate the ROI
    exit_event = m5.simulate()

    if exit_event.getCause() == "workend":
        print("Dump stats at the end of the ROI!")
        m5.stats.dump()
    else:
        print("Unexpected termination during ROI!")
        print("Exit cause:", exit_event.getCause())
        m5.stats.dump()

    # Finish benchmark cleanup until m5 exit
    exit_event = m5.simulate()
    print("Final exit cause:", exit_event.getCause())

else:
    print("Unexpected termination before ROI!")
    print("Exit cause:", exit_event.getCause())
    m5.stats.dump()

print("All simulation events were successful.")

# Simulation statistics
print("Done with the simulation")
print()
print("Performance statistics:")

# If ROI was reached, get_roi_ticks() is not available here because we are not
# using the Simulator wrapper, so use the dumped stats.txt afterwards.
print(
    "Ran a total of", m5.curTick() / 1e12, "simulated seconds"
)
print(
    "Total wallclock time: %.2fs %.2f min"
    % (time.time() - globalStart, (time.time() - globalStart) / 60)
)# C2c architecture restoring from checkpoint and running PARSEC
# Uses X86 and CHI
import m5
import argparse
import time

from gem5.utils.requires import requires
from gem5.components.boards.x86_c2cv2_board import X86C2cBoard
from gem5.components.memory.multi_channel import DualChannelDDR3_1600_C2C
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.components.cachehierarchies.chi.c2cv2_cache_hierarchy import (
    C2cCacheHierarchy,
)
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.coherence_protocol import CoherenceProtocol
from gem5.resources.workload import (
    Workload,
    CustomWorkload,
)
from gem5.resources.resource import Resource, CustomDiskImageResource
from m5.objects import Root

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
    description="Restore from checkpoint and run PARSEC on the C2C X86/CHI system."
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

parser.add_argument(
    "--checkpoint",
    type=str,
    required=True,
    help="Path to the checkpoint directory to restore from.",
)

args = parser.parse_args()

# Here we setup a MESI Two Level Cache Hierarchy.
cache_hierarchy = C2cCacheHierarchy(
    l1_size="64kB",
    l1_assoc=4,
    l2_size="1MB",
    l2_assoc=8,
)

# System memory
memory = DualChannelDDR3_1600_C2C(size="3GB", range_size="1610612736")

# Switchable noncaching -> timing
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.NONCACHING_SIMPLE,
    #starting_core_type=CPUTypes.KVM,
    switch_core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=3,
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
    "cd /home/gem5/parsec-benchmark;"
    + "source env.sh;"
    + "parsecmgmt -a run -p {} -c gcc-hooks -i {} \
        -n {};".format(
            args.benchmark, args.size, "2"
    )
    + "sleep 5;"
    + "m5 exit;"
)

#workload = Workload("x86-ubuntu-18.04-boot")
#workload.set_parameter("readfile_contents", command)
#board.set_workload(workload)

# Custom disk image setup
board.set_kernel_disk_workload(
    kernel=Resource("x86-linux-kernel-5.4.49"),
    #disk_image = CustomDiskImageResource(
    #    "/home/lbertranalvarez/Work/disk-image/images/x86-ubuntu-18.04-img"
    #),
    disk_image=Resource("x86-parsec"),
    readfile_contents=command,
)

# Create root object manually because we restore via m5.instantiate(checkpoint)
root = Root(full_system=True, system=board)

# Wall clock time
globalStart = time.time()

print("Running the simulation")
print("Restoring from checkpoint:", args.checkpoint)
print("Using NONCACHING_SIMPLE cpu for restore")
print("Benchmark:", args.benchmark)
print("Size:", args.size)

# Reset stats before restore/run
m5.stats.reset()

# Instantiate from checkpoint
m5.instantiate(args.checkpoint)

# First simulate call:
# - If the guest workload issues m5_work_begin(), we switch to timing there.
# - If not, we still print the exit cause so you can see what happened.
exit_event = m5.simulate()

if exit_event.getCause() == "workbegin":
    print("Restored checkpoint and reached the start of the ROI!")
    print("Resetting stats at the start of the ROI!")
    m5.stats.reset()
    processor.switch()

    # Simulate the ROI
    exit_event = m5.simulate()

    if exit_event.getCause() == "workend":
        print("Dump stats at the end of the ROI!")
        m5.stats.dump()
    else:
        print("Unexpected termination during ROI!")
        print("Exit cause:", exit_event.getCause())
        m5.stats.dump()

    # Finish benchmark cleanup until m5 exit
    exit_event = m5.simulate()
    print("Final exit cause:", exit_event.getCause())

else:
    print("Unexpected termination before ROI!")
    print("Exit cause:", exit_event.getCause())
    m5.stats.dump()

print("All simulation events were successful.")

# Simulation statistics
print("Done with the simulation")
print()
print("Performance statistics:")

# If ROI was reached, get_roi_ticks() is not available here because we are not
# using the Simulator wrapper, so use the dumped stats.txt afterwards.
print(
    "Ran a total of", m5.curTick() / 1e12, "simulated seconds"
)
print(
    "Total wallclock time: %.2fs %.2f min"
    % (time.time() - globalStart, (time.time() - globalStart) / 60)
)