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
from three_chips_c2c import ruby_config
import options

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
        #TrafficGen(
        #    #config_file="./m5out/lat_mem_rd_2.cfg",
        #    config_file="./m5out/threads_2.cfg",
        #    progress_check="10s",
        #),
    ],
    tgens1=[
        TrafficGen(
            #config_file="./m5out/lat_mem_rd_3.cfg",
            config_file="./m5out/threads_3.cfg",
            progress_check="10s",
        ),
    ],
    tgens2=[
        TrafficGen(
            config_file="./m5out/threads_3.cfg",
            progress_check="10s",
        ),
    ],
    #cpus0=[CPUClass(cpu_id=0), CPUClass(cpu_id=1)],
    cpus0=[CPUClass(cpu_id=0)],
    cpus1=[CPUClass(cpu_id=1)],
    cpus2=[CPUClass(cpu_id=2)],
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

for cpu in system.cpus2:
    cpu.clk_domain = system.cpu_clk_domain

if len(multiprocesses) == 1:
    system.cpus0[0].workload = multiprocesses[0]
    system.cpus1[0].workload = multiprocesses[0]
    system.cpus2[0].workload = multiprocesses[0]
else:
    system.cpus0[0].workload = multiprocesses[0]
    system.cpus1[0].workload = multiprocesses[1]
    system.cpus2[0].workload = multiprocesses[0]
system.cpus0[0].createThreads()
system.cpus1[0].createThreads()
system.cpus2[0].createThreads()



ruby_config.create_system(options0, options1, options2, False, system)

system.ruby.clk_domain = SrcClockDomain(
    clock='2GHz', voltage_domain=system.voltage_domain
)

ruby_port = system.ruby._cpu_ports[0]
ruby_port = system.ruby._cpu_ports[1]
ruby_port = system.ruby._cpu_ports[2]
system.cpus0[0].createInterruptController()
system.cpus1[0].createInterruptController()
system.cpus2[0].createInterruptController()
ruby_port.connectCpuPorts(system.cpus0[0])
ruby_port.connectCpuPorts(system.cpus1[0])
ruby_port.connectCpuPorts(system.cpus2[0])


system.workload = SEWorkload.init_compatible(mp0_path)

wait_gdb = False
if wait_gdb:
    system.workload.wait_for_remote_gdb = True
    
root = Root(full_system=False, system=system)
Simulation.run(options0, root, system, FutureClass)
