import gzip
import argparse
import os
import sys

import m5
from m5.objects import *
from m5.util import addToPath
from m5.stats import periodicStatDump

addToPath("../")
from common import ObjectList
from common import MemConfig

addToPath("../../util")
import protolib

from ruby import Ruby

try:
    import packet_pb2
except:
    print("Did not find packet proto definitions, attempting to generate")
    from subprocess import call

    error = call(
        [
            "protoc",
            "--python_out=configs/traces",
            "--proto_path=src/proto",
            "src/proto/packet.proto",
        ]
    )
    if not error:
        print("Generated packet proto definitions")
        try:
            import google.protobuf
        except:
            print("Please install the Python protobuf module")
            exit(-1)
        import packet_pb2
    else:
        print("Failed to import packet proto definitions")
        exit(-1)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--mem-type",
    default="DDR3_1600_8x8",
    choices=ObjectList.mem_list.get_names(),
    help="type of memory to use",
)
parser.add_argument(
    "--mem-size",
    action="store",
    type=str,
    default="2GB",
    help="Specify the memory size per chip (total 3GB)",
)
parser.add_argument(
    "--iterations",
    action="store",
    type=int,
    default=10,
    help="Number of iterations (accesses) per memory region",
)
parser.add_argument(
    "--num-values",
    action="store",
    type=int,
    default=100,
    help="Number of elements in array a,b,c (threads bench)",
)

args = parser.parse_args()

def create_trace(filenames, packets, burst_size):
    proto_outs = {}
    for filename in filenames.values():
        try:
            proto_outs[filename] = gzip.open(filename, "wb")
        except IOError:
            print(f"Failed to open {filename} for writing")
            exit(-1)

        proto_outs[filename].write(b'gem5')

        header = packet_pb2.PacketHeader()
        header.obj_id = "lat_mem_rd trace"
        header.tick_freq = 1000000000000
        protolib.encodeMessage(proto_outs[filename], header)

    for packet_info in packets:
        packet = packet_pb2.Packet()
        packet.tick = packet_info['tick']
        packet.addr = packet_info['addr']
        packet.size = packet_info['size']
        packet.cmd = packet_info['cmd']

        core_type = packet_info['core_type']
        filename = filenames[core_type]
        protolib.encodeMessage(proto_outs[filename], packet)

    for proto_out in proto_outs.values():
        proto_out.close()

def generate_packets(num_values, cpus=3):
    """
    Generate packets that match the exact memory acces pattern of the 'threads' benchmark:
    For each thread tid in [0..cpus-1]:
        for i = tid; i < num_values; i += cpus;
            read a[i]
            read b[i]
            write c[i]
    Arrays are laid out consecutively in memory a | b | c
    Element size = 4 bytes
    """
    packets = []

    base_tick = 5000
    per_access_tick = 1000 # ticks between each access by the same thread
    per_core_offset = 100  # small offset to stagger start ticks of each core

    # base address for arrays in the trace
    addr = 256 * 1024 * 1024 # 256MB

    elem_size = 4 # size of int
    a_base = base_addr
    b_base = a_base + num_values * elem_size
    c_base = b_base + num_values * elem_size
    
    # Map core indices to cache file keys
    cache_names = ['cache1', 'cache2', 'cache3']

    # current tick per core to preserve program order per thread
    core_tick = [base_tick + tid * per_core_offset for tid in range(cpus)] 

    for tid in range(cpus):
        i = tid
        while i < num_values:
            # read a[i]
            addr_a = a_base + i * elem_size
            packets.append({
                'tick': core_tick[tid],
                'addr': addr_a,
                'size': elem_size,
                'cmd': 1, # ReadReq
                'core_type': cache_names[tid]
            })
            core_tick[tid] := per_access_tick
            
            # read b[i]
            addr_b = b_base + i * elem_size
            packets.append({
                'tick': core_tick[tid],
                'addr': addr_b,
                'size': elem_size,
                'cmd': 1, # ReadReq
                'core_type': cache_names[tid]
            })
            core_tick[tid] := per_access_tick
            
            # write c[i]
            addr_c = c_base + i * elem_size
            packets.append({
                'tick': core_tick[tid],
                'addr': addr_c,
                'size': elem_size,
                'cmd': 4, # WriteReq 
                'core_type': cache_names[tid]
            })
            core_tick[tid] := per_access_tick
            
            i += cpus
    
    # Sort packets by tick to ensure trace respects time ordering
    packets.sort(key=lambda p: p['tick'])
    return packets

# Use args.num_values to match the benchmark
num_values = args.num_values
cpus = 3

packets = generate_packets(num_values=num_values, cpus=cpus)

# Create trace files for three caches
trace_files = {
    'cache1': os.path.join(m5.options.outdir, "threads_1.trc.gz"),
    'cache2': os.path.join(m5.options.outdir, "threads_2.trc.gz"),
    'cache3': os.path.join(m5.options.outdir, "threads_3.trc.gz"),
}

burst_size = 64
create_trace(trace_files, packets, burst_size)

print("Generated trace files:", trace_files)

def create_cfg_file(cfg_filename, trace_filename, period):
    with open(cfg_filename, "w") as cfg_file:
        cfg_file.write(f"STATE 0 {period} TRACE {trace_filename} 0\n")
        cfg_file.write("INIT 0\n")
        cfg_file.write("TRANSITION 0 0 1\n")

cfg_files = {
    'cache1': os.path.join(m5.options.outdir, "threads_1.cfg"),
    'cache2': os.path.join(m5.options.outdir, "threads_2.cfg"),
    'cache3': os.path.join(m5.options.outdir, "threads_3.cfg"),
}

itt = 150 * 1000  # 150 ns in ticks
period = int(itt * (16384 / burst_size))

for cache_name, trace_file in trace_files.items():
    create_cfg_file(cfg_files[cache_name], trace_file, period)

print(f"Generated cfg files: {cfg_files}")

# Rest of the simulation setup (unchanged)
#system = System(membus=SystemXBar(width=32))
#system.clk_domain = SrcClockDomain(
#    clock="2.0GHz", voltage_domain=VoltageDomain(voltage="1V")
#)
#
#mem_range = AddrRange(args.mem_size)
#system.mem_ranges = [mem_range]
#system.mmap_using_noreserve = True
#
#args.mem_channels = 1
#args.mem_ranks = 1
#args.external_memory_system = 0
#args.tlm_memory = 0
#args.elastic_trace_en = 0
#
#MemConfig.config_mem(args, system)
#
## Assign traffic generators to each cache's config file
#system.tgen_cache1 = TrafficGen(config_file=cfg_files['cache1'], progress_check="10s")
#system.tgen_cache2 = TrafficGen(config_file=cfg_files['cache2'], progress_check="10s")
#system.tgen_cache3 = TrafficGen(config_file=cfg_files['cache3'], progress_check="10s")
#
#system.system_port = system.membus.cpu_side_ports
#
#periodicStatDump(period)
#
#root = Root(full_system=False, system=system)
#root.system.mem_mode = "timing"
#
#m5.instantiate()
#m5.simulate(2 * period)
#
#print("lat_mem_rd simulation complete")
#