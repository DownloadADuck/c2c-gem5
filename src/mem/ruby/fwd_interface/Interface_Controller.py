
from m5.params import *
from m5.SimObject import SimObject
from m5.objects.Controller import RubyController

class Interface_Controller(RubyController):
    type = "Interface_Controller"
    cxx_header = "mem/ruby/fwd_interface/Interface_Controller.hh"
    cxx_class = "gem5::ruby::Interface_Controller"
    to_bridge_latency = Param.Cycles((1), "")
    data_channel_size = Param.Int("")

    reqOut = Param.MessageBuffer("")
    snpOut = Param.MessageBuffer("")
    rspOut = Param.MessageBuffer("")
    datOut = Param.MessageBuffer("")
    reqIn = Param.MessageBuffer("")
    snpIn = Param.MessageBuffer("")
    rspIn = Param.MessageBuffer("")
    datIn = Param.MessageBuffer("")

    # Interface to the bridge
    toBridge = Param.MessageBuffer("")
    fromBridge = Param.MessageBuffer("")