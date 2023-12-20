# Building a simple architecture python script using se.py as example

import m5
from m5.util import *

from m5.objects import *

m5.util.addToPath("../")
from common.FileSystemConfig import config_filesystem

from chi_caches import MyCacheSystem

system = System()

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
arv = convert.toMemorySize('256MB')
addr_ranges_vaults = [AddrRange(i*arv, ((i+1)*arv-1)) for i in range(2)]
system.mem_ranges = addr_ranges_vaults

system.cpu0 = [ArmTimingSimpleCPU() for i in range(1)]
system.cpu1 = [ArmTimingSimpleCPU() for i in range(1)]

system.mem_ctrl0 = MemCtrl()
system.mem_ctrl0.dram = DDR3_1600_8x8()
system.mem_ctrl0.dram.range = system.mem_ranges[0]

system.mem_ctrl1 = MemCtrl()
system.mem_ctrl1.dram = DDR3_1600_8x8()
system.mem_ctrl1.dram.range = system.mem_ranges[1]

# Interrupt controllers 
for cpu in system.cpu0:
      cpu.createInterruptController()
for cpu in system.cpu1:
      cpu.createInterruptController()

system.caches = MyCacheSystem()
system.caches.setup(system, system.cpu0, system.cpu1, system.mem_ctrl0,
      system.mem_ctrl1)

thispath = os.path.dirname(os.path.realpath(__file__))

binary0 = os.path.join(
      thispath, 
      "../../",
      "tests/test-progs/hello/bin/arm/linux/hello"
)
binary1 = os.path.join(
      thispath, 
      "../../",
      "tests/test-progs/hello/bin/arm/linux/hello"
)

process0 = Process(pid=101)
process1 = Process(pid=102)

process0.cmd = [binary0]
process1.cmd = [binary1]

for cpu in system.cpu0:
      cpu.workload = process0
      cpu.createThreads()
for cpu in system.cpu1:
      cpu.workload = process1
      cpu.createThreads()

system.workload = SEWorkload.init_compatible(binary0)

# don't know if this is needed if we do not use threads
config_filesystem(system)

root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print(
      "Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getCause())
)