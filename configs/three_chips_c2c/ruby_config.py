import math
import m5

from m5.objects import *
from m5.defines import buildEnv
from m5.util import addToPath, fatal
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

from three_chips_c2c import chip_config
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
    dir_cntrls2,
    mem_ranges0,
    mem_ranges1,
    mem_ranges2,
    options0,
    options1,
    options2
):
    ruby.block_size_bytes = options0.cacheline_size
    ruby.memory_size_bits = 48

    index = 0
    mem_ctrls0 = []
    mem_ctrls1 = []
    mem_ctrls2 = []
    crossbars = []

    intlv_size = options0.cacheline_size
    
    # Chip-0
    for i, dir_cntrl in enumerate(dir_cntrls0):
        crossbar = None
        mem_type = ObjectList.mem_list.get(options0.mem_type)

        dir_ranges = []
        if i == 1:
            # C2CI-00 -> addr_range[1] -> [200MB:400MB]
            range = m5.objects.AddrRange(
                mem_ranges1.start,
                size=mem_ranges1.size(),
            )
            dir_ranges.append(range)
        elif i == 2:
            # C2CI-01 -> addr_range[2] -> [400MB:600MB]
            range = m5.objects.AddrRange(
                mem_ranges2.start,
                size=mem_ranges2.size(),
            ) 
            dir_ranges.append(range)
        elif i == 0:
            # classic SN
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
        else: 
            pass

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

    # Chip-1
    for i, dir_cntrl in enumerate(dir_cntrls1):
        crossbar = None
        mem_type = ObjectList.mem_list.get(options1.mem_type)
        
        dir_ranges = []
        if i == 1:
            # C2CI-10 -> addr_range[0] -> [0:200MB]
            range = m5.objects.AddrRange(
                mem_ranges0.start,
                size=mem_ranges0.size(),
            )
            dir_ranges.append(range)
        elif i == 2:
            # C2CI-11 -> addr_range[2] -> [400MB:600MB]
            range = m5.objects.AddrRange(
                mem_ranges2.start,
                size=mem_ranges2.size(),
            ) 
            dir_ranges.append(range)
        elif i == 0: 
            # classic SN
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
        else:
            pass

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

    index = 0        

    # Chip-2
    for i, dir_cntrl in enumerate(dir_cntrls2):
        crossbar = None
        mem_type = ObjectList.mem_list.get(options2.mem_type)
        
        dir_ranges = []
        if i == 1:
            # C2CI-20 -> addr_range[0] -> [0:200MB]
            range = m5.objects.AddrRange(
                mem_ranges0.start,
                size=mem_ranges0.size(),
            )
            dir_ranges.append(range)
        elif i == 2:
            # C2CI-21 -> addr_range[1] -> [200MB:400MB]
            range = m5.objects.AddrRange(
                mem_ranges1.start,
                size=mem_ranges1.size(),
            ) 
            dir_ranges.append(range)
        elif i == 0: 
            # classic SN
            mem_type = ObjectList.mem_list.get(options2.mem_type)
            dram_intf = MemConfig.create_mem_intf(
                mem_type,
                mem_ranges2,
                i,
                int(math.log(options2.num_dirs, 2)),
                intlv_size,
                options1.xor_low_bit,
            )

            if issubclass(mem_type, DRAMInterface):
                mem_ctrl = m5.objects.MemCtrl(dram=dram_intf)
            else: 
                mem_ctrl = dram_intf
                
            mem_ctrls2.append(mem_ctrl)
            dir_ranges.append(dram_intf.range)

        if crossbar != None:
            mem_ctrl.port = crossbar.mem_side_ports
        else:
            if i == 0:
                mem_ctrl.port = dir_cntrl.memory_out_port

            # Enable low-power DRAM states if option is enabled
            if issubclass(mem_type, DRAMInterface):
                mem_ctrl.dram.enable_dram_powerdown = (
                    options2.enable_dram_powerdown
                )
        index += 1
        dir_cntrl.addr_ranges = dir_ranges

    system.mem_ctrls0 = mem_ctrls0
    system.mem_ctrls1 = mem_ctrls1
    system.mem_ctrls2 = mem_ctrls2
    
    if len(crossbars) > 0:
        ruby.crossbars = crossbars

def create_topology(controllers, options):
    exec("import topologies.%s as Topo" % options.topology)
    topology = eval("Topo.%s(controllers)" % options.topology)
    return topology

