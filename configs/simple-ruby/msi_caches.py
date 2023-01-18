# -*- coding: utf-8 -*-
# Copyright (c) 2017 Jason Power
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

""" This file creates a set of Ruby caches, the Ruby network, and a simple
point-to-point topology.
See Part 3 in the Learning gem5 book:
http://gem5.org/documentation/learning_gem5/part3/MSIintro

IMPORTANT: If you modify this file, it's likely that the Learning gem5 book
           also needs to be updated. For now, email Jason <jason@lowepower.com>

"""

import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

from topologies.BaseTopology import SimpleTopology
from example.c2ctest.DisjointNetwork import *
from ruby import Ruby


class MyCacheSystem(RubySystem):
    def __init__(self):
        if buildEnv["PROTOCOL"] != "MSI":
            fatal("This system assumes MSI from learning gem5!")

        super(MyCacheSystem, self).__init__()


#   def create(self, options, system, piobus, dma_devices):
    def setup(self, system, cpus, mem_ctrls):
        """Set up the Ruby cache subsystem. Note: This can't be done in the
        constructor because many of these items require a pointer to the
        ruby system (self). This causes infinite recursion in initialize()
        if we do this in the __init__.
        """
        # Ruby's global network.
        self.network = MyNetwork(self)
#        self.network_cpu = DisjointGarnet(self)

        # MSI uses 3 virtual networks. One for requests (lowest priority), one
        # for responses (highest priority), and one for "forwards" or
        # cache-to-cache requests. See *.sm files for details.
        self.number_of_virtual_networks = 3
        self.network.number_of_virtual_networks = 3

