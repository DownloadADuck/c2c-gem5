from m5.params import *
from m5.SimObject import SimObject

class InterfaceBridge(SimObject):
    type = "InterfaceBridge"
    cxx_header = "mem/ruby/fwd_interface/Interface_Bridge.hh"
    cxx_class = "gem5::InterfaceBridge"

    chip0_port = ResponsePort("chip0 side port, receives requests")
    chip1_port = RequestPort("chip1 side port, sends requests")