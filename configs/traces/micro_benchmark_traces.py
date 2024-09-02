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

        core_type = packet_info['core_type']
        filename = filenames[core_type]
        protolib.encodeMessage(proto_outs[filename], packet)

        # Updated print statements to distinguish between memory regions
        region = "Region 1 (0-1.5GB)" if packet.addr < (1.5 * 1024**3) else "Region 2 (2GB-3.5GB)"
        print(f"Encoding packet tick: {packet.tick}, addr: {packet.addr} ({region}), cmd: {packet.cmd}, size: {packet.size}")

    for proto_out in proto_outs.values():
        proto_out.close()

def generate_packets(iterations):
    packets = []
    base_tick = 5000
    mem_increment = 8 * 1024  # 8KB
    mem_start_1 = 0
    mem_start_2 = 2 * 1024**3  # 2GB
    mem_size = int(args.mem_size[:-2]) * 1024**3  # Convert from GB to bytes

    for i in range(iterations):
        tick = base_tick + i * 100

        # First memory region (0 - 1.5GB)
        addr_1 = (mem_start_1 + i * mem_increment) % mem_size
        packet_info_1 = {
            'tick': tick,
            'addr': addr_1,
            'size': 64,
            'cmd': 1,  # ReadReq
            'core_type': 'core_cluster0_dcache'
        }
        packets.append(packet_info_1)

        # Second memory region (2GB - 3.5GB)
        addr_2 = mem_start_2 + (i * mem_increment) % mem_size
        packet_info_2 = {
            'tick': tick + 50,  # Small offset between two packets
            'addr': addr_2,
            'size': 64,
            'cmd': 1,  # ReadReq
            'core_type': 'core_cluster0_dcache'
        }
        packets.append(packet_info_2)

    packets.sort(key=lambda x: x['tick'])
    return packets

iterations = args.iterations
packets = generate_packets(iterations)

trace_files = {
    'core_cluster0_icache': os.path.join(m5.options.outdir, "lat_mem_rd_core0_L1i.trc.gz"),
    'core_cluster0_dcache': os.path.join(m5.options.outdir, "lat_mem_rd_core0_L1d.trc.gz"),
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
