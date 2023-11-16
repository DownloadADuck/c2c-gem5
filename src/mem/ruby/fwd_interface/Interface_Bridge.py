from m5.params import *
from m5.SimObject import SimObject

class InterfaceBridge(SimObject):
    type = "InterfaceBridge"
    cxx_header = "mem/ruby/fwd_interface/Interface_Bridge.hh"
    cxx_class = "gem5::InterfaceBridge"

    chip0request = RequestPort("chip0 side port, receives requests")
    chip0response = ResponsePort("chip0 side port, sends responses")

    chip1request = RequestPort("chip1 side port, receives requests")
    chip1response = ResponsePort("chip1 side port, sends responses")