def create_system(
    options,
    options1,
    options2,
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
    # Chip 1
    (
        network1,
        IntLinkClass,
        ExtLinkClass,
        RouterClass,
        InterfaceClass,
    ) = Network.create_network(options1, ruby)
    ruby.network1 = network1
    
    # Chip 2
    (
        network2,
        IntLinkClass,
        ExtLinkClass,
        RouterClass,
        InterfaceClass,
    ) = Network.create_network(options2, ruby)
    ruby.network2 = network2

    if cpus is None:
        cpus0 = system.cpus0
        cpus1 = system.cpus1
        cpus2 = system.cpus2
    
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

    # Chip 2
    (cpu_sequencers2, dir_cntrls2, topology2) = \
        chip_config.create_chip2(
            options2,
            full_system,
            system,
            dma_ports,
            bootmem,
            ruby,
            cpus2,
            network2
        )

    # Create the network topology
    # Chip 0
    topology0.makeTopology(
        options, 
        network0,
        IntLinkClass,
        ExtLinkClass,
        RouterClass
    )

    # Chip 1
    topology1.makeTopology(
        options1, 
        network1, 
        IntLinkClass, 
        ExtLinkClass, 
        RouterClass
    )

    # Chip 2
    topology2.makeTopology(
        options2, 
        network2, 
        IntLinkClass, 
        ExtLinkClass, 
        RouterClass
    )

    # C2C forwarding interface setup
    #for interface1 in system.ruby.interface1:
    #    for interface0 in system.ruby.interface0:
    #        interface0.cntrl.c2c_out_port = interface1.cntrl.c2c_in_port
    #        interface0.cntrl.c2c_in_port = interface1.cntrl.c2c_out_port
    c2ci0 = system.ruby.interface0
    c2ci1 = system.ruby.interface1
    c2ci2 = system.ruby.interface2
    # c2ci0 <-> c2ci1
    c2ci0[0].cntrl.c2c_out_port = c2ci1[0].cntrl.c2c_in_port
    c2ci1[0].cntrl.c2c_out_port = c2ci0[0].cntrl.c2c_in_port
    # c2ci0 <-> c2ci2
    c2ci0[1].cntrl.c2c_out_port = c2ci2[0].cntrl.c2c_in_port
    c2ci2[0].cntrl.c2c_out_port = c2ci0[1].cntrl.c2c_in_port
    # c2ci1 <-> c2ci2
    c2ci1[1].cntrl.c2c_out_port = c2ci2[1].cntrl.c2c_in_port
    c2ci2[1].cntrl.c2c_out_port = c2ci1[1].cntrl.c2c_in_port

    # In SE register the ropology elements with fake filesystem
    if not full_system:
        topology0.registerTopology(options)
        topology1.registerTopology(options1)
        topology2.registerTopology(options2)

    # Initialize network based topology
    Network.init_network(options, network0, InterfaceClass)
    Network.init_network(options1, network1, InterfaceClass)
    Network.init_network(options2, network2, InterfaceClass)

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
        dir_cntrls2,
        system.mem_ranges[0],
        system.mem_ranges[1],
        system.mem_ranges[2],
        options,
        options1,
        options2
    )

    # Connect the cpu sequencers and the piobus
    if piobus != None:
        for cpu_seq in cpu_sequencers0:
            cpu_seq.connectIOPorts(piobus)
        for cpu_seq in cpu_sequencers1:
            cpu_seq.connectIOPorts(piobus)
        for cpu_seq in cpu_sequencers2:
            cpu_seq.connectIOPorts(piobus)

    # TrafficGen setup
    for i in range(len(cpus0)):
        system.tgens0[i].port = cpu_sequencers0[i].in_ports

    for i in range(len(cpus1)):
        system.tgens1[i].port = cpu_sequencers1[i].in_ports

    for i in range(len(cpus2)):
        system.tgens2[i].port = cpu_sequencers2[i].in_ports
    
    ruby.number_of_virtual_networks = ruby.network0.number_of_virtual_networks
    ruby._cpu_ports = cpu_sequencers0 + cpu_sequencers1 + cpu_sequencers2
    ruby.num_of_sequencers = len(cpu_sequencers0) + len(cpu_sequencers1) + len(cpu_sequencers2)


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
