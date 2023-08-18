import os
import m5
from m5.util import addToPath
from m5.objects import *
from m5.options import *
import argparse

m5.util.addToPath("../../../")

from common import MemConfig
from common import ObjectList
from common import Options
from common import SysPaths
from common.cores.arm import O3_ARM_v7a, HPI
from ruby import Ruby

import devices

cpu_types = {
    "noncaching": NonCachingSimpleCPU,
    "minor": MinorCPU,
    "hpi": HPI.HPI,
    "o3": O3_ARM_v7a.O3_ARM_v7a_3,
}

def config_ruby(system, args):
    cpus = []
    for cluster in system.cpu_cluster:
        for cpu in cluster.cpus:
            cpus.append(cpu)
    
    Ruby.create_system(
        args,
        True, 
        system, 
        system.iobus,
        system._dma_ports,
        system.realview.bootmem,
        cpus,
    )

    system.ruby.clk_domain = SrcClockDomain(
        clock=args.ruby_clock, voltage_domain=system.voltage_domain
    )

def create(args):
    """Create and configure the system object."""

    if args.script and not os.path.isfile(args.script):
        print("Error: Bootscript %s does not exist" % args.script)
        sys.exit(1)

    cpu_class = cpu_types[args.cpu]
    mem_mode = cpu_class.memory_mode()

    system = devices.ArmRubySystem(
        args.mem_size,
        mem_mode=mem_mode,
        workload=ArmFsLinux(object_file=SysPaths.binary(args.kernel)),
        readfile=args.script,
    )

    # Add CPU clusters to the system
    system.cpu_cluster = [
        devices.CpuCluster(
            system,
            args.num_cpus,
            args.cpu_freq,
            "1.0V",
            cpu_class,
            None,
            None,
            None,
        )
    ]

    # Add the PCI devices we need for this system. The base system
    # doesn't have any PCI devices by default since they are assumed
    # to be added by the configuration scripts needing them.
    system.pci_devices = [
        # Create a VirtIO block device for the system's boot
        # disk. Attach the disk image using gem5's Copy-on-Write
        # functionality to avoid writing changes to the stored copy of
        # the disk image.
        PciVirtIO(vio=VirtIOBlock(image=create_cow_image(args.disk_image)))
    ]

    # Attach the PCI devices to the system. The helper method in the
    # system assigns a unique PCI bus ID to each of the devices and
    # connects them to the IO bus.
    for dev in system.pci_devices:
        system.attach_pci(dev)

    config_ruby(system, args)

    # Wire up the system's memory system
    system.connect()

    # Setup gem5's minimal Linux boot loader.
    system.realview.setupBootLoader(system, SysPaths.binary)

    if args.dtb:
        system.workload.dtb_filename = args.dtb
    else:
        # No DTB specified: autogenerate DTB
        system.workload.dtb_filename = os.path.join(
            m5.options.outdir, "system.dtb"
        )
        system.generateDtb(system.workload.dtb_filename)

    # Linux boot command flags
    kernel_cmd = [
        # Tell Linux to use the simulated serial port as a console
        "console=ttyAMA0",
        # Hard-code timi
        "lpj=19988480",
        # Disable address space randomisation to get a consistent
        # memory layout.
        "norandmaps",
        # Tell Linux where to find the root disk image.
        "root=%s" % args.root_device,
        # Mount the root disk read-write by default.
        "rw",
        # Tell Linux about the amount of physical memory present.
        "mem=%s" % args.mem_size,
    ]
    system.workload.command_line = " ".join(kernel_cmd)

    return system


def run(args):
    cptdir = m5.options.outdir
    if args.checkpoint:
        print("Checkpoint directory: %s" % cptdir)

    while True:
        event = m5.simulate()
        exit_msg = event.getCause()
        if exit_msg == "checkpoint":
            print("Dropping checkpoint at tick %d" % m5.curTick())
            cpt_dir = os.path.join(m5.options.outdir, "cpt.%d" % m5.curTick())
            m5.checkpoint(os.path.join(cpt_dir))
            print("Checkpoint done.")
        else:
            print(exit_msg, " @ ", m5.curTick())
            break

    sys.exit(event.getCode())


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dtb", type=str, default=None, help="DTB file to load"
    )
    parser.add_argument(
        "--kernel", type=str, default=default_kernel, help="Linux kernel"
    )
    parser.add_argument(
        "--disk-image",
        type=str,
        default=default_disk,
        help="Disk to instantiate",
    )
    parser.add_argument(
        "--root-device",
        type=str,
        default=default_root_device,
        help="OS device name for root partition (default: {})".format(
            default_root_device
        ),
    )
    parser.add_argument(
        "--script", type=str, default="", help="Linux bootscript"
    )
    parser.add_argument(
        "--cpu",
        choices=list(cpu_types.keys()),
        default="minor",
        help="CPU model to use",
    )
    parser.add_argument("--cpu-freq", type=str, default="4GHz")
    parser.add_argument("-n", "--num-cpus", type=int, default=1)
    parser.add_argument("--checkpoint", action="store_true")
    parser.add_argument("--restore", type=str, default=None)

    parser.add_argument(
        "--mem-type",
        default="DDR3_1600_8x8",
        choices=ObjectList.mem_list.get_names(),
        help="type of memory to use",
    )
    parser.add_argument(
        "--mem-channels", type=int, default=1, help="number of memory channels"
    )
    parser.add_argument(
        "--mem-ranks",
        type=int,
        default=None,
        help="number of memory ranks per channel",
    )
    parser.add_argument(
        "--mem-size",
        action="store",
        type=str,
        default="2GiB",
        help="Specify the physical memory size (single memory)",
    )
    parser.add_argument(
        "--enable-dram-powerdown",
        action="store_true",
        help="Enable low-power states in DRAMInterface",
    )
    parser.add_argument(
        "--mem-channels-intlv",
        type=int,
        default=0,
        help="Memory channels interleave",
    )

    parser.add_argument("--num-dirs", type=int, default=1)
    parser.add_argument("--num-l2caches", type=int, default=1)
    parser.add_argument("--num-l3caches", type=int, default=1)
    parser.add_argument("--l1d_size", type=str, default="64kB")
    parser.add_argument("--l1i_size", type=str, default="32kB")
    parser.add_argument("--l2_size", type=str, default="2MB")
    parser.add_argument("--l3_size", type=str, default="16MB")
    parser.add_argument("--l1d_assoc", type=int, default=2)
    parser.add_argument("--l1i_assoc", type=int, default=2)
    parser.add_argument("--l2_assoc", type=int, default=8)
    parser.add_argument("--l3_assoc", type=int, default=16)
    parser.add_argument("--cacheline_size", type=int, default=64)

    Ruby.define_options(parser)
    args = parser.parse_args()

    root = Root(full_system=False)
    root.system = create(args)

    if args.restore is not None:
        m5.instantiate(args.restore)
    else:
        m5.instantiate()

    run(args)


if __name__ == "__m5_main__":
    main()
