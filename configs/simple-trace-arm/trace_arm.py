import math

import m5
from m5.objects import *

import gzip
import argparse
import os

import m5
from m5.objects import *
from m5.util import addToPath
from m5.stats import periodicStatDump

addToPath("../")
from common import ObjectList
from common import MemConfig

addToPath("../../util")
import pdb; pdb.set_trace()
import protolib

m5.util.addToPath("../")
from common.FileSystemConfig import config_filesystem

addToPath("../traces")
import packet_pb2

import ruby_config
from ruby_config import MyNetwork, L1CacheTrace, DirController


np = 1
system = System(
    tgens = [TrafficGen(config_file="./m5out/lat_mem_rd.cfg", progress_check="10s") for i in range(1)],
    cpus = [X86TimingSimpleCPU() for i in range(np)],
)

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# System setup
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MB")]

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]

# Create and interrupt controller for each cpu and connect it to the membus
for cpu in system.cpus:
    cpu.createInterruptController()

# Create the Ruby system
system.ruby = RubySystem()

system.ruby.network = MyNetwork(system.ruby)

# Network configuration
# virtual networks: 0=request, 1=snoop, 2=response, 3=data
system.ruby.number_of_virtual_networks = 4

system.ruby.controllers = \
    [L1CacheTrace(system, system.ruby, cpu) for cpu in system.cpus] + \
    [DirController(system.ruby, system.mem_ranges, [system.mem_ctrl])] + \
    [L1CacheTrace(system, system.ruby, cpu) for cpu in system.cpus] 

# When np = 1
#   0      1      2    
# CPU0 | DIR | TGEN0 

# Create one sequencer per CPU
system.ruby.sequencers = [
    RubySequencer(
        version=i,
        dcache=system.ruby.controllers[i].cacheMemory,
        clk_domain=system.ruby.controllers[i].clk_domain,
    ) 
    for i in range(np)
] + [
   RubySequencer(
       version=i,
       dcache=system.ruby.controllers[i+1].cacheMemory,
       clk_domain=system.ruby.controllers[i+1].clk_domain,
   ) 
   for i in range(2, 3)
]

system.caches.controllers[0].sequencer = system.ruby.seqencers[0] 
system.caches.controllers[2].sequencer = system.ruby.seqencers[1]

system.ruby.num_of_sequencer = len(system.ruby.sequencers)

system.ruby.network.connectControllers(system.caches.controllers)
system.ruby.network.setup_buffers()

system.ruby.sys_port_proxy = RubyPortProxy()
system.system_port = system.ruby.sys_port_proxy.in_ports

# Connect the cpu's cache, interrupt, and TLB ports to Ruby
for i, cpu in enumerate(system.cpus):
    cpu.icache_port = system.caches.sequencers[i].in_ports
    cpu.dcache_port = system.caches.sequencers[i].in_ports
    cpu.mmu.itb.walker.port = system.caches.sequencers[i].in_ports
    cpu.mmu.dtb.walker.port = system.caches.sequencers[i].in_ports
    cpu.interrupts[0].pio = system.caches.sequencers[i].interrupt_out_port
    cpu.interrupts[0].int_responder = system.caches.sequencers[i].interrupt_out_port
    cpu.interrupts[0].int_requestor = system.caches.sequencers[i].in_ports

system.tgen[0].port = system.ruby.sequencers[2].in_ports

thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(
    thispath,
    "../../",
    "tests/test-progs/threads/bin/x86/threads",
)

process = Process()
process.cmd = [binary]
for cpu in system.cpus:
    cpu.workload = process
    cpu.createThreads()

system.workload = SEWorkload.init_compatible(binary)

config_filesystem(system)

root = Root(full_system=False, system=system)

m5.instantiate()
print("Begining simulation!")
exit_event = m5.simulate()
print(
    "Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getCause())
)