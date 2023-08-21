# -*- coding: utf-8 -*-
# Copyright (c) 2015 Jason Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" This file creates a system with Ruby caches and executes 'threads', a
simple multi-threaded application with false sharing to stress the Ruby
protocol.

See Part 3 in the Learning gem5 book:
http://gem5.org/documentation/learning_gem5/part3/MSIintro

IMPORTANT: If you modify this file, it's likely that the Learning gem5 book
           also needs to be updated. For now, email Jason <jason@lowepower.com>

"""
import math

# import the m5 (gem5) library created when gem5 is built
import m5

# import all of the SimObjects
from m5.objects import *


import gzip
import argparse
import os

import m5
from m5.objects import *
from m5.util import addToPath
from m5.stats import periodicStatDump

addToPath("../../")
from common import ObjectList
from common import MemConfig


addToPath("../../../util")
import pdb; pdb.set_trace()
import protolib


# Needed for running C++ threads
m5.util.addToPath("../../")
from common.FileSystemConfig import config_filesystem


addToPath("../../traces")
import packet_pb2

# You can import ruby_caches_MI_example to use the MI_example protocol instead
# of the MSI protocol
from msi_caches import MyNetwork, L1Cache, DirController, L1Cache_Controller


class L1CacheTrace(L1Cache_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, system, ruby_system, cpu):
        """CPUs are needed to grab the clock domain and system is needed for
        the cache block size.
        """
        super(L1CacheTrace, self).__init__()

        self.version = self.versionCount()
        # This is the cache memory object that stores the cache data and tags
        self.cacheMemory = RubyCache(
            size="16kB", assoc=8, start_index_bit=self.getBlockSizeBits(system)
        )
        self.clk_domain = system.clk_domain
        self.send_evictions = self.sendEvicts(cpu)
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

    def getBlockSizeBits(self, system):
        bits = int(math.log(system.cache_line_size, 2))
        if 2**bits != system.cache_line_size.value:
            panic("Cache line size not a power of 2!")
        return bits

    def sendEvicts(self, cpu):
        """True if the CPU model or ISA requires sending evictions from caches
        to the CPU. Two scenarios warrant forwarding evictions to the CPU:
        1. The O3 model must keep the LSQ coherent with the caches
        2. The x86 mwait instruction is built on top of coherence
        3. The local exclusive monitor in ARM systems

        As this is an X86 simulation we return True.
        """
        return True

    def connectQueues(self, ruby_system):
        """Connect all of the queues for this controller."""
        # mandatoryQueue is a special variable. It is used by the sequencer to
        # send RubyRequests from the CPU (or other processor). It isn't
        # explicitly connected to anything.
        self.mandatoryQueue = MessageBuffer()

        # All message buffers must be created and connected to the
        # general Ruby network. In this case, "in_port/out_port" don't
        # mean the same thing as normal gem5 ports. If a MessageBuffer
        # is a "to" buffer (i.e., out) then you use the "out_port",
        # otherwise, the in_port.
        self.requestToDir = MessageBuffer(ordered=True)
        self.requestToDir.out_port = ruby_system.network.in_port
        self.responseToDirOrSibling = MessageBuffer(ordered=True)
        self.responseToDirOrSibling.out_port = ruby_system.network.in_port
        self.forwardFromDir = MessageBuffer(ordered=True)
        self.forwardFromDir.in_port = ruby_system.network.out_port
        self.responseFromDirOrSibling = MessageBuffer(ordered=True)
        self.responseFromDirOrSibling.in_port = ruby_system.network.out_port
        

# create the system we are going to simulate
system = System()

# Set the clock frequency of the system (and all of its children)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the system
system.mem_mode = "timing"  # Use timing accesses
system.mem_ranges = [AddrRange("512MB")]  # Create an address range

# Create a pair of simple CPUs
system.cpu = [X86TimingSimpleCPU() for i in range(2)]

system.tgen1 = TrafficGen(config_file="./m5out/lat_mem_rd.cfg", progress_check="10s")
system.tgen2 = TrafficGen(config_file="./m5out/lat_mem_rd.cfg", progress_check="10s")

# Create a DDR3 memory controller and connect it to the membus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]

# create the interrupt controller for the CPU and connect to the membus
for cpu in system.cpu:
    cpu.createInterruptController()
#cpu.createInterruptController()

# Create the Ruby System
system.caches = RubySystem()


#system.caches.setup(system, system.cpu, [system.mem_ctrl])

# Ruby's global network.
system.caches.network = MyNetwork(system.caches)

# MSI uses 3 virtual networks. One for requests (lowest priority), one
# for responses (highest priority), and one for "forwards" or
# cache-to-cache requests. See *.sm files for details.
system.caches.number_of_virtual_networks = 3
system.caches.network.number_of_virtual_networks = 3

# There is a single global list of all of the controllers to make it
# easier to connect everything to the global network. This can be
# customized depending on the topology/network requirements.
# Create one controller for each L1 cache (and the cache mem obj.)
# Create a single directory controller (Really the memory cntrl)
system.caches.controllers = [L1CacheTrace(system, system.caches, cpu) for cpu in system.cpu] + [
            DirController(system.caches, system.mem_ranges, [system.mem_ctrl])] + [
            L1CacheTrace(system, system.caches, system.cpu[0])] + [L1CacheTrace(system, system.caches, system.cpu[0])]

#  0      1      2     3
# CPU0 | CPU1 | DIR | TRA

# Create one sequencer per CPU. In many systems this is more
# complicated since you have to create sequencers for DMA controllers
# and other controllers, too.
system.caches.sequencers = [
    RubySequencer(
        version=i,
        # I/D cache is combined and grab from ctrl
        dcache=system.caches.controllers[i].cacheMemory,
        clk_domain=system.caches.controllers[i].clk_domain,
    )
    for i in range(len(system.cpu))
] + [ RubySequencer(
        version=i,
        # I/D cache is combined and grab from ctrl
        dcache=system.caches.controllers[i+1].cacheMemory,
        clk_domain=system.caches.controllers[i+1].clk_domain,
    )for i in range(2,4)]

# We know that we put the controllers in an order such that the first
# N of them are the L1 caches which need a sequencer pointer
#for i, c in enumerate(system.caches.controllers[0 : len(system.cpu)]):
#    c.sequencer = system.caches.sequencers[i]
system.caches.controllers[0].sequencer = system.caches.sequencers[0]
system.caches.controllers[1].sequencer = system.caches.sequencers[1]
system.caches.controllers[3].sequencer = system.caches.sequencers[2]
system.caches.controllers[4].sequencer = system.caches.sequencers[3]    
    
system.caches.num_of_sequencers = len(system.caches.sequencers)

# Create the network and connect the controllers.
# NOTE: This is quite different if using Garnet!
system.caches.network.connectControllers(system.caches.controllers)
system.caches.network.setup_buffers()

# Set up a proxy port for the system_port. Used for load binaries and
# other functional-only things.
system.caches.sys_port_proxy = RubyPortProxy()
system.system_port = system.caches.sys_port_proxy.in_ports

# Connect the cpu's cache, interrupt, and TLB ports to Ruby
for i, cpu in enumerate(system.cpu):
    cpu.icache_port = system.caches.sequencers[i].in_ports
    cpu.dcache_port = system.caches.sequencers[i].in_ports
    cpu.mmu.itb.walker.port = system.caches.sequencers[i].in_ports
    cpu.mmu.dtb.walker.port = system.caches.sequencers[i].in_ports
    cpu.interrupts[0].pio = system.caches.sequencers[i].interrupt_out_port
    cpu.interrupts[0].int_responder = system.caches.sequencers[i].interrupt_out_port
    cpu.interrupts[0].int_requestor = system.caches.sequencers[i].in_ports


system.tgen1.port = system.caches.sequencers[2].in_ports
system.tgen2.port = system.caches.sequencers[3].in_ports
# Run application and use the compiled ISA to find the binary
# grab the specific path to the binary
thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(
    thispath,
    "../../../",
    "tests/test-progs/threads/bin/x86/linux/threads",
)

# Create a process for a simple "multi-threaded" application
process = Process()
# Set the command
# cmd is a list which begins with the executable (like argv)
process.cmd = [binary]
# Set the cpu to use the process as its workload and create thread contexts
for cpu in system.cpu:
    cpu.workload = process
    cpu.createThreads()

system.workload = SEWorkload.init_compatible(binary)

# Set up the pseudo file system for the threads function above
config_filesystem(system)

# set up the root SimObject and start the simulation
root = Root(full_system=False, system=system)
# instantiate all of the objects we've created above
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print(
    "Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getCause())
)
