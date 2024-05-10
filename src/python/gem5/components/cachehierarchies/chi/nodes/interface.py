from typing import List
from abc import abstractmethod
from gem5.isas import ISA
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.abstract_core import AbstractCore

from m5.objects import (
    AddrRange,
    Interface_Controller,
    MessageBuffer,
    RubyNetwork,
    ClockDomain, 
    NULL,
)

import math

class TriggerMessageBuffer(MessageBuffer):
    # Not affected by Ruby tester randomization
    randomization = "disabled"
    allow_zero_latency = True

class OrderedTriggerMessageBuffer(TriggerMessageBuffer):
    ordered = True

class C2cMessageBuffer(MessageBuffer):
    randomization = "disabled"
    ordered = True

class InterfaceNode(Interface_Controller):
    _version = 0
    
    @classmethod
    def versionCount(cls):
        cls._version += 1
        return cls._version - 1
    
    def __init__(
        self, 
        network: RubyNetwork, 
        cache_line_size: int, 
        ranges: List[AddrRange]
    ):
        super(InterfaceNode, self).__init__()

        self.version = InterfaceNode.versionCount()
        self._cache_line_size = cache_line_size

        self.addr_ranges = ranges
        self.data_channel_size = 32
        self.connectQueues(network)

    def getBlockSizeBits(self):
        bits = int(math.log(self._cache_line_size, 2))
        if 2**bits != self._cache_line_size.value:
            raise Exception("Cache line size not a power of 2!")
        return bits
    
    def connectQueues(self, network: RubyNetwork):
        self.mandatoryQueue = MessageBuffer()
        self.prefetchQueue = MessageBuffer()

        self.triggerQueue = TriggerMessageBuffer()
        self.c2cReqRdy = TriggerMessageBuffer()
        self.reqRdy = TriggerMessageBuffer()

        self.requestToC2c=C2cMessageBuffer() 
        self.responseFromC2c=C2cMessageBuffer()
        self.responseToC2c=C2cMessageBuffer()
        self.requestFromC2c=C2cMessageBuffer()

        self.reqOut = MessageBuffer()
        self.rspOut = MessageBuffer()
        self.snpOut = MessageBuffer()
        self.datOut = MessageBuffer()
        self.reqIn = MessageBuffer()
        self.rspIn = MessageBuffer()
        self.snpIn = MessageBuffer()
        self.datIn = MessageBuffer()
        self.reqOut.out_port = network.in_port
        self.rspOut.out_port = network.in_port
        self.snpOut.out_port = network.in_port
        self.datOut.out_port = network.in_port
        self.reqIn.in_port = network.out_port
        self.rspIn.in_port = network.out_port
        self.snpIn.in_port = network.out_port
        self.datIn.in_port = network.out_port

        
class Interface(InterfaceNode):
    def __init__(
        self,
        network: RubyNetwork,
        cache_line_size: int,
        clk_domain: ClockDomain,
    ):
        super().__init__(network, cache_line_size)
        
        self.clk_domain = clk_domain