import math
import m5

from m5.objects import *
from m5.defines import buildEnv
from m5.util import addToPath, fatal
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

from two_HNFs import tgen_CHI

addToPath("../")
from common import ObjectList
from common import MemConfig
from common import FileSystemConfig

from topologies import *
from network import Network

def setup_memory_controllers(system, ruby, dir_cntrls, options):
    ruby.block_size_bytes = options.cacheline_size
    ruby.memory_size_bits = 48

    index = 0
    mem_ctrls = []
    crossbars = []

    intlv_size = options.cacheline_size

    for dir_cntrl, mem_range in zip(dir_cntrls, system.mem_ranges):
        crossbar = None
        
        dir_ranges = []
        mem_type = ObjectList.mem_list.get(options.mem_type) 
        dram_intf = MemConfig.create_mem_intf(
            mem_type,
            mem_range,
            index,
            int(math.log(options.num_dirs, 2)),
            intlv_size, #6
            options.xor_low_bit + 1, #20
        )

        if issubclass(mem_type, DRAMInterface):
            mem_ctrl = m5.objects.MemCtrl(dram=dram_intf)
        else:
            mem_ctrl = dram_intf
        
        mem_ctrls.append(mem_ctrl)
        dir_ranges.append(dram_intf.range)

        if crossbar is not None:
            mem_ctrl.port = crossbar.mem_side_ports
        else:
            mem_ctrl.port = dir_cntrl.memory_out_port
        
        # Enable low-power DRAM states if option is enabled
        if issubclass(mem_type, DRAMInterface):
            mem_ctrl.dram.enable_dram_powerdown = options.enable_dram_powerdown
        
        index += 1
        dir_cntrl.addr_ranges = dir_ranges
    
    system.mem_ctrls = mem_ctrls

    #for dir_cntrl in dir_cntrls:
    #    crossbar = None
    #    #if len(system.mem_ranges) > 1:
    #    #    crossbar = IOXBar()
    #    #    crossbars.append(crossbar)
    #    #    dir_cntrl.memory_out_ports = crossbar.cpu_side_ports
    #    
    #    dir_ranges = []
    #    for r in system.mem_ranges:
    #        mem_type = ObjectList.mem_list.get(options.mem_type)
    #        dram_intf = MemConfig.create_mem_intf(
    #            mem_type,
    #            r,
    #            index,
    #            int(math.log(options.num_dirs, 2)),
    #            intlv_size, # 6
    #            options.xor_low_bit + 1, #20
    #        )
    #        if issubclass(mem_type, DRAMInterface):
    #            mem_ctrl = m5.objects.MemCtrl(dram=dram_intf)
    #        else: 
    #            mem_ctrl = dram_intf
    #        
    #        mem_ctrls.append(mem_ctrl)
    #        dir_ranges.append(dram_intf.range)

    #        if crossbar != None:
    #            mem_ctrl.port = crossbar.mem_side_ports
    #        else:
    #            mem_ctrl.port = dir_cntrl.memory_out_port
    #        # Enable low-power DRAM states if option is enabled
    #        if issubclass(mem_type, DRAMInterface):
    #            mem_ctrl.dram.enable_dram_powerdown = (
    #                options.enable_dram_powerdown
    #            )
    #    index += 1
    #    dir_cntrl.addr_ranges = dir_ranges
    #system.mem_ctrls = mem_ctrls
    
    if len(crossbars) > 0:
        ruby.crossbars = crossbars

def create_topology(controllers, options):
    exec("import topologies.%s as Topo" % options.topology)
    topology = eval("Topo.%s(controllers)" % options.topology)
    return topology

def create_system(
    options,
    full_system,
    system,
    piobus=None,
    dma_ports=[],
    bootmem=None,
    cpus=None,
):
    system.ruby = RubySystem()
    ruby = system.ruby
    
    # Generate pseudo filesystem
    FileSystemConfig.config_filesystem(system, options)

    # Create the network object
    (
        network,
        IntLinkClass,
        ExtLinkClass,
        RouterClass,
        InterfaceClass,
    ) = Network.create_network(options, ruby)
    ruby.network = network

    if cpus is None:
        cpus = system.cpus
    
    (cpu_sequencers, tgen_sequencers, dir_cntrls, topology) = \
        tgen_CHI.create_system(
            options, 
            full_system, 
            system, 
            dma_ports, 
            bootmem, 
            ruby, 
            cpus
        )

    # Create the network topology
    topology.makeTopology(
        options, network, IntLinkClass, ExtLinkClass, RouterClass
    )

    # In SE register the ropology elements with fake filesystem
    if not full_system:
        topology.registerTopology(options)

    # Initialize network based topology
    Network.init_network(options, network, InterfaceClass)

    # Create a port proxy for connecting the system port.
    sys_port_proxy = RubyPortProxy(ruby_system=ruby)
    if piobus is not None:
        sys_port_proxy.pio_request_port = piobus.cpu_side_ports
    
    # Give the system port proxy a SimObject parent without creating a
    # full-fledged controller
    system.sys_port_proxy = sys_port_proxy
    
    # Connect the system port for loading of binaries etc
    system.system_port = system.sys_port_proxy.in_ports

    for dir_cntrl in dir_cntrls:
        print("dir cntrls -> ", dir_cntrl)
    
    setup_memory_controllers(system, ruby, dir_cntrls, options)

    # Connect the cpu sequencers and the piobus
    if piobus != None:
        for cpu_seq in cpu_sequencers:
            cpu_seq.connectIOPorts(piobus)

    # TrafficGen setup
    for i in range(len(cpus)):
        system.tgens[i].port = cpu_sequencers[i].in_ports
    
    ruby.number_of_virtual_networks = ruby.network.number_of_virtual_networks
    ruby._cpu_ports = cpu_sequencers
    ruby.num_of_sequencers = len(cpu_sequencers) + len(tgen_sequencers)


def create_directories(options, bootmem, ruby_system, system):
    dir_cntrl_nodes = []
    for i in range(options.num_dirs):
        dir_cntrl = Directory_Controller()
        dir_cntrl.version = i
        dir_cntrl.directory = RubyDirectoryMemory()
        dir_cntrl.ruby_system = ruby_system
        
        exec("ruby_system.dir_cntrl%d = dir_cntrl" % i)
        dir_cntrl_nodes.append(dir_cntrl)
    
    if bootmem is not None:
        rom_dir_cntrl = Directory_Controller()
        rom_dir_cntrl.directoy = RubyDirectoryMemory()
        rom_dir_cntrl.ruby_system = ruby_system
        rom_dir_cntrl.version = i + 1
        rom_dir_cntrl.memory = bootmem.port
        rom_dir_cntrl.addr_ranges = bootmem.range
        return (dir_cntrl_nodes, rom_dir_cntrl)
    
    return (dir_cntrl_nodes, None) 


def send_evicts(options):
    # Forwarding evictions to the CPU happens when:
    # 1. The O3 model must keep the LSQ coherent with the caches
    # 2. The x86 mwait intruction is built on top of coherence invalidations
    # 3. The local exclusive monitor in ARM systems
    if options.cpu_type == "DerivO3CPU" or get_runtime_isa() in (
        ISA.X86,
        ISA.ARM,
    ):
        return True
    return False