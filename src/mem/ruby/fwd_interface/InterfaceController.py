
from m5.params import *
from m5.SimObjects import SimObjects
from m5.objects.Controller import RubyController
from m5.objects.SimpleMemory import *


class Interface_Controller(RubyController):
    type = "Interface_Controller"
    cxx_header = "mem/ruby/fwd_interface/Interface_Controller.hh"
    cxx_class = "gem5::ruby::Interface_Controller"
    interface = Param.RubyDirectoryMemory("")
    toMemLatency = Param.Cycles((1), "")

    # Finish the buffer setup
    forwardToCache = Param.MessageBuffer("")
    responseToCache = Param.MessageBuffer("")
    requestFromCache = Param.MessageBuffer("")
    responseFromCache = Param.MessageBuffer("")
    requestToMemory = Param.MessageBuffer("")
    responseFromMemory = Param.MessageBuffer("")