###############################################################################
#        # Construct CPU controllers
#        cpu_dir_nodes = construct_dirs(options, system, self, self.network_cpu)
#        (cp_sequencers, cp_cntrl_nodes) = construct_corepairs(
#            options, system, self, self.network_cpu
#        )
#
#        # Construct CPU memories for cpu_network
#        Ruby.setup_memory_controllers(system, self, cpu_dir_nodes, options)
#
#        # Configure the directories based on which network they are in
#        for cpu_dir_node in cpu_dir_nodes:
#          cpu_dir_node.CPUonly = True
#          cpu_dir_node.GPUonly = False
#
#        # Assign the memory controller to the system
#        cpu_abstract_mems = []
#        for mem_ctrl in system.mem_ctrls:
#          cpu_abstract_mems.append(mem_ctrl.dram)
#        system.memories = cpu_abstract_mems
#
#        cpu_dma_ctrls = []
#
#        for i, dma_device in enumerate(dma_devices):
#            dma_seq = DMASequencer(version=i, ruby_system=self)
#            dma_cntrl = DMA_Controller(
#                version=i, dma_sequencer=dma_seq, ruby_system=self
#            )
#
#            # Handle inconsistently named ports on various DMA devices:
#            if not hasattr(dma_device, "type"):
#                # IDE doesn't have a .type but seems like everything else does.
#                dma_seq.in_ports = dma_device
#            elif dma_device.type in gpu_dma_types:
#                dma_seq.in_ports = dma_device.port
#            else:
#                dma_seq.in_ports = dma_device.dma
#
#            if (
#                hasattr(dma_device, "type")
#                and dma_device.type in gpu_dma_types
#            ):
#                dma_cntrl.requestToDir = MessageBuffer(buffer_size=0)
#                dma_cntrl.requestToDir.out_port = self.network_gpu.in_port
#                dma_cntrl.responseFromDir = MessageBuffer(buffer_size=0)
#                dma_cntrl.responseFromDir.in_port = self.network_gpu.out_port
#                dma_cntrl.mandatoryQueue = MessageBuffer(buffer_size=0)
#
#                gpu_dma_ctrls.append(dma_cntrl)
#            else:
#                dma_cntrl.requestToDir = MessageBuffer(buffer_size=0)
#                dma_cntrl.requestToDir.out_port = self.network_cpu.in_port
#                dma_cntrl.responseFromDir = MessageBuffer(buffer_size=0)
#                dma_cntrl.responseFromDir.in_port = self.network_cpu.out_port
#                dma_cntrl.mandatoryQueue = MessageBuffer(buffer_size=0)
#
#                cpu_dma_ctrls.append(dma_cntrl)
#
#            dma_cntrls.append(dma_cntrl)
#
#        system.dma_cntrls = dma_cntrls
#
#        # Collect CPU and GPU controllers into seperate lists
#        cpu_cntrls = cpu_dir_nodes + cp_cntrl_nodes + cpu_dma_ctrls
#
#        self.network_cpu.number_of_virtual_networks = 11
#        
#        # Connect the controllers and builds the topology
#        self.network_cpu.connectCPU(options, cpu_cntrls)
#
#        # Proxy for connecting system port. System port is used for loading
#        # from outside guest, e.g., binaries like vmlinux.
#        system.sys_port_proxy = RubyPortProxy(ruby_system=self)
#        system.sys_port_proxy.pio_request_port = piobus.cpu_side_ports
#        system.system_port = system.sys_port_proxy.in_ports
#
#        # Only CPU sequencers connect to PIO bus. This acts as the "default"
#        # destination for unknown address ranges. PCIe requests fall under this
#        # category.
#
#        for i in range(len(cp_sequencers)):
#            cp_sequencers[i].pio_request_port = piobus.cpu_side_ports
#            cp_sequencers[i].mem_request_port = piobus.cpu_side_ports
#
#            # The CorePairs in MOESI_AMD_Base round up when constructing
#            # sequencers, but if the CPU does not exit there would be no
#            # sequencer to send a range change, leading to assert.
#            if i < options.num_cpus:
#                cp_sequencers[i].pio_response_port = piobus.mem_side_ports
#
#        # Setup ruby port. Both CPU and GPU are actually connected here.
#        all_sequencers = (
#            cp_sequencers + tcp_sequencers + sqc_sequencers + scalar_sequencers
#        )
#        self._cpu_ports = all_sequencers
#        self.num_of_sequencers = len(all_sequencers)
#
###############################################################################
        # There is a single global list of all of the controllers to make it
        # easier to connect everything to the global network. This can be
        # customized depending on the topology/network requirements.
        # Create one controller for each L1 cache (and the cache mem obj.)
        # Create a single directory controller (Really the memory cntrl)
        self.controllers = [L1Cache(system, self, cpu) for cpu in cpus] + [
            DirController(self, system.mem_ranges, mem_ctrls)
        ]

        # Create one sequencer per CPU. In many systems this is more
        # complicated since you have to create sequencers for DMA controllers
        # and other controllers, too.
        self.sequencers = [
            RubySequencer(
                version=i,
                # I/D cache is combined and grab from ctrl
                dcache=self.controllers[i].cacheMemory,
                clk_domain=self.controllers[i].clk_domain,
            )
            for i in range(len(cpus))
        ]

        # We know that we put the controllers in an order such that the first
        # N of them are the L1 caches which need a sequencer pointer
        for i, c in enumerate(self.controllers[0 : len(self.sequencers)]):
            c.sequencer = self.sequencers[i]

        self.num_of_sequencers = len(self.sequencers)

        # Create the network and connect the controllers.
        # NOTE: This is quite different if using Garnet!
        self.network.connectControllers(self.controllers)
        self.network.setup_buffers()

        # Set up a proxy port for the system_port. Used for load binaries and
        # other functional-only things.
        self.sys_port_proxy = RubyPortProxy()
        system.system_port = self.sys_port_proxy.in_ports

        # Connect the cpu's cache, interrupt, and TLB ports to Ruby
        for i, cpu in enumerate(cpus):
            self.sequencers[i].connectCpuPorts(cpu)



