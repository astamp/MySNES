"""
apu - Audio processing unit

https://wiki.superfamicom.org/snes/show/Transferring+Data+from+ROM+to+the+SNES+APU
"""

# Standard library imports

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
class APU(object):
    """ Mock audio processing unit for MySNES. """
    def __init__(self):
        pass
        
    def read_status(self):
        return 0xAA
        
    def write_status(self, value):
        self.temp_address = value
        
    def read_data(self):
        return 0xBB
        
    def write_data(self, value):
        self.temp_byte = value
        