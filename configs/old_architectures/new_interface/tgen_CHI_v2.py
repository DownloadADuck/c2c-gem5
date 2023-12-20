# Copyright (c) 2021 ARM Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import m5
from m5.objects import *
from m5.defines import buildEnv

from ruby_config import create_topology


def define_options(parser):
    parser.add_argument(
        "--chi-config",
        action="store",
        type=str,
        default=None,
        help="NoC config. parameters and bindings. "
        "Required for CustomMesh topology",
    )
    parser.add_argument("--enable-dvm", default=False, action="store_true")


def read_config_file(file):
    """Read file as a module and return it"""
    import types
    import importlib.machinery

    loader = importlib.machinery.SourceFileLoader("chi_configs", file)
    chi_configs = types.ModuleType(loader.name)
    loader.exec_module(chi_configs)
    return chi_configs


def create_chips(
    options0,
    options1,
    full_system,
    system,
    dma_ports, 
    bootmem, 
    ruby_system, 
    cpus,
    network0,
    network1,
):

    if buildEnv["PROTOCOL"] != "CHI":
        m5.panic("This script requires the CHI build")

    if options0.num_dirs < 1:
        m5.fatal("--num-dirs must be at least 1")

    if options0.num_l3caches < 1:
        m5.fatal("--num-l3caches must be at least 1")

    if full_system and options0.enable_dvm:
        if len(cpus) <= 1:
            m5.fatal("--enable-dvm can't be used with a single CPU")
        for cpu in cpus:
            for decoder in cpu.decoder:
                decoder.dvm_enabled = True

    # read specialized classes from config file if provided
    if options0.chi_config:
        chi_defs = read_config_file(options.chi_config)
    elif options0.topology == "CustomMesh":
        m5.fatal("--noc-config must be provided if topology is CustomMesh")
    else:
        # Use the defaults from CHI_config
        from test_interface import CHI_config as chi_defs

    # NoC params
    params = chi_defs.NoC_Params
    # Node types
    CHI_RNF = chi_defs.CHI_RNF
    CHI_HNF = chi_defs.CHI_HNF
    CHI_MN = chi_defs.CHI_MN
    CHI_SNF_MainMem = chi_defs.CHI_SNF_MainMem
    CHI_SNF_BootMem = chi_defs.CHI_SNF_BootMem
    CHI_RNI_DMA = chi_defs.CHI_RNI_DMA
    CHI_RNI_IO = chi_defs.CHI_RNI_IO

    CHI_Interface = chi_defs.CHI_Interface

    # Declare caches and controller types used by the protocol
    # Notice tag and data accesses are not concurrent, so the a cache hit
    # latency = tag + data + response latencies.
    # Default response latencies are 1 cy for all controllers.
    # For L1 controllers the mandatoryQueue enqueue latency is always 1 cy and
    # this is deducted from the initial tag read latency for sequencer requests
    # dataAccessLatency may be set to 0 if one wants to consider parallel
    # data and tag lookups
    class L1ICache(RubyCache):
        dataAccessLatency = 1
        tagAccessLatency = 1
        size = options0.l1i_size
        assoc = options0.l1i_assoc

    class L1DCache(RubyCache):
        dataAccessLatency = 2
        tagAccessLatency = 1
        size = options0.l1d_size
        assoc = options0.l1d_assoc

    class L2Cache(RubyCache):
        dataAccessLatency = 6
        tagAccessLatency = 2
        size = options0.l2_size
        assoc = options0.l2_assoc

    class HNFCache(RubyCache):
        dataAccessLatency = 10
        tagAccessLatency = 2
        size = options0.l3_size
        assoc = options0.l3_assoc

    # other functions use system.cache_line_size assuming it has been set
    assert system.cache_line_size.value == options0.cacheline_size

    cpu_sequencers0 = []
    mem_cntrls0 = []
    mem_dests0 = []
    network_nodes0 = []
    network_cntrls0 = []
    hnf_dests0 = []
    all_cntrls0 = []

    ############# CHIP0 #############

    # Creates on RNF per cpu with priv l2 caches
    assert len(cpus) == options0.num_cpus
    ruby_system.rnf0 = [
        CHI_RNF(
            [cpu],
            ruby_system,
            L1ICache,
            L1DCache,
            system.cache_line_size.value,
            network0,
        )
        for cpu in cpus
    ]

    for rnf in ruby_system.rnf0:
        rnf.addPrivL2Cache(L2Cache)
        cpu_sequencers0.extend(rnf.getSequencers())
        all_cntrls0.extend(rnf.getAllControllers())
        network_nodes0.append(rnf)
        network_cntrls0.extend(rnf.getNetworkSideControllers())
    
    # Creates one Misc Node
    ruby_system.mn0 = [CHI_MN(ruby_system, [cpu.l1d for cpu in cpus], network0)]
    for mn in ruby_system.mn0:
        all_cntrls0.extend(mn.getAllControllers())
        network_nodes0.append(mn)
        network_cntrls0.extend(mn.getNetworkSideControllers())
        assert mn.getAllControllers() == mn.getNetworkSideControllers()

    # Look for other memories
    other_memories0 = []
    if bootmem:
        other_memories0.append(bootmem)
    if getattr(system, "sram", None):
        other_memories0.append(getattr(system, "sram", None))
    on_chip_mem_ports = getattr(system, "_on_chip_mem_ports", None)
    if on_chip_mem_ports:
        other_memories0.extend([p.simobj for p in on_chip_mem_ports])

    # Create the LLCs cntrls
    sysranges0 = [] + system.mem_ranges

    for m in other_memories0:
        sysranges.append(m.range)

    hnf_list0 = [i for i in range(options0.num_l3caches)]
    CHI_HNF.createAddrRanges(sysranges0, system.cache_line_size.value, hnf_list0)
    ruby_system.hnf0 = [
        CHI_HNF(i, ruby_system, HNFCache, None, network0)
        for i in range(options0.num_l3caches)
    ]

    for hnf in ruby_system.hnf0:
        network_nodes0.append(hnf)
        network_cntrls0.extend(hnf.getNetworkSideControllers())
        assert hnf.getAllControllers() == hnf.getNetworkSideControllers()
        all_cntrls0.extend(hnf.getAllControllers())
        hnf_dests0.extend(hnf.getAllControllers())

    # Create the memory controllers
    # Notice we don't define a Directory_Controller type so we don't use
    # create_directories shared by other protocols.

    ruby_system.snf0 = [
        CHI_SNF_MainMem(ruby_system, None, network0, None)
        for i in range(options0.num_dirs)
    ]
    for snf in ruby_system.snf0:
        network_nodes0.append(snf)
        network_cntrls0.extend(snf.getNetworkSideControllers())
        assert snf.getAllControllers() == snf.getNetworkSideControllers()
        mem_cntrls0.extend(snf.getAllControllers())
        all_cntrls0.extend(snf.getAllControllers())
        mem_dests0.extend(snf.getAllControllers())

    if len(other_memories0) > 0:
        ruby_system.rom_snf0 = [
            CHI_SNF_BootMem(ruby_system, None, m) for m in other_memories0
        ]
        for snf in ruby_system.rom_snf0:
            network_nodes0.append(snf)
            network_cntrls0.extend(snf.getNetworkSideControllers())
            all_cntrls0.extend(snf.getAllControllers())
            mem_dests0.extend(snf.getAllControllers())

    # Creates the controller for dma ports and io

    if len(dma_ports) > 0:
        ruby_system.dma_rni0 = [
            CHI_RNI_DMA(ruby_system, dma_port, None) for dma_port in dma_ports
        ]
        for rni in ruby_system.dma_rni0:
            network_nodes0.append(rni)
            network_cntrls0.extend(rni.getNetworkSideControllers())
            all_cntrls0.extend(rni.getAllControllers())

    # Assign downstream destinations
    for rnf in ruby_system.rnf0:
        rnf.setDownstream(hnf_dests0)
    if len(dma_ports) > 0:
        for rni in ruby_system.dma_rni:
            rni.setDownstream(hnf_dests0)
    if full_system:
        ruby_system.io_rni.setDownstream(hnf_dests0)
    for hnf in ruby_system.hnf0:
        hnf.setDownstream(mem_dests0)

    # Setup data message size for all controllers
    for cntrl in all_cntrls0:
        cntrl.data_channel_size = params.data_width

    ############# CHIP1 #############

    cpu_sequencers1 = []
    mem_cntrls1 = []
    mem_dests1 = []
    network_nodes1 = []
    network_cntrls1 = []
    hnf_dests1 = []
    all_cntrls1 = []

    # Creates on RNF per cpu with priv l2 caches
    #assert len(cpus) == options1.num_cpus
    #ruby_system.rnf1 = [
    #    CHI_RNF(
    #        [cpu],
    #        ruby_system,
    #        L1ICache,
    #        L1DCache,
    #        system.cache_line_size.value,
    #        network1,
    #    )
    #    for cpu in cpus
    #]

    #for rnf in ruby_system.rnf1:
    #    rnf.addPrivL2Cache(L2Cache)
    #    cpu_sequencers1.extend(rnf.getSequencers())
    #    all_cntrls1.extend(rnf.getAllControllers())
    #    network_nodes1.append(rnf)
    #    network_cntrls1.extend(rnf.getNetworkSideControllers())
    
    # Creates one Misc Node
    ruby_system.mn1 = [CHI_MN(ruby_system, [cpu.l1d for cpu in cpus], network1)]
    for mn in ruby_system.mn1:
        all_cntrls1.extend(mn.getAllControllers())
        network_nodes1.append(mn)
        network_cntrls1.extend(mn.getNetworkSideControllers())
        assert mn.getAllControllers() == mn.getNetworkSideControllers()

    # Look for other memories
    other_memories1 = []
    if bootmem:
        other_memories1.append(bootmem)
    if getattr(system, "sram", None):
        other_memories1.append(getattr(system, "sram", None))
    on_chip_mem_ports = getattr(system, "_on_chip_mem_ports", None)
    if on_chip_mem_ports:
        other_memories1.extend([p.simobj for p in on_chip_mem_ports])

    # Create the LLCs cntrls
    sysranges1 = [] + system.mem_ranges

    for m in other_memories1:
        sysranges.append(m.range)

    hnf_list1 = [i for i in range(options1.num_l3caches)]
    CHI_HNF.createAddrRanges(sysranges1, system.cache_line_size.value, hnf_list1)
    ruby_system.hnf1 = [
        CHI_HNF(i, ruby_system, HNFCache, None, network1)
        for i in range(options1.num_l3caches)
    ]

    for hnf in ruby_system.hnf1:
        network_nodes1.append(hnf)
        network_cntrls1.extend(hnf.getNetworkSideControllers())
        assert hnf.getAllControllers() == hnf.getNetworkSideControllers()
        all_cntrls1.extend(hnf.getAllControllers())
        hnf_dests1.extend(hnf.getAllControllers())

    # Create the memory controllers
    # Notice we don't define a Directory_Controller type so we don't use
    # create_directories shared by other protocols.

    ruby_system.snf1 = [
        CHI_SNF_MainMem(ruby_system, None, network0, None)
        for i in range(options1.num_dirs)
    ]
    for snf in ruby_system.snf1:
        network_nodes1.append(snf)
        network_cntrls1.extend(snf.getNetworkSideControllers())
        assert snf.getAllControllers() == snf.getNetworkSideControllers()
        mem_cntrls1.extend(snf.getAllControllers())
        all_cntrls1.extend(snf.getAllControllers())
        mem_dests1.extend(snf.getAllControllers())

    if len(other_memories1) > 0:
        ruby_system.rom_snf1 = [
            CHI_SNF_BootMem(ruby_system, None, m) for m in other_memories1
        ]
        for snf in ruby_system.rom_snf1:
            network_nodes1.append(snf)
            network_cntrls1.extend(snf.getNetworkSideControllers())
            all_cntrls1.extend(snf.getAllControllers())
            mem_dests1.extend(snf.getAllControllers())

    # Creates the controller for dma ports and io

    if len(dma_ports) > 0:
        ruby_system.dma_rni1 = [
            CHI_RNI_DMA(ruby_system, dma_port, None) for dma_port in dma_ports
        ]
        for rni in ruby_system.dma_rni1:
            network_nodes1.append(rni)
            network_cntrls1.extend(rni.getNetworkSideControllers())
            all_cntrls1.extend(rni.getAllControllers())

    # Assign downstream destinations
    #for rnf in ruby_system.rnf1:
    #    rnf.setDownstream(hnf_dests1)
    if len(dma_ports) > 0:
        for rni in ruby_system.dma_rni:
            rni.setDownstream(hnf_dests1)
    if full_system:
        ruby_system.io_rni.setDownstream(hnf_dests1)
    for hnf in ruby_system.hnf1:
        hnf.setDownstream(mem_dests1)

    # Setup data message size for all controllers
    for cntrl in all_cntrls1:
        cntrl.data_channel_size = params.data_width


    ############# INTERFACE #############
    # Registers the Inerface controller in the network_cntrls
    ruby_system.interface = [
        CHI_Interface(
            ruby_system,
            network0,
            network1
        )
    ]
    network_cntrls0.extend(ruby_system.interface.getNetworkSideControllers())
    network_cntrls1.extend(ruby_system.interface.getNetworkSideControllers())

    ############# NETWORK #############
    # Network configurations
    # virtual networks: 0=request, 1=snoop, 2=response, 3=data
    network0.number_of_virtual_networks = 4
    network0.control_msg_size = params.cntrl_msg_size
    network0.data_msg_size = params.data_width

    network1.number_of_virtual_networks = 4
    network1.control_msg_size = params.cntrl_msg_size
    network1.data_msg_size = params.data_width
    
    if options0.network == "simple":
        network0.buffer_size = params.router_buffer_size
    if options1.network == "simple":
        network1.buffer_size = params.router_buffer_size

    # Incorporate the params into options so it's propagated to
    # makeTopology and create_topology the parent scripts
    for k in dir(params):
        if not k.startswith("__"):
            setattr(options0, k, getattr(params, k))
            setattr(options1, k, getattr(params, k))

    if options0.topology == "CustomMesh":
        topology0 = create_topology(network_nodes0, options0)
    elif options0.topology in ["Crossbar", "Pt2Pt"]:
        topology0 = create_topology(network_cntrls0, options0)
    else:
        m5.fatal("%s not supported!" % options0.topology)

    if options1.topology == "CustomMesh":
        topology1 = create_topology(network_nodes1, options1)
    elif options1.topology in ["Crossbar", "Pt2Pt"]:
        topology1 = create_topology(network_cntrls1, options1)
    else:
        m5.fatal("%s not supported!" % options1.topology)

    return (cpu_sequencers0, cpu_sequencers1, mem_cntrls0, mem_cntrls1, topology0, topology1)