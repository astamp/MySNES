"""
mmio - Memory mapped I/O registers
"""

# Standard library imports
import array

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants

# Functions

# Classes
class MMIO(object):
    def __getitem__(self, key):
        # log.debug("MMIO read 0x%04x", key)
        return 0
        
    def __setitem__(self, key, value):
        # log.debug("MMIO write 0x%04x -> 0x%02x", key, value)
        pass