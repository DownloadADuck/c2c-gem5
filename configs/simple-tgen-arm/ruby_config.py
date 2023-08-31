import math
import m5

from m5.objects import *
from m5.defines import buildEnv
from m5.util import addToPath, fatal
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

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

    for dir_cntrl in dir_cntrls:
        crossbar = None
        if len(system.mem_ranges) > 1:
            crossbar = IOXBar()
            crossbars.append(crossbar)
            dir_cntrl.memory_out_ports = crossbar.cpu_side_ports
        
        dir_ranges = []
        for r in system.mem_ranges:
            mem_type = ObjectList.mem_list.get(options.mem_type)
            dram_intf = MemConfig.create_mem_intf(
                mem_type,
                r,
                index,
                int(math.log(options.num_dirs, 2)),
                intlv_size,
                options.xor_low_bit,
            )
            if issubclass(mem_type, DRAMInterface):
                mem_ctrl = m5.objects.MemCtrl(dram=dram_intf)
            else: 
                mem_ctrl = dram_intf
            
            mem_ctrls.append(mem_ctrl)
            dir_ranges.append(dram_intf.range)

            if crossbar != None:
                mem_ctrl.port = crossbar.mem_side_ports
            else:
                mem_ctrl.port = dir_cntrl.mem_out_port
            # Enable low-power DRAM states if option is enabled
            if issubclass(mem_type, DRAMInterface):
                mem_ctrl.dram.enable_dram_powerdown = (
                    options.enable_dram_powerdown
                )
        index += 1
        dir_cntrl.addr_rages = dir_ranges
    system.mem_ctrls = mem_ctrls
    
    if len(crossbar) > 0:
        ruby.crossbars = crossbars

def create_topology(controllers, options):
    exec("import topologies.%s as Topo" % options.topology)
    topology = eval("Topo.%s(controllers)" % options.topology)
    return topology

