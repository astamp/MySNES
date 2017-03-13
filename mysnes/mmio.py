"""
mmio - Memory mapped I/O registers

https://wiki.superfamicom.org/snes/show/Registers
"""

# Standard library imports

# Local
from .apu import APU

# Logging setup
import logging
log = logging.getLogger(__name__) # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

# Constants
APU_STATUS = 0x2140 # Byte
APU_DATA = 0x2141 # Byte
APU_ADDRESS = 0x2142 # Word

# Functions

# Classes
class MMIO(object):
    """ Mock memory mapped I/O bank for MySNES. """
    def __init__(self):
        self.apu = APU()
        self.map = {
            APU_STATUS : (self.apu.read_status, self.apu.write_status),
            APU_DATA : (self.apu.read_data, self.apu.write_data),
        }
    def __getitem__(self, address):
        handlers = self.map.get(address, None)
        if handlers:
            return handlers[0]()
        else:
            log.warning("Unhandled MMIO read 0x%04x, returning 0", address)
            return 0
        
    def __setitem__(self, address, value):
        handlers = self.map.get(address, None)
        if handlers:
            handlers[1](value)
        else:
            log.warning("Unhandled MMIO write 0x%04x -> 0x%02x", address, value)
        