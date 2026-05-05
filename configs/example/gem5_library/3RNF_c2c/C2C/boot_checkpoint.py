import m5
import argparse
import time

from gem5.utils.requires import requires
from gem5.components.boards.x86_c2cv2_board import X86C2cBoard
from gem5.components.memory.multi_channel import DualChannelDDR3_1600_C2C
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.cachehierarchies.chi.c2cv2_cache_hierarchy import (
    C2cCacheHierarchy,
)
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.coherence_protocol import CoherenceProtocol
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent
from gem5.resources.resource import Resource

requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.CHI,
)

parser = argparse.ArgumentParser()
parser.add_argument("--checkpoint-dir", type=str, required=True)
args = parser.parse_args()

cache_hierarchy = C2cCacheHierarchy(
    l1_size="64kB",
    l1_assoc=4,
    l2_size="1MB",
    l2_assoc=8,
)

memory = DualChannelDDR3_1600_C2C(size="3GB", range_size="1610612736")

# Boot estable, sin KVM
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.NONCACHING_SIMPLE,
    switch_core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=3,
)

board = X86C2cBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# En vez de PARSEC, solo boot + checkpoint
command = (
    "echo '[guest] booted';"
    f"m5 checkpoint {args.checkpoint_dir};"
    "sleep 2;"
    "m5 exit;"
)

board.set_kernel_disk_workload(
    kernel=Resource("x86-linux-kernel-5.4.49"),
    disk_image=Resource("x86-parsec"),
    readfile_contents=command,
)

simulator = Simulator(board=board)

globalStart = time.time()

print("Running boot-to-checkpoint simulation")
simulator.run()

print("Checkpoint creation finished")
print(
    "Total wallclock time: %.2fs %.2f min"
    % (time.time() - globalStart, (time.time() - globalStart) / 60)
)