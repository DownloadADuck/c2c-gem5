import math
import m5

from m5.objects import *
from m5.defines import buildEnv
from m5.util import addToPath, fatal
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

from interface_bridge import tgen_CHI
from CHI_config import Interface, MemCtrlMessageBuffer

addToPath("../")
from common import ObjectList
from common import MemConfig
from common import FileSystemConfig

from topologies import *
from network import Network

def setup_memory_controllers(
    system,
    ruby, 
    dir_cntrls0, 
    dir_cntrls1, 
    mem_ranges0,
    mem_ranges1,
    options0,
    options1
):
    ruby.block_size_bytes = options0.cacheline_size
    ruby.memory_size_bits = 48

    index = 0
    mem_ctrls0 = []
    mem_ctrls1 = []
    crossbars = []

    intlv_size = options0.cacheline_size

    for dir_cntrl in dir_cntrls0:
        crossbar = None
        
        dir_ranges = []
        #for mem_range in mem_ranges0:
        mem_type = ObjectList.mem_list.get(options0.mem_type)
        dram_intf = MemConfig.create_mem_intf(
            mem_type,
            mem_ranges0,
            index,
            int(math.log(options0.num_dirs, 2)),
            intlv_size,
            options0.xor_low_bit,
        )
        if issubclass(mem_type, DRAMInterface):
            mem_ctrl = m5.objects.MemCtrl(dram=dram_intf)
        else: 
            mem_ctrl = dram_intf
            
        mem_ctrls0.append(mem_ctrl)
        dir_ranges.append(dram_intf.range)

        if crossbar != None:
            mem_ctrl.port = crossbar.mem_side_ports
        else:
            mem_ctrl.port = dir_cntrl.memory_out_port
        # Enable low-power DRAM states if option is enabled
        if issubclass(mem_type, DRAMInterface):
            mem_ctrl.dram.enable_dram_powerdown = (
                options0.enable_dram_powerdown
            )
        index += 1
        dir_cntrl.addr_ranges = dir_ranges

    for dir_cntrl in dir_cntrls1:
        crossbar = None
        
        dir_ranges = []
        #for mem_range in mem_ranges1:
        mem_type = ObjectList.mem_list.get(options1.mem_type)
        dram_intf = MemConfig.create_mem_intf(
            mem_type,
            mem_ranges1,
            index,
            int(math.log(options1.num_dirs, 2)),
            intlv_size,
            options1.xor_low_bit,
        )
        if issubclass(mem_type, DRAMInterface):
            mem_ctrl = m5.objects.MemCtrl(dram=dram_intf)
        else: 
            mem_ctrl = dram_intf
            
        mem_ctrls1.append(mem_ctrl)
        dir_ranges.append(dram_intf.range)

        if crossbar != None:
            mem_ctrl.port = crossbar.mem_side_ports
        else:
            mem_ctrl.port = dir_cntrl.memory_out_port
        # Enable low-power DRAM states if option is enabled
        if issubclass(mem_type, DRAMInterface):
            mem_ctrl.dram.enable_dram_powerdown = (
                options1.enable_dram_powerdown
            )
        index += 1
        dir_cntrl.addr_ranges = dir_ranges
    system.mem_ctrls0 = mem_ctrls0
    system.mem_ctrls1 = mem_ctrls1

    
    if len(crossbars) > 0:
        ruby.crossbars = crossbars

def create_topology(controllers, options):
    exec("import topologies.%s as Topo" % options.topology)
    topology = eval("Topo.%s(controllers)" % options.topology)
    return topology

def create_system(
    options,
    options1,
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

    # Create the network0 object
    # Chip 0
    (
        network0,
        IntLinkClass,
        ExtLinkClass,
        RouterClass,
        InterfaceClass,
    ) = Network.create_network(options, ruby)
    ruby.network0 = network0

    (
        network1,
        IntLinkClass,
        ExtLinkClass,
        RouterClass,
        InterfaceClass,
    ) = Network.create_network(options1, ruby)
    ruby.network1 = network1

    if cpus is None:
        cpus0 = system.cpus
        cpus1 = []

    # C2C forwarding interface setup
    ## Connecting one interface to one unique network
    ruby.interface0 = Interface(ruby, network0, network0)
    ruby.interface1 = Interface(ruby, network1, network1)

    # Create the bridge object and connect it to both interfaces
    system.bridge = InterfaceBridge()
    system.ruby.interface0.toBridge = MemCtrlMessageBuffer()
    system.ruby.interface0.fromBridge = MemCtrlMessageBuffer()
    #system.ruby.interface0.toBridge.out_port = system.bridge.chip0Response
    #system.ruby.interface0.fromBridge.in_port = system.bridge.chip1Request

    # Trying to use the RubyController mem_out_port
    system.ruby.interface0.memory_out_port = system.bridge.chip0Response

    system.ruby.interface1.toBridge = MemCtrlMessageBuffer()
    system.ruby.interface1.fromBridge = MemCtrlMessageBuffer()
    #system.ruby.interface1.toBridge.out_port = system.bridge.chip1Response
    #system.ruby.interface1.fromBridge.in_port = system.bridge.chip0Request

    # Trying to use the RubyController mem_out_port
    system.ruby.interface1.memory_out_port = system.bridge.chip0Request
    
    # Chip 0
    (cpu_sequencers0, dir_cntrls0, topology0, hnf_dests) = \
        tgen_CHI.create_chip0(
            options, 
            full_system, 
            system, 
            dma_ports, 
            bootmem, 
            ruby, 
            cpus0,
            network0,
            ruby.interface0
        )
    
    # Chip 1
    (cpu_sequencers1, dir_cntrls1, topology1) = \
        tgen_CHI.create_chip1(
            options1,
            full_system,
            system,
            dma_ports,
            bootmem,
            ruby,
            cpus1,
            network1,
            ruby.interface1,
            hnf_dests
        )

    # Create the network topology
    topology0.makeTopology(
        options, 
        network0,
        IntLinkClass,
        ExtLinkClass,
        RouterClass
    )

    topology1.makeTopology(
        options1, 
        network1, 
        IntLinkClass, 
        ExtLinkClass, 
        RouterClass
    )

    # In SE register the ropology elements with fake filesystem
    if not full_system:
        topology0.registerTopology(options)
        topology1.registerTopology(options1)

    # Initialize network based topology
    Network.init_network(options, network0, InterfaceClass)
    Network.init_network(options1, network1, InterfaceClass)

    # Create a port proxy for connecting the system port.
    sys_port_proxy = RubyPortProxy(ruby_system=ruby)
    if piobus is not None:
        sys_port_proxy.pio_request_port = piobus.cpu_side_ports
    
    # Give the system port proxy a SimObject parent without creating a
    # full-fledged controller
    system.sys_port_proxy = sys_port_proxy
    
    # Connect the system port for loading of binaries etc
    system.system_port = system.sys_port_proxy.in_ports
    
    setup_memory_controllers(
        system,
        ruby,
        dir_cntrls0,
        dir_cntrls1,
        system.mem_ranges[0],
        system.mem_ranges[1],
        options,
        options1
    )

    # Connect the cpu sequencers and the piobus
    if piobus != None:
        for cpu_seq in cpu_sequencers0:
            cpu_seq.connectIOPorts(piobus)

    # TrafficGen setup
    for i in range(len(cpus0)):
        system.tgens[i].port = cpu_sequencers0[i].in_ports
    
    ruby.number_of_virtual_networks = ruby.network0.number_of_virtual_networks
    ruby._cpu_ports = cpu_sequencers0
    ruby.num_of_sequencers = len(cpu_sequencers0)


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
