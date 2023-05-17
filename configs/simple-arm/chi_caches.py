import math 

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

from topologies.BaseTopology import SimpleTopology
from ruby import Ruby

class MyCacheSystem(RubySystem):
    def __init__(self):
        if buildEnv["PROTOCOL"] != "CHI":
            fatal("This system assumes CHI protcol from arm!")

        super(MyCacheSystem, self).__init__()

    def setup(self, system, cpus0, cpus1, mem_ctrls0, mem_ctrls1):

        self.network0 = MyNetwork(self)
        self.network1 = MyNetwork(self)

        self.number_of_virtual_networks = 4
        self.network0.number_of_virtual_networks = 4
        self.network1.number_of_virtual_networks = 4

        self.controllers0 = [L1Cache(system, self, self.network0, cpu) for cpu
                in cpus0] + [DirController(self, self.network0, 
                system.mem_ranges[0], mem_ctrls0)]
        self.controllers1 = [L1Cache(system, self, self.network1, cpu) for cpu
                in cpus1] + [DirController(self, self.network1, 
                system.mem_ranges[1], mem_ctrls1)]

        self.sequencers0 = [
            RubySequencer(
                version = i,
                dcache = self.controllers0[i].cacheMemory,
                clk_domain = self.controllers0[i].clk_domain,
            )
            for i in range(len(cpus0))
        ]
        self.sequencers1 = [
            RubySequencer(
                version = i,
                dcache = self.controllers1[i].cacheMemory,
                clk_domain = self.controllers1[i].clk_domain,
            )
            for i in range(len(cpus1))
        ]

        # First N controllers are caches which need a sequencer pointer
        for i, c in enumerate(self.controllers0[0 : len(self.sequencers0)]):
            c.sequencer = self.sequencers0[i]
        for i, c in enumerate(self.controllers1[0 : len(self.sequencers1)]):
            c.sequencer = self.sequencers1[i]

        self.num_of_sequencers = len(self.sequencers0) + len(self.sequencers1) 

        self.network0.connectControllers(self.controllers0)
        self.network0.setup_buffers()
        self.network1.connectControllers(self.controllers1)
        self.network1.setup_buffers()

        self.sys_port_proxy = RubyPortProxy()
        system.system_port = self.sys_port_proxy.in_ports

        for i, cpu in enumerate(cpus0):
            self.sequencers0[i].connectCpuPorts(cpu)
        for i, cpu in enumerate(cpus1):
            self.sequencers1[i].connectCpuPorts(cpu)

class L1Cache(L)