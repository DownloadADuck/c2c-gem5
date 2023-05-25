import m5
from m5.util import *
import os

# import all of the SimObjects
from m5.objects import *

# Needed for running C++ threads
m5.util.addToPath("../")
from common.FileSystemConfig import config_filesystem

# You can import ruby_caches_MI_example to use the MI_example protocol instead
# of the MSI protocol
from msi_caches import MyCacheSystem

# create the system we are going to simulate
system = System()

# Set the clock frequency of the system (and all of its children)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the system
system.mem_mode = "timing"  # Use timing accesses
arv = convert.toMemorySize('256MB')
addr_ranges_vaults = [AddrRange(i*arv, ((i+1)*arv-1)) for i in range(2)]
system.mem_ranges = addr_ranges_vaults  # Create an address range

# Create a pair of simple CPUs
system.cpu0 = [ArmSimpleCPU() for i in range(1)]
system.cpu1 = [ArmSimpleCPU() for i in range(1)]

# Create a DDR3 memory controller and connect it to the membus
system.mem_ctrl0 = MemCtrl()
system.mem_ctrl0.dram = DDR3_1600_8x8()
system.mem_ctrl0.dram.range = system.mem_ranges[0]

system.mem_ctrl1 = MemCtrl()
system.mem_ctrl1.dram = DDR3_1600_8x8()
system.mem_ctrl1.dram.range = system.mem_ranges[1]

# create the interrupt controller for the CPU and connect to the membus
for cpu in system.cpu0:
    cpu.createInterruptController()
for cpu in system.cpu1:
    cpu.createInterruptController()

# Create the Ruby System
system.caches = MyCacheSystem()
system.caches.setup(system, system.cpu0, system.cpu1, system.mem_ctrl0,
                    system.mem_ctrl1)

# Run application and use the compiled ISA to find the binary
# grab the specific path to the binary
thispath = os.path.dirname(os.path.realpath(__file__))
binary0 = os.path.join(thispath, "../../", "tests/test-progs/micro-bench/vector_add_default_region_1")
binary1 = os.path.join(thispath, "../../", "tests/test-progs/micro-bench/vector_add_default_region_2")

# Create a process for a simple "multi-threaded" application
process0 = Process(pid=101)
process1 = Process(pid=102)

# Set the command
# cmd is a list which begins with the executable (like argv)
process0.cmd = [binary0]
process1.cmd = [binary1]
# Set the cpu to use the process as its workload and create thread contexts
for cpu in system.cpu0:
    cpu.workload = process0
    cpu.createThreads()

for cpu in system.cpu1:
    cpu.workload = process1
    cpu.createThreads()

system.workload = SEWorkload.init_compatible(binary0)

# Set up the pseudo file system for the threads function above
config_filesystem(system)

# set up the root SimObject and start the simulation
root = Root(full_system=False, system=system)
# instantiate all of the objects we've created above
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print(
    "Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getC
