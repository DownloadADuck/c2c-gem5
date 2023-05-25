# Ruby configuration script for arm CHI simlation
import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

from topologies.BaseTopology import SimpleTopology
from ruby import Ruby
from CHI_config import *
#from .Ruby import create_topology


class MyCacheSystem(RubySystem):
    def __init__(self):
        if buildEnv["PROTOCOL"] != "CHI":
            fatal("This system assumes MSI.")

        super(MyCacheSystem, self).__init__()

    def setup(self, system, cpus0, cpus1, mem_ctrls0, mem_ctrls1):

        l1i_size  = '64KB'
        l1i_assoc = 2
        l1d_size  = '64KB'
        l1d_assoc = 4
        l2_size  = '256KB'
        l2_assoc = 4
        l3_size  = '16MB'
        l3_assoc = 6

        num_l3caches = 1
        num_dirs = 1


        # Ruby's global network.
#        self.network0 = MyNetwork(self)
#        self.network1 = MyNetwork(self)
        # MSI uses 3 virtual networks. One for requests (lowest priority), one
        # for responses (highest priority), and one for "forwards" or
        # cache-to-cache requests. See *.sm files for details.
#        self.number_of_virtual_networks = 3
#        self.network0.number_of_virtual_networks = 3
#        self.network1.number_of_virtual_networks = 3

        # There is a single global list of all of the controllers to make it
        # easier to connect everything to the global network. This can be
        # customized depending on the topology/network requirements.
        # Create one controller for each L1 cache (and the cache mem obj.)
        # Create a single directory controller (Really the memory cntrl)
        #######################################################################
        RNF = CHI_RNF(cpus0, self, l1Icache_type, l1Dcache_type, '64B')
        HNF = CHI_HNF()
        MN  = CHI_MN()
        SNF_MainMem = CHI_SNF_MainMem()
        SNF_BootMem = CHI_SNF_BootMem()
        RNI_DMA = CHI_RNI_DMA()
        RNI_IO  = CHI_RNI_IO()

        class L1ICache(RubyCache):
            dataAccessLatency = 1
            tagAccessLatency  = 1
            size = l1i_size
            assoc = l1i_assoc # TO BE DEFINED
        
        class L1Dcache(RubyCache):
            dataAccessLatency = 2
            tagAccessLatency  = 1
            size = l1d_size
            assoc = l1d_assoc # TO BE DEFINED

        class L2Dcache(RubyCache):
            dataAccessLatency = 6
            tagAccessLatency  = 2
            size = l2_size
            assoc = l2_assoc # TO BE DEFINED

        class HNFcache(RubyCache):
            dataAccessLatency = 10
            tagAccessLatency  = 2
            size = l3_size
            assoc = l3_assoc # TO BE DEFINED

        # other functions use system.cache_line_size assuming it has been set
        assert system.cache_line_size == '64B'        

        cpu_sequencers = []
        mem_cntrls = []
        men_dests = []
        network_nodes = []
        network_cntrls = []
        hnf_dests = []
        all_cntrls = []

        # Creates one RNF per cpu with priv L2 caches
        self.rnf = [
            CHI_RNF(
                [cpu],
                self,
                L1ICache,
                L1DCache,
                system.cache_line_size.value,
            )
            for cpu in cpus0
        ] 
        for rnf in self.rnf:
            rnf.addPrivL2Cache(L2Cache)
            cpu_sequencers.extend(rnf.getSequencers())
            all_cntrls.extend(rnf.getAllControllers())
            network_nodes.append(rnf)
            network_cntrls.extend(rnf.getNetworkSideControllers())

        # Creates one Misc Node
        self.mn = [CHI_MN(self, [cpu.l1d for cpu in cpus0])]
        for mn in self.mn:
            all_cntrls.extend(mn.getAllControllers())
            network_nodes.append(mn)
            network_cntrls.extend(mn.getNetworkSideControllers())
            assert mn.getAllControllers() == mn.getNetworkSideControllers()

        # Look for other memories
        other_memories = []
        if bootmem:
            other_memories.append(bootmen)
        if getattr(system, "sram", None):
            other_memories.append(getattr(system, "sran", None))
        on_chip_mem_ports = getattr(system, "_on_chip_mem_ports", None)
        if on_chip_mem_ports:
            other_memories.extend([p.simobj for p in on_chip_mem_ports])

        # Creates LLCs cntrls
        sysranges = [] + system.mem_ranges

        for m in other_memories:
            sysranges.append(m.range)

        hnf_list = [i for i in range(options.num_l3caches)]
        CHI_HNF.createAddrRanges(sysranges, system.cache_line_size.value, hnf_list)
        self.hnf = [
            CHI_HNF(i, self, HNFCache, None)
            for i in range(num_l3caches)
        ]

        for hnf in self.hnf:
            network_nodes.append(hnf)
            network_cntrls.extend(hnf.getNetworkSideControllers())
            assert hnf.getAllControllers() == hnf.getNetworkSideControllers()
            all_cntrls.extend(hnf.getAllControllers())
            hnf_dests.extend(hnf.getAllControllers())
        
        # Create the memory controllers
        # We don't define a Directory_Controller type se we don't use
        # create_directories shared by other protocols

        self.snf = [
            CHI_SNF_MainMem(self, None, None)
            for i in range(num_dirs)
        ]
        for snf in self.snf:
            network_nodes.append(snf)
            network_cntrls.extend(snf.getNetworkSideControllers())
            assert snf.getAllControllers() == snf.getNetworkSideControllers()
            mem_cntrls.extend(snf.getAllControllers())
            all_cntrls.extend(snf.getAllControllers())
            mem_dests.extend(snf.getAllControllers())

        if len(other_memories) > 0:
            self.rom_snf = [
                CHI_SNF_BootMem(self, None, m) for m in other_memories
            ]
        for snf in self.rom_snf:
            network_nodes.append(snf)
            network_cntrls.extend(snf.getNetworkSideControllers())
            all_cntrls.extend(snf.getAllControllers())
            mem_dests.extend(snf.getAllControllers())

        # Create controllers for dma ports and io
        if len(dma_ports) > 0:
            self.dma_rni = [
                CHI_RNI_DMA(self, dma_port, None) for dma_port in dma_ports
            ]
            for rni in self.dma_rni:
                network_nodes.append(rni)
                network_cntrls.extend(rni.getNetworkSideControllers())
                all_cntrls.extend(rni.getAllControllers())

        # Assign downstream destinations

        for rnf in self.rnf:
            rnf.setDownstream(hnf_dests)
        if len(dma_ports) > 0:
            for rni in self.dma_rni:
                rni.setDownstream(hnf_dests)
        if full_system:
            self.io_rni.setDownstream(hnf_dests)
        for hnf in self.hnf:
            hnf.setDownstream(mem_dests)

        # Setup data message size for all controllers
        for cntrl in all_cntrls:
            cntrl.data_channel_size = params.data_width

        # Network configurations
        # virtual networks: 0=request, 1=snoop, 2=response, 3=data
        self.network.number_of_virtual_networks = 4

        self.network.control_msg_size = params.cntrl_msg_size
        self.network.data_msg_size = params.data_width
        if options.network == "simple":
            self.network.buffer_size = params.router_buffer_size

        # Incorporate the params into options so it's propagated to
        # makeTopology and create_topology the parent scripts
        for k in dir(params):
            if not k.startswith("__"):
                setattr(options, k, getattr(params, k))

        if options.topology == "CustomMesh":
            topology = create_topology(network_nodes, options)
        elif options.topology in ["Crossbar", "Pt2Pt"]:
            topology = create_topology(network_cntrls, options)
        else:
            m5.fatal("%s not supported!" % options.topology)