class L1Cache(L1Cache_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, system, ruby_system, cpu):
        """CPUs are needed to grab the clock domain and system is needed for
        the cache block size.
        """
        super(L1Cache, self).__init__()

        self.version = self.versionCount()
        # This is the cache memory object that stores the cache data and tags
        self.cacheMemory = RubyCache(
            size="16kB", assoc=8, start_index_bit=self.getBlockSizeBits(system)
        )
        self.clk_domain = cpu.clk_domain
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


class DirController(Directory_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, ruby_system, ranges, mem_ctrls):
        """ranges are the memory ranges assigned to this controller."""
        if len(mem_ctrls) > 1:
            panic("This cache system can only be connected to one mem ctrl")
        super(DirController, self).__init__()
        self.version = self.versionCount()
        self.addr_ranges = ranges
        self.ruby_system = ruby_system
        self.directory = RubyDirectoryMemory()
        # Connect this directory to the memory side.
        self.memory = mem_ctrls[0].port
        self.connectQueues(ruby_system)

    def connectQueues(self, ruby_system):
        self.requestFromCache = MessageBuffer(ordered=True)
        self.requestFromCache.in_port = ruby_system.network.out_port
        self.responseFromCache = MessageBuffer(ordered=True)
        self.responseFromCache.in_port = ruby_system.network.out_port

        self.responseToCache = MessageBuffer(ordered=True)
        self.responseToCache.out_port = ruby_system.network.in_port
        self.forwardToCache = MessageBuffer(ordered=True)
        self.forwardToCache.out_port = ruby_system.network.in_port

        # These are other special message buffers. They are used to send
        # requests to memory and responses from memory back to the controller.
        # Any messages sent or received on the memory port (see self.memory
        # above) will be directed through these message buffers.
        self.requestToMemory = MessageBuffer()
        self.responseFromMemory = MessageBuffer()


class MyNetwork(SimpleNetwork):
    """A simple point-to-point network. This doesn't not use garnet."""

    def __init__(self, ruby_system):
        super(MyNetwork, self).__init__()

        self.netifs = []
        self.routers = []
        self.int_links = []
        self.ext_links = []
        self.ruby_system = ruby_system

    def connectControllers(self, controllers):
        """Connect all of the controllers to routers and connec the routers
        together in a point-to-point network.
        """
        # Create one router/switch per controller in the system
        self.routers = [Switch(router_id=i) for i in range(len(controllers))]

        # Make a link from each controller to the router. The link goes
        # externally to the network.
        self.ext_links = [
            SimpleExtLink(link_id=i, ext_node=c, int_node=self.routers[i])
            for i, c in enumerate(controllers)
        ]

        # Make an "internal" link (internal to the network) between every pair
        # of routers.
        link_count = 0
        int_links = []
        for ri in self.routers:
            for rj in self.routers:
                if ri == rj:
                    continue  # Don't connect a router to itself!
                link_count += 1
                int_links.append(
                    SimpleIntLink(link_id=link_count, src_node=ri, dst_node=rj)
                )
        self.int_links = int_links


class Crossbar(SimpleTopology):
    decription = "Crossbar"

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        
        link_latency = options.link_latency
        router_latency = options.router_latency

        routers = [Router(router_id=i) for i in range(len(self.nodes) + 1)]
        xbar = routers[len(self.nodes)]
        
        network.routers = routers

        ext_links = [
            ExtLink(
                link_id=i,
                ext_node=n,
                int_node=routers[i],
                latency=link_latency,
            )
            for (i, n) in enumerate(self.nodes)
        ]
        network.ext_links = ext_links

        link_count = len(self.nodes)

        int_links = []
        for i in range(len(self.nodes)):
            int_links.append(
                IntLink(
                    link_id=(link_count + i),
                    src_node=routers[i],
                    dst_node=xbar,
                    latency=link_latency,
                )
            )

        link_count += len(self.nodes)

        for i in range(len(self.nodes)):
            int_links.append(
                IntLink(
                    link_id=(link_count + i),
                    src_node=xbar,
                    dst_node=routers[i],
                    latency=link_latency,
                )
            )
        network.int_links = int_links
