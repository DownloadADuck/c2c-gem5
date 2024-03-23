import sys
import os

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.params import NULL
from m5.util import addToPath, fatal, warn
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

#from ruby_config import *

addToPath("../")
from simple_tgen_arm import ruby_config

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

# Needed options for the create_system method
options = Object()
options.cmd = "tests/test-progs/hello/bin/x86/linux/hello"
options.input = ''
options.output = ''
options.errout = '' 
options.options = ''
options.env = ''
options.caches = True
options.cache_line_size = 64
options.num_dirs = 1
options.xor_low_bit = 20
options.enable_dram_powerdown = False
options.access_backing_store = False
options.mem_type = 'DDR3_1600_8x8'
options.topology = 'Pt2Pt'
options.link_latency = 1
options.router_latency = 1
options.outdir = "/m5out"
options.cpu_clock = '2GHz'
options.l2_size = '2MB'
options.network = 'simple'
options.simple_physical_channels = False
options.repeat_switch = None
options.take_checkpoints = None
options.smt = False
options.cpu_type = 'TimingSimpleCPU'
options.checkpoint_restore = None
options.fast_forward = None
options.num_l3caches = 1
options.chi_config = None
options.l1i_size = '32kB'
options.l1i_assoc = 2
options.l1d_size = '64kB'
options.l1d_assoc = 2
options.l2_assoc = 8
options.l3_size = '32kB'
options.l3_assoc = 16
options.cacheline_size = 64
options.num_cpus = 2
options.network_fault_model = False
options.checkpoint_dir = None
options.standard_switch = None
options.stats_root = []
options.prog_interval = None
options.maxinsts = None
options.override_vendor_string = None
options.take_simpoint_checkpoints = None
options.param = []
options.initialize_only = False
options.abs_max_tick = 18446744073709551615
options.rel_max_tick = None
options.maxtime = None
options.restore_simpoint_checkpoint = False
options.max_checkpoints = 5
options.checkpoint_at_end = False

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
    if args.options != "":
        pargs = args.options.split(";")

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

multiprocesses, numThreads = get_processes(options)
(CPUClass, test_mem_mode, FutureClass) = Simulation.setCPUClass(options)
CPUClass.numThreads = numThreads

# Number of cpus
np = options.num_cpus
mp0_path = multiprocesses[0].executable

system = System(
    tgens=[
        TrafficGen(
            config_file="./m5out/lat_mem_rd.cfg",
            progress_check="10s",
        ),
        TrafficGen(
            config_file="./m5out/lat_mem_rd.cfg",
            progress_check="10s",
        )
    ],
    cpus=[CPUClass(cpu_id=i) for i in range(np)],
    mem_mode="timing",
    mem_ranges=[AddrRange('4MB')],
    cache_line_size=64
)

print(system.tgens)

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

for cpu in system.cpus:
    cpu.clk_domain = system.cpu_clk_domain

for i in range(np):
    if len(multiprocesses) == 1:
        system.cpus[i].workload = multiprocesses[0]
    else:
        system.cpus[i].workload = multiprocesses[i]
    system.cpus[i].createThreads()


ruby_config.create_system(options, False, system)

system.ruby.clk_domain = SrcClockDomain(
    clock='2GHz', voltage_domain=system.voltage_domain
)
for i in range(np):
    ruby_port = system.ruby._cpu_ports[i]
    # Interrupt controller needs its message port conected only with x86
    system.cpus[i].createInterruptController()
    ruby_port.connectCpuPorts(system.cpus[i])

system.workload = SEWorkload.init_compatible(mp0_path)

wait_gdb = False
if wait_gdb:
    system.workload.wait_for_remote_gdb = True
    
root = Root(full_system=False, system=system)
Simulation.run(options, root, system, FutureClass)