from m5.params import *
from m5.simObject import SimObject

class Bridge(SimObject):
    type = "Bridge"
    cxx_header = "src/mem/ruby/fwd_interface/Bridge.hh"
    cxx_class = "gem5::Bridge"

    chip0_port = ResponsePort("chip0 side port, receives requests")
    chip1_port = RequestPort("chip1 side port, sends requests")