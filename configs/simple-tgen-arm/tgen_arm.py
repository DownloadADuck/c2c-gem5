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

multiprocesses = []
numThreads = 1

# Number of cpus
np = 2

system = System(
    tgens=[
        TrafficGen(
            config_file="./m5out/lat_mem_rd.cfg",
            progress_check="10s",
        ) for i in range(np)
    ],
    cpu=[AtomicSimpleCPU(cpu_id=i) for i in range(np)],
    mem_mode="atomic",
    mem_ranges=[AddrRange('512MB')],
    cache_line_size=64
)

if numThreads > 1:
    system.multi_tread = True

# Top level voltage domain
system.voltage_domain = VoltageDomain(voltage='1.0V')

