from m5.params import *
from m5.SimObject import SimObject

class InterfaceBridge(SimObject):
    type = "InterfaceBridge"
    cxx_header = "mem/ruby/fwd_interface/Interface_Bridge.hh"
    cxx_class = "gem5::InterfaceBridge"

    chip0Request = ResponsePort("chip0 side port, receives requests")
    chip0Response = ResponsePort("chip0 side port, sends responses")