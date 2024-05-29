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

    base_tick = 5000
    tick = base_tick

    for i, packet_info in enumerate(packets):
        if i > 0:
            tick += packet_info['tick'] - packets[i - 1]['tick']
        
        packet = packet_pb2.Packet()
        packet.tick = tick
        packet.addr = packet_info['addr']
        packet.size = packet_info['size']
        packet.cmd = packet_info['cmd']
        if packet.cmd == 61:
            print(f"Ifetch packet @ address: {packet.addr}")

        core_type = packet_info['core_type']
        filename = filenames[core_type]
        protolib.encodeMessage(proto_outs[filename], packet)
        print(f"Encoding packet tick: {packet.tick}")
        print(f"cmd: {packet.cmd}")
        print(f"addr: {packet.addr}")
        print(f"size: {packet.size}")
        print(f" in {filename}")

    for proto_out in proto_outs.values():
        proto_out.close()

def parse_log_file(log_file):
    packets = []
    with open(log_file, 'r') as file:
        lines = file.readlines()
        for i in range(0, len(lines), 6):
            tick = int(lines[i].split(':')[0])
            core_cluster = lines[i].split(':')[1].split('.')[2]
            cache_type = lines[i].split(':')[1].split('.')[3]
            addr = int(lines[i + 1].split(':')[1])
            size = int(lines[i + 2].split(':')[1])
            packet_type = lines[i + 5].split(':')[1].strip()

            if packet_type == "IFETCH":
                cmd = 61  # trace_ifetch
            elif packet_type == "LD":
                cmd = 1  # ReadReq
            elif packet_type == "ST":
                cmd = 4  # WriteReq
            else:
                raise RuntimeError(f"Error parsing command for Addr: {addr}")

            core_type = f"{core_cluster}_{cache_type}"
            packet_info = {
                'tick': tick,
                'addr': addr,
                'size': size,
                'cmd': cmd,
                'core_type': core_type
            }

            packets.append(packet_info)

    # Sort packets by tick
    packets.sort(key=lambda x: x['tick'])

    return packets

packets = parse_log_file(args.log_file)

print(f"\npackets: {packets}")

trace_files = {
    'core_cluster0_icache': os.path.join(m5.options.outdir, "lat_mem_rd_core0_L1i.trc.gz"),
    'core_cluster0_dcache': os.path.join(m5.options.outdir, "lat_mem_rd_core0_L1d.trc.gz"),
    'core_cluster1_icache': os.path.join(m5.options.outdir, "lat_mem_rd_core1_L1i.trc.gz"),
    'core_cluster1_dcache': os.path.join(m5.options.outdir, "lat_mem_rd_core1_L1d.trc.gz")
}

burst_size = 64

create_trace(trace_files, packets, burst_size)

print("Generated trace files:", trace_files)

def create_cfg_file(cfg_filename, trace_filename, period):
    cfg_file = open(cfg_filename, "w")
    cfg_file.write(f"STATE 0 {period} TRACE {trace_filename} 0\n")
    cfg_file.write("INIT 0\n")
    cfg_file.write("TRANSITION 0 0 1\n")
    cfg_file.close()

cfg_files = {
    'core_cluster0_icache': os.path.join(m5.options.outdir, "lat_mem_rd_core0_L1i.cfg"),
    'core_cluster0_dcache': os.path.join(m5.options.outdir, "lat_mem_rd_core0_L1d.cfg"),
    'core_cluster1_icache': os.path.join(m5.options.outdir, "lat_mem_rd_core1_L1i.cfg"),
    'core_cluster1_dcache': os.path.join(m5.options.outdir, "lat_mem_rd_core1_L1d.cfg")
}

itt = 150 * 1000  # 150 ns in ticks
period = int(itt * (16384 / burst_size))

for core_type, trace_file in trace_files.items():
    create_cfg_file(cfg_files[core_type], trace_file, period)

print(f"Generated cfg files: {cfg_files}")

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

system.tgen = TrafficGen(config_file=cfg_files['core_cluster0_icache'], progress_check="10s")
system.system_port = system.membus.cpu_side_ports

periodicStatDump(period)

root = Root(full_system=False, system=system)
root.system.mem_mode = "timing"

m5.instantiate()
m5.simulate(2 * period)

print("lat_mem_rd simulation complete")

print(f"lat_mem_rd with iterations, ranges:")
for packet in packets:
    print(packet)
