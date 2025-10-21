import sys
import os

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.params import NULL
from m5.util import *
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

addToPath("../")
from four_tgens_se_c2c import ruby_config

from common import Options
from common import Simulation
from common import CacheConfig
from common import CpuConfig
from common import ObjectList
from common import MemConfig
from common.FileSystemConfig import config_filesystem
from common.Caches import *
from common.cpu2000 import *

class Object(object):
    pass

# Needed options0 for the create_system method
options0 = Object()
options0.cmd = "tests/test-progs/infinite-loop/bin/infinite_loop"
options0.input = ''
options0.output = ''
options0.errout = '' 
options0.options0 = ''
options0.env = ''
options0.caches = True
options0.cache_line_size = 64
options0.num_dirs = 1
options0.xor_low_bit = 20
options0.enable_dram_powerdown = False
options0.access_backing_store = False
options0.mem_type = 'DDR3_1600_8x8'
options0.topology = 'Pt2Pt'
options0.link_latency = 1
options0.router_latency = 1
options0.outdir = "/m5out"
options0.cpu_clock = '2GHz'
options0.network = 'simple'
options0.simple_physical_channels = False
options0.repeat_switch = None
options0.take_checkpoints = None
options0.smt = False
options0.cpu_type = 'TimingSimpleCPU'
options0.checkpoint_restore = None
options0.fast_forward = None
options0.num_l3caches = 1
options0.chi_config = None
options0.l1i_size = '64kB'
options0.l1i_assoc = 4
options0.l1d_size = '64kB'
options0.l1d_assoc = 4
options0.l2_size = '1MB'
options0.l2_assoc = 8
options0.l3_size = '128'
options0.l3_assoc = 1
options0.cacheline_size = 64
options0.num_cpus = 2
options0.network_fault_model = False
options0.checkpoint_dir = None
options0.standard_switch = None
options0.stats_root = []
options0.prog_interval = None
options0.maxinsts = None
options0.override_vendor_string = None
options0.take_simpoint_checkpoints = None
options0.param = []
options0.initialize_only = False
options0.abs_max_tick = 18446744073709551615
options0.rel_max_tick = None
options0.maxtime = None
options0.restore_simpoint_checkpoint = False
options0.max_checkpoints = 5
options0.checkpoint_at_end = False
options0.num_interfaces = 1
options0.abs_max_tick = 3001400000

options1 = Object()
options1.cmd = "tests/test-progs/infinite-loop/bin/infinite_loop"
options1.input = ''
options1.output = ''
options1.errout = '' 
options1.options0 = ''
options1.env = ''
options1.caches = False
options1.cache_line_size = 64
options1.num_dirs = 1
options1.xor_low_bit = 20
options1.enable_dram_powerdown = False
options1.access_backing_store = False
options1.mem_type = 'DDR3_1600_8x8'
options1.topology = 'Pt2Pt'
options1.link_latency = 1
options1.router_latency = 1
options1.outdir = "/m5out"
options1.cpu_clock = '2GHz'
options1.network = 'simple'
options1.simple_physical_channels = False
options1.repeat_switch = None
options1.take_checkpoints = None
options1.smt = False
options1.cpu_type = 'TimingSimpleCPU'
options1.checkpoint_restore = None
options1.fast_forward = None
options1.num_l3caches = 1
options1.chi_config = None
options1.l1i_size = '64kB'
options1.l1i_assoc = 4
options1.l1d_size = '64kB'
options1.l1d_assoc = 4
options1.l2_size = '1MB'
options1.l2_assoc = 8
options1.l3_size = '1MB'
options1.l3_assoc = 16
options1.cacheline_size = 64
options1.num_cpus = 1
options1.network_fault_model = False
options1.checkpoint_dir = None
options1.standard_switch = None
options1.stats_root = []
options1.prog_interval = None
options1.maxinsts = None
options1.override_vendor_string = None
options1.take_simpoint_checkpoints = None
options1.param = []
options1.initialize_only = False
options1.abs_max_tick = 18446744073709551615
options1.rel_max_tick = None
options1.maxtime = None
options1.restore_simpoint_checkpoint = False
options1.max_checkpoints = 5
options1.checkpoint_at_end = False
options1.num_interfaces = 1

def get_processes(args):
    """Interprets provided args and returns a list of processes"""

    multiprocesses = []
    inputs = []
    outputs = []
    errouts = []
    pargs = []

    workloads = args.cmd.split(";")
    if args.input != "":
        inputs = args.input.split(";")
    if args.output != "":
        outputs = args.output.split(";")
    if args.errout != "":
        errouts = args.errout.split(";")
    if args.options0 != "":
        pargs = args.options0.split(";")

    idx = 0
    for wrkld in workloads:
        process = Process(pid=100 + idx)
        process.executable = wrkld
        process.cwd = os.getcwd()
        process.gid = os.getgid()

        if args.env:
            with open(args.env, "r") as f:
                process.env = [line.rstrip() for line in f]

        if len(pargs) > idx:
            process.cmd = [wrkld] + pargs[idx].split()
        else:
            process.cmd = [wrkld]

        if len(inputs) > idx:
            process.input = inputs[idx]
        if len(outputs) > idx:
            process.output = outputs[idx]
        if len(errouts) > idx:
            process.errout = errouts[idx]

        multiprocesses.append(process)
        idx += 1

    if args.smt:
        assert args.cpu_type == "DerivO3CPU"
        return multiprocesses, idx
    else:
        return multiprocesses, 1

multiprocesses = []
numThreads = 1

multiprocesses, numThreads = get_processes(options0)
(CPUClass, test_mem_mode, FutureClass) = Simulation.setCPUClass(options0)
CPUClass.numThreads = numThreads

# Number of cpus
np = options0.num_cpus
mp0_path = multiprocesses[0].executable

# Memory ranges
#arv = convert.toMemorySize('1610612736')
arv = convert.toMemorySize('200MB')
addr_range_vaults = [AddrRange(i*arv, ((i+1)*arv-1)) for i in range(2)]

system = System(
    tgens0=[
        TrafficGen(
            #config_file="./m5out/lat_mem_rd_1.cfg",
            config_file="./m5out/threads_1.cfg",
            progress_check="10s",
        ),
        TrafficGen(
            #config_file="./m5out/lat_mem_rd_2.cfg",
            config_file="./m5out/threads_2.cfg",
            progress_check="10s",
        ),
    ],
    tgens1=[
        TrafficGen(
            #config_file="./m5out/lat_mem_rd_3.cfg",
            config_file="./m5out/threads_3.cfg",
            progress_check="10s",
        ),
    ],
    cpus0=[CPUClass(cpu_id=0), CPUClass(cpu_id=1)],
    cpus1=[CPUClass(cpu_id=2)],
    mem_mode="timing",
    mem_ranges=addr_range_vaults,
    cache_line_size=64
)

if numThreads > 1:
    system.multi_tread = True

# Top level voltage domain
system.voltage_domain = VoltageDomain(voltage='1.0V')

# Source clock for the system
system.clk_domain = SrcClockDomain(
    clock='1GHz', voltage_domain=system.voltage_domain
)

# CPU voltage domain
system.cpu_voltage_domain = VoltageDomain()

# Separate CPU clock domain
system.cpu_clk_domain = SrcClockDomain(
    clock='2GHz', voltage_domain=system.cpu_voltage_domain
)

for cpu in system.cpus0:
    cpu.clk_domain = system.cpu_clk_domain

for cpu in system.cpus1:
    cpu.clk_domain = system.cpu_clk_domain

#for i in range(np):
#    if len(multiprocesses) == 1:
#        system.cpus0[i].workload = multiprocesses[0]
#        system.cpus1[i].workload = multiprocesses[0]
#    else:
#        system.cpus0[i].workload = multiprocesses[i]
#        system.cpus1[i].workload = multiprocesses[i]
#    system.cpus0[i].createThreads()
#    system.cpus1[i].createThreads()

if len(multiprocesses) == 1:
    system.cpus0[0].workload = multiprocesses[0]
    system.cpus0[1].workload = multiprocesses[0]
    system.cpus1[0].workload = multiprocesses[0]
else:
    system.cpus0[0].workload = multiprocesses[0]
    system.cpus0[1].workload = multiprocesses[1]
    system.cpus1[0].workload = multiprocesses[0]
system.cpus0[0].createThreads()
system.cpus0[1].createThreads()
system.cpus1[0].createThreads()



ruby_config.create_system(options0, options1, False, system)

system.ruby.clk_domain = SrcClockDomain(
    clock='2GHz', voltage_domain=system.voltage_domain
)
#for i in range(np):
#    ruby_port = system.ruby._cpu_ports[i]
#    # Interrupt controller needs its message port conected only with x86
#    system.cpus0[i].createInterruptController()
#    system.cpus1[i].createInterruptController()
#    ruby_port.connectCpuPorts(system.cpus0[i])
#    ruby_port.connectCpuPorts(system.cpus1[i])

ruby_port = system.ruby._cpu_ports[0]
ruby_port = system.ruby._cpu_ports[1]
system.cpus0[0].createInterruptController()
system.cpus0[1].createInterruptController()
system.cpus1[0].createInterruptController()
ruby_port.connectCpuPorts(system.cpus0[0])
ruby_port.connectCpuPorts(system.cpus0[1])
ruby_port.connectCpuPorts(system.cpus1[0])


system.workload = SEWorkload.init_compatible(mp0_path)

wait_gdb = False
if wait_gdb:
    system.workload.wait_for_remote_gdb = True
    
root = Root(full_system=False, system=system)
Simulation.run(options0, root, system, FutureClass)
