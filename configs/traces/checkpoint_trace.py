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
parser.add_argument("--log-file", type=str, required=True, help="Path to the log file")
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
    default="16MB",
    help="Specify the memory size",
)
parser.add_argument(
    "--reuse-trace",
    action="store_true",
    help="Prevent generation of traces and reuse existing",
)

args = parser.parse_args()

def is_pow2(num):
    return num != 0 and ((num & (num - 1)) == 0)

def create_trace(filename, packets, burst_size, itt):
    try:
        proto_out = gzip.open(filename, "wb")
    except IOError:
        print("Failed to open ", filename, " for writing")
        exit(-1)

    proto_out.write(b'gem5')

    header = packet_pb2.PacketHeader()
    header.obj_id = "lat_mem_rd trace"
    header.tick_freq = 1000000000000
    protolib.encodeMessage(proto_out, header)

    tick = 0
    for packet_info in packets:
        packet = packet_pb2.Packet()
        packet.tick = packet_info['tick']
        packet.addr = packet_info['addr']
        packet.size = packet_info['size']
        packet.cmd = packet_info['cmd']
        print(f"flags: {packet.request}")
        #if packet_info['isInstFetch']:
            #packet.flags. = True
        

        print(f"Packet - Tick: {packet.tick}, Address: {packet.addr}, \
            Size: {packet.size}, Command: {packet.cmd}, isInstFetch: \
            {packet.req.isInstFetch}")

        protolib.encodeMessage(proto_out, packet)
        tick += itt

    proto_out.close()

def parse_log_file(log_file):
    packets_core0 = []
    packets_core1 = []
    with open(log_file, 'r') as file:
        lines = file.readlines()
        for i in range(0, len(lines), 6):
            tick = int(lines[i].split(':')[0])
            core_cluster = lines[i].split(':')[1].split('.')[2]
            addr = int(lines[i + 1].split(':')[1])
            size = int(lines[i + 2].split(':')[1])
            packet_type = lines[i + 5].split(':')[1].strip()
            isInstFetch = bool(False)

            if packet_type == "IFETCH":
                cmd = 1  # ReadReq
                isInstFetch = True
            elif packet_type == "LD":
                cmd = 1 # ReadReq
            elif packet_type == "ST":
                cmd = 4 # WriteReq
            else:
                raise RuntimeError(f"Error parsing command for Addr: {addr}")

            packet_info = {
                'tick': tick,
                'addr': addr,
                'size': size,
                'cmd': cmd,
                'isInstFetch': isInstFetch
            }

            if core_cluster == 'core_cluster0':
                packets_core0.append(packet_info)
            else:
                packets_core1.append(packet_info)

    return packets_core0, packets_core1

packets_core0, packets_core1 = parse_log_file(args.log_file)

trace_file_core0 = os.path.join(m5.options.outdir, "lat_mem_rd_core0.trc.gz")
trace_file_core1 = os.path.join(m5.options.outdir, "lat_mem_rd_core1.trc.gz")

itt = 150 * 1000  # 150 ns in ticks
burst_size = 64

create_trace(trace_file_core0, packets_core0, burst_size, itt)
create_trace(trace_file_core1, packets_core1, burst_size, itt)

print("Generated trace files:", trace_file_core0, trace_file_core1)

system = System(membus=SystemXBar(width=32))
system.clk_domain = SrcClockDomain(
    clock="2.0GHz", voltage_domain=VoltageDomain(voltage="1V")
)

mem_range = AddrRange(args.mem_size)
system.mem_ranges = [mem_range]
system.mmap_using_noreserve = True

args.mem_channels = 1
args.mem_ranks = 1
args.external_memory_system = 0
args.tlm_memory = 0
args.elastic_trace_en = 0

MemConfig.config_mem(args, system)

cfg_file_name = os.path.join(m5.options.outdir, "lat_mem_rd.cfg")
cfg_file = open(cfg_file_name, "w")
system.cache_line_size = burst_size

#ranges = [1024, 2048, 4096, 8192, 16384]
iterations = 0
period = int(itt * (16384 / burst_size))

nxt_range = 0
nxt_state = 0

#for r in ranges:
filename_core0 = os.path.join(m5.options.outdir, "lat_mem_rd_core0_%d.trc.gz" % nxt_range)
filename_core1 = os.path.join(m5.options.outdir, "lat_mem_rd_core1_%d.trc.gz" % nxt_range)
    
if not args.reuse_trace:
    create_trace(filename_core0, packets_core0, burst_size, itt)
    create_trace(filename_core1, packets_core1, burst_size, itt)

cfg_file.write("STATE %d %d TRACE %s 0\n" % (nxt_state, period, filename_core0))
nxt_state += 1

cfg_file.write("STATE %d %d TRACE %s 0\n" % (nxt_state, period, filename_core1))
nxt_state += 1

for i in range(iterations):
    cfg_file.write("STATE %d %d TRACE %s 0\n" % (nxt_state, period, filename_core0))
    nxt_state += 1

    cfg_file.write("STATE %d %d TRACE %s 0\n" % (nxt_state, period, filename_core1))
    nxt_state += 1

nxt_range += 1

cfg_file.write("INIT 0\n")

for state in range(1, nxt_state):
    cfg_file.write("TRANSITION %d %d 1\n" % (state - 1, state))

cfg_file.write("TRANSITION %d %d 1\n" % (nxt_state - 1, nxt_state - 1))
cfg_file.close()

system.tgen = TrafficGen(config_file=cfg_file_name, progress_check="10s")
system.system_port = system.membus.cpu_side_ports

periodicStatDump(period)

root = Root(full_system=False, system=system)
root.system.mem_mode = "timing"

m5.instantiate()
m5.simulate(nxt_state * period)

print("lat_mem_rd with %d iterations, ranges:" % iterations)
for r in ranges:
    print(r)

