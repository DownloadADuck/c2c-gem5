import m5
from m5.objects import *
from m5.util import *

# Specify the simulation parameters
num_cpus = 1
mem_size = '512MB'
cpu_type = 'timing'
cpu_clock = '2GHz'
network_link_speed = '10Gbps'

# Create the system object
system = System()

# Set the clock frequency of the system
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = cpu_clock
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the memory system
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('0', size=mem_size)]
system.membus = SystemXBar()

# Set up the CPU
cpu = TimingSimpleCPU()
cpu.clk_domain = system.clk_domain
system.cpu = cpu

# Set up the memory controller and connect it to the CPU
mem_ctrl = DDR3_1600_8x8()
system.mem_ctrl = mem_ctrl
system.cpu.mem_side_ports = system.membus.mem_side_ports
mem_ctrl.port = system.membus.slave

# Set up the network interface
ethernet = Eth10G()
ethernet.pcap = "test.pcap"
ethernet.link_speed = network_link_speed
system.ethernet = ethernet

# Set up the traffic generator
traffic_gen = TrafficGen(config_file='traffic_gen.cfg')
system.traffic_gen = traffic_gen

# Connect the network interface and the traffic generator
ethernet.interface = network.SwitchedEthernetInterface()
ethernet.interface.pktgen = traffic_gen

# Set up the simulation
root = Root(full_system=False, system=system)
m5.instantiate()

# Run the simulation
print("Running the simulation...")
exit_event = m5.simulate()

print('Exiting @ tick %i because %s' % (m5.curTick(), exit_event.getCause()))
