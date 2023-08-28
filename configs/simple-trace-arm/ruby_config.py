import math

from m5.defines import buildEnv
from m5.util import fatal, panic, addToPath
from m5.objects import *

from topologies import *
from network import Network

from . import CHI_config as chi_defs



class CHI_Cache_Controller(Cache_Controller):
    """
    Cache_Controller can also be used as a DMA requester or as
    a pure directory if all cache allocation policies are disabled.
    """
    def __init__(self, ruby_system):
        super(CHI_Cache_Controller, self).__init__(
            version=Versions.getVersion(Cache_Controller),
            ruby_system=ruby_system,
            mandatoryQueue=MessageBuffer(),
            prefetchQueue=MessageBuffer(),
            triggerQueue=TriggerMessageBuffer(),
            retryTriggerQueue=OrderedTriggerMessageBuffer(),
            replTriggerQueue=OrderedTriggerMessageBuffer(),
            reqRdy=TriggerMessageBuffer(),
            snpRdy=TriggerMessageBuffer(),
        )
        # Set somewhat large number since we really a lot on internal
        # triggers. To limit the controller performance, tweak other
        # params such as: input port buffer size, cache banks, and output
        # port latency
        self.transitions_per_cycle = 1024
        # This should be set to true in the data cache controller to enable
        # timeouts on unique lines when a store conditional fails
        self.sc_lock_enabled = False

class MyNetwork(SimpleNetwork):
    """A simple point-to-point network. This doesn't not use garnet."""

    def __init__(self, ruby_system):
        super(MyNetwork, self).__init__()
        self.netifs = []
        self.ruby_system = ruby_system

    def connectControllers(self, controllers):
        """Connect all of the controllers to routers and connec the routers
        together in a point-to-point network.
        """
        # Create one router/switch per controller in the system
        self.routers = [Switch(router_id=i) for i in range(len(controllers))]
        print("######################################")
        print("routers", self.routers)

        # Make a link from each controller to the router. The link goes
        # externally to the network.
        self.ext_links = [
            SimpleExtLink(link_id=i, ext_node=c, int_node=self.routers[i])
            for i, c in enumerate(controllers)
        ]
        print("Ext Links", self.ext_links)

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
        print("Int Links", self.int_links)


class L1CacheTrace(CHI_Cache_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, system, ruby_system, cpus):
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
        self.send_evictions = self.sendEvicts(cpus)
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

    def getBlockSizeBits(self, system):
        bits = int(math.log(system.cache_line_size, 2))
        if 2**bits != system.cache_line_size.value:
            panic("Cache line size not a power of 2!")
        return bits

    def sendEvicts(self, cpus):
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
        self.mandatoryQueue = MessageBuffer()

        # To Network
        self.reqOut = MessageBuffer(ordered=True)
        self.reqOut.out_port = ruby_system.network.in_port
        self.rspOut = MessageBuffer(ordered=True)
        self.rspOut.out_port = ruby_system.network.in_port
        self.snpOut = MessageBuffer(ordered=True)
        self.snpOut.out_port = ruby_system.network.in_port
        self.datOut = MessageBuffer(ordered=True)
        self.datOut.out_port = ruby_system.network.in_port

        # From Network
        self.reqIn = MessageBuffer(ordered=True)
        self.reqIn.in_port = ruby_system.network.out_port
        self.rspIn = MessageBuffer(ordered=True)
        self.rspIn.in_port = ruby_system.network.out_port
        self.snpIn = MessageBuffer(ordered=True)
        self.snpIn.in_port = ruby_system.network.out_port
        self.datIn = MessageBuffer(ordered=True)
        self.datIn.in_port = ruby_system.network.out_port


class DirController(CHI_Cache_Controller):

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
        # To Network
        self.reqOut = MessageBuffer(ordered=True)
        self.reqOut.out_port = ruby_system.network.in_port
        self.rspOut = MessageBuffer(ordered=True)
        self.rspOut.out_port = ruby_system.network.in_port
        self.snpOut = MessageBuffer(ordered=True)
        self.snpOut.out_port = ruby_system.network.in_port
        self.datOut = MessageBuffer(ordered=True)
        self.datOut.out_port = ruby_system.network.in_port

        # From Network
        self.reqIn = MessageBuffer(ordered=True)
        self.reqIn.in_port = ruby_system.network.out_port
        self.rspIn = MessageBuffer(ordered=True)
        self.rspIn.in_port = ruby_system.network.out_port
        self.snpIn = MessageBuffer(ordered=True)
        self.snpIn.in_port = ruby_system.network.out_port
        self.datIn = MessageBuffer(ordered=True)
        self.datIn.in_port = ruby_system.network.out_port


        # These are other special message buffers. They are used to send
        # requests to memory and responses from memory back to the controller.
        # Any messages sent or received on the memory port (see self.memory
        # above) will be directed through these message buffers.
        self.requestToMemory = MessageBuffer()
        self.responseFromMemory = MessageBuffer()
