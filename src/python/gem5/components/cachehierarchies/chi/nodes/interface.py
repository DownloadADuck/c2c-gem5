from abc import abstractmethod
from gem5.isas import ISA
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.abstract_core import AbstractCore

from m5.objects import Interface_Controller, MessageBuffer, RubyNetwork

import math