# We don't need to return since we are in class
#        return (cpu_sequencers, mem_cntrls, topology)

        #######################################################################

#        self.controllers0 = [L1Cache(system, self, self.network0, cpu) for cpu 
#                in cpus0] + [DirController(self, self.network0,
#                    system.mem_ranges[0], mem_ctrls0)]
#
#        self.controllers1 = [L1Cache(system, self, self.network1, cpu) for cpu 
#                in cpus1] + [DirController(self, self.network1,
#                    system.mem_ranges[1], mem_ctrls1)]

        # Create one sequencer per CPU. In many systems this is more
        # complicated since you have to create sequencers for DMA controllers
        # and other controllers, too.
#        self.sequencers0 = [
#            RubySequencer(
#                version=i,
#                # I/D cache is combined and grab from ctrl
#                dcache=self.controllers0[i].cacheMemory,
#                clk_domain=self.controllers0[i].clk_domain,
#            )
#            for i in range(len(cpus0))
#        ]
#        self.sequencers1 = [
#            RubySequencer(
#                version=i,
#                # I/D cache is combined and grab from ctrl
#                dcache=self.controllers1[i].cacheMemory,
#                clk_domain=self.controllers1[i].clk_domain,
#            )
#            for i in range(len(cpus1))
#        ]
#
#        # We know that we put the controllers in an order such that the first
#        # N of them are the L1 caches which need a sequencer pointer
#        for i, c in enumerate(self.controllers0[0 : len(self.sequencers0)]):
#            c.sequencer = self.sequencers0[i]
#            
#        for i, c in enumerate(self.controllers1[0 : len(self.sequencers1)]):
#            c.sequencer = self.sequencers1[i]
#        
#        # In our case, the number of sequencers does not have a direct impact.
#        # We still set it to the right amount.
#        self.num_of_sequencers = len(self.sequencers0) + len(self.sequencers1)
#        # self.num_of_sequencers = len(self.sequencers0)
#
#        # Create the network and connect the controllers.
#        # NOTE: This is quite different if using Garnet!
#        self.network0.connectControllers(self.controllers0)
#        self.network0.setup_buffers()
#        self.network1.connectControllers(self.controllers1)
#        self.network1.setup_buffers()
#
#        # Set up a proxy port for the system_port. Used for load binaries and
#        # other functional-only things.
#        self.sys_port_proxy = RubyPortProxy()
#        system.system_port = self.sys_port_proxy.in_ports
#
#        # Connect the cpu's cache, interrupt, and TLB ports to Ruby
#        for i, cpu in enumerate(cpus0):
#            self.sequencers0[i].connectCpuPorts(cpu)
#        for i, cpu in enumerate(cpus1):
#            self.sequencers1[i].connectCpuPorts(cpu)



#class L1Cache(L1Cache_Controller):
#
#    _version = 0
#
#    @classmethod
#    def versionCount(cls):
#        cls._version += 1  # Use count for this particular type
#        return cls._version - 1
#
#    def __init__(self, system, ruby_system, network, cpu):
#        """CPUs are needed to grab the clock domain and system is needed for
#        the cache block size.
#        """
#        super(L1Cache, self).__init__()
#
#        self.version = self.versionCount()
#        # This is the cache memory object that stores the cache data and tags
#        self.cacheMemory = RubyCache(
#            size="16kB", assoc=8, start_index_bit=self.getBlockSizeBits(system)
#        )
#        self.clk_domain = cpu.clk_domain
#        self.send_evictions = self.sendEvicts(cpu)
#        self.ruby_system = ruby_system
#        self.connectQueues(ruby_system, network)
#
#    def getBlockSizeBits(self, system):
#        bits = int(math.log(system.cache_line_size, 2))
#        if 2**bits != system.cache_line_size.value:
#            panic("Cache line size not a power of 2!")
#        return bits
#
#    def sendEvicts(self, cpu):
#        """True if the CPU model or ISA requires sending evictions from caches
#        to the CPU. Two scenarios warrant forwarding evictions to the CPU:
#        1. The O3 model must keep the LSQ coherent with the caches
#        2. The x86 mwait instruction is built on top of coherence
#        3. The local exclusive monitor in ARM systems
#
#        As this is an X86 simulation we return True.
#        """
#        return True
#
#    def connectQueues(self, ruby_system, network):
#        """Connect all of the queues for this controller."""
#        # mandatoryQueue is a special variable. It is used by the sequencer to
#        # send RubyRequests from the CPU (or other processor). It isn't
#        # explicitly connected to anything.
#        self.mandatoryQueue = MessageBuffer()
#
#        # All message buffers must be created and connected to the
#        # general Ruby network. In this case, "in_port/out_port" don't
#        # mean the same thing as normal gem5 ports. If a MessageBuffer
#        # is a "to" buffer (i.e., out) then you use the "out_port",
#        # otherwise, the in_port.
#        self.requestToDir = MessageBuffer(ordered=True)
#        self.requestToDir.out_port = network.in_port
#        self.responseToDirOrSibling = MessageBuffer(ordered=True)
#        self.responseToDirOrSibling.out_port = network.in_port
#        self.forwardFromDir = MessageBuffer(ordered=True)
#        self.forwardFromDir.in_port = network.out_port
#        self.responseFromDirOrSibling = MessageBuffer(ordered=True)
#        self.responseFromDirOrSibling.in_port = network.out_port
#
#
#class DirController(Directory_Controller):
#
#    _version = 0
#
#    @classmethod
#    def versionCount(cls):
#        cls._version += 1  # Use count for this particular type
#        return cls._version - 1
#
#    def __init__(self, ruby_system, network, ranges, mem_ctrls):
#        """ranges are the memory ranges assigned to this controller."""
#        if len(mem_ctrls) > 1:
#            panic("This cache system can only be connected to one mem ctrl")
#        super(DirController, self).__init__()
#        self.version = self.versionCount()
#        self.addr_ranges = ranges
#        self.ruby_system = ruby_system
#        self.directory = RubyDirectoryMemory()
#        # Connect this directory to the memory side.
#        self.memory = mem_ctrls.port
#        self.connectQueues(ruby_system, network)
#
#    def connectQueues(self, ruby_system, network):
#        self.requestFromCache = MessageBuffer(ordered=True)
#        self.requestFromCache.in_port = network.out_port
#        self.responseFromCache = MessageBuffer(ordered=True)
#        self.responseFromCache.in_port = network.out_port
#
#        self.responseToCache = MessageBuffer(ordered=True)
#        self.responseToCache.out_port = network.in_port
#        self.forwardToCache = MessageBuffer(ordered=True)
#        self.forwardToCache.out_port = network.in_port
#
#        # These are other special message buffers. They are used to send
#        # requests to memory and responses from memory back to the controller.
#        # Any messages sent or received on the memory port (see self.memory
#        # above) will be directed through these message buffers.
#        self.requestToMemory = MessageBuffer()
#        self.responseFromMemory = MessageBuffer()
#
#
#class MyNetwork(SimpleNetwork):
#    """A simple point-to-point network. This doesn't not use garnet."""
#
#    def __init__(self, ruby_system):
#        super(MyNetwork, self).__init__()
#
#        self.netifs = []
#        self.routers = []
#        self.int_links = []
#        self.ext_links = []
#        self.ruby_system = ruby_system
#
#    def connectControllers(self, controllers):
#        """Connect all of the controllers to routers and connec the routers
#        together in a point-to-point network.
#        """
#        topo = Crossbar(controllers)
#        print("controllers: ", controllers)
#        topo.makeTopology(self, SimpleIntLink, SimpleExtLink, Switch)
#
#        self.initSimple(self.int_links, self.ext_links)
#    
#    def initSimple(self, int_links, ext_links):
#        # Attach links to network
#        self.int_links = int_links
#        self.ext_links = ext_links
#
#        # Commented because fatal: User should not manually set links
##        self.setup_buffers()
#        
#
#
#
#class Crossbar(SimpleTopology):
#    decription = "Crossbar"
#
#    def makeTopology(self, network, IntLink, ExtLink, Router):
#
#        # We don't have any arg parser. We manually set the latencies 
##        link_latency = options.link_latency
##        router_latency = options.router_latency
#        link_latency = 1
#        router_latency = 1
#
#        routers = [Router(router_id=i) for i in range(len(self.nodes) + 1)]
#        xbar = routers[len(self.nodes)]
#        
#        network.routers = routers
#
#        ext_links = [
#            ExtLink(
#                link_id=i,
#                ext_node=n,
#                int_node=routers[i],
#                latency=link_latency,
#            )
#            for (i, n) in enumerate(self.nodes)
#        ]
#        network.ext_links = ext_links
#
#        link_count = len(self.nodes)
#
#        int_links = []
#        for i in range(len(self.nodes)):
#            int_links.append(
#                IntLink(
#                    link_id=(link_count + i),
#                    src_node=routers[i],
#                    dst_node=xbar,
#                    latency=link_latency,
#                )
#            )
#
#        link_count += len(self.nodes)
#
#        for i in range(len(self.nodes)):
#            int_links.append(
#                IntLink(
#                    link_id=(link_count + i),
#                    src_node=xbar,
#                    dst_node=routers[i],
#                    latency=link_latency,
#                )
#            )
#        network.int_links = int_links
#