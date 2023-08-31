import sys
import os

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.params import NULL
from m5.util import addToPath, fatal, warn
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

from . import ruby_config

addToPath("../")
from common import Options
from common import Simulation
from common import CacheConfig
from common import CpuConfig
from common import ObjectList
from common import MemConfig
from common.FileSystemConfig import config_filesystem
from common.Caches import *
from common.cpu2000 import *

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

cmd = "tests/tests-progs/hello/bin/x86/linux/hello"
multiprocesses, numThreads = get_processes(cmd)

# Number of cpus
np = 2

system = System(
    tgens=[
        TrafficGen(
            config_file="./m5out/lat_mem_rd.cfg",
            progress_check="10s",
        ) for i in range(np)
    ],
    cpus=[AtomicSimpleCPU(cpu_id=i) for i in range(np)],
    mem_mode="atomic",
    mem_ranges=[AddrRange('512MB')],
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

for cpu in system.cpus:
    cpu.clk_domain = system.cpu_clk_domain

for i in range(np):
    if len(multiprocesses) == 1:
        system.cpu[i].workload = multiprocesses[0]
    else:
        system.cpu[i].workload = multiprocesses[i]
    system.cpu[i].createTreads()

class Object(object):
    pass

# Needed options for the create_system method
options = Object()
options.caches = True
options.access_backing_store = False
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

ruby_config.create_system(options, False, system)

system.ruby.clk_domain = SrcClockDomain(
    clock='2GHz', voltage_domain=system.voltage_domain
)
for i in range(np):
    ruby_port = system.ruby._cpu_ports[i]
    # Interrupt controller needs its message port conected only with x86
    system.cpu[i].createInterruptController()
    ruby_port.connectCpuPorts(system.cpu[i])

system.workload = SEWorkload.init_compatible(mp0_path)

wait_gdb = False
if wait_gdb:
    system.workload.wait_for_remote_gdb = True
    
root = Root(full_system=False, system=system)
simulation.run(options, root, system, FutureClass)