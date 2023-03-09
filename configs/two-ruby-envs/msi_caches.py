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


import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

from topologies.BaseTopology import SimpleTopology
from ruby import Ruby


class MyCacheSystem(RubySystem):
    def __init__(self):
        if buildEnv["PROTOCOL"] != "MSI":
            fatal("This system assumes MSI from learning gem5!")

        super(MyCacheSystem, self).__init__()

    def setup(self, system, cpus, mem_ctrl):

        self.network = MyNetwork(self)

        self.number_of_virtual_networks = 3
        self.network.number_of_virtual_networks = 3

        self.controllers0 = \
                [L1Cache(system, self, self.network, cpu) for cpu in cpus] + \
                [DirController(self, self.network, system.mem_ranges[0], mem_ctrl)]
        
        self.sequencers0 = [
            RubySequencer(
                version=i,
                # I/D cache is combined and grab from ctrl
                dcache=self.controllers0[i].cacheMemory,
                clk_domain=self.controllers0[i].clk_domain,
            )
            for i in range(len(cpus))
        ]

        for i, c in enumerate(self.controllers0[0 : len(self.sequencers0)]):
            c.sequencer = self.sequencers0[i]

        self.num_of_sequencers = len(self.sequencers0)

        self.network.connectControllers(self.controllers0)
        self.network.setup_buffers()

        #self.sys_port_proxy = RubyPortProxy()
        #system.system_port = self.sys_port_proxy.in_ports

        for i, cpu in enumerate(cpus):
            self.sequencers0[i].connectCpuPorts(cpu)



class L1Cache(L1Cache_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, system, ruby_system, network, cpu):
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
        self.connectQueues(ruby_system, network)

    def getBlockSizeBits(self, system):
        bits = int(math.log(system.cache_line_size, 2))
        if 2**bits != system.cache_line_size.value:
            panic("Cache line size not a power of 2!")
        return bits

    def sendEvicts(self, cpu):
        return True

    def connectQueues(self, ruby_system, network):

        self.mandatoryQueue = MessageBuffer()

        self.requestToDir = MessageBuffer(ordered=True)
        self.requestToDir.out_port = network.in_port
        self.responseToDirOrSibling = MessageBuffer(ordered=True)
        self.responseToDirOrSibling.out_port = network.in_port
        self.forwardFromDir = MessageBuffer(ordered=True)
        self.forwardFromDir.in_port = network.out_port
        self.responseFromDirOrSibling = MessageBuffer(ordered=True)
        self.responseFromDirOrSibling.in_port = network.out_port


class DirController(Directory_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, ruby_system, network, ranges, mem_ctrl):
        """ranges are the memory ranges assigned to this controller."""
        super(DirController, self).__init__()
        self.version = self.versionCount()
        self.addr_ranges = ranges
        self.ruby_system = ruby_system
        self.directory = RubyDirectoryMemory()
        # Connect this directory to the memory side.
        self.memory = mem_ctrl.port
        self.connectQueues(ruby_system, network)

    def connectQueues(self, ruby_system, network):
        self.requestFromCache = MessageBuffer(ordered=True)
        self.requestFromCache.in_port = network.out_port
        self.responseFromCache = MessageBuffer(ordered=True)
        self.responseFromCache.in_port = network.out_port

        self.responseToCache = MessageBuffer(ordered=True)
        self.responseToCache.out_port = network.in_port
        self.forwardToCache = MessageBuffer(ordered=True)
        self.forwardToCache.out_port = network.in_port

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

        topo = Crossbar(controllers)
        topo.makeTopology(self, SimpleIntLink, SimpleExtLink, Switch)

        self.initSimple(self.int_links, self.ext_links)
    
    def initSimple(self, int_links, ext_links):
        # Attach links to network
        self.int_links = int_links
        self.ext_links = ext_links
        


class Crossbar(SimpleTopology):
    decription = "Crossbar"

    def makeTopology(self, network, IntLink, ExtLink, Router):

        link_latency = 1
        router_latency = 1

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
