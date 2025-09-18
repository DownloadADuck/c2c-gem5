import math
import m5

from m5.objects import *
from m5.defines import buildEnv
from m5.util import addToPath, fatal
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

from three_rnf_threads_c2c import chip_config
from CHI_config import MemCtrlMessageBuffer

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

    for i, dir_cntrl in enumerate(dir_cntrls0):
        crossbar = None

        dir_ranges = []
        #for mem_range in mem_ranges0:
        if i != 0:
            mem_type = ObjectList.mem_list.get(options0.mem_type)
            range = m5.objects.AddrRange(
                mem_ranges1.start,
                size=mem_ranges1.size(),
            )

            dir_ranges.append(range)
        else:
            # classic SN
            mem_type = ObjectList.mem_list.get(options0.mem_type)
            dram_intf = MemConfig.create_mem_intf(
                mem_type,
                mem_ranges0,
                i,
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
            if i == 0:
                # classic SN
                mem_ctrl.port = dir_cntrl.memory_out_port

                # Enable low-power DRAM states if option is enabled
                if issubclass(mem_type, DRAMInterface):
                    mem_ctrl.dram.enable_dram_powerdown = (
                        options0.enable_dram_powerdown
                    )
        index += 1
        dir_cntrl.addr_ranges = dir_ranges

    index = 0

    for i, dir_cntrl in enumerate(dir_cntrls1):
        crossbar = None
        
        dir_ranges = []
        #for mem_range in mem_ranges1:
        if i != 0:
            # C2C Interface
            mem_type = ObjectList.mem_list.get(options1.mem_type)
            range = m5.objects.AddrRange(
                mem_ranges0.start,
                size=mem_ranges0.size(),
            )

            dir_ranges.append(range)
        else: 
            # classic SN
            mem_type = ObjectList.mem_list.get(options1.mem_type)
            dram_intf = MemConfig.create_mem_intf(
                mem_type,
                mem_ranges1,
                i,
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
            if i == 0:
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
        cpus0 = system.cpus0
        cpus1 = system.cpus1
    
    # Chip 0
    (cpu_sequencers0, dir_cntrls0, topology0) = \
        chip_config.create_chip0(
            options, 
            full_system, 
            system, 
            dma_ports, 
            bootmem, 
            ruby, 
            cpus0,
            network0
        )
    
    # Chip 1
    (cpu_sequencers1, dir_cntrls1, topology1) = \
        chip_config.create_chip1(
            options1,
            full_system,
            system,
            dma_ports,
            bootmem,
            ruby,
            cpus1,
            network1
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

    # C2C forwarding interface setup
    for interface in system.ruby.interface1:
        for interface0 in system.ruby.interface0:
            interface0.cntrl.c2c_out_port = interface.cntrl.c2c_in_port
            interface0.cntrl.c2c_in_port = interface.cntrl.c2c_out_port

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
