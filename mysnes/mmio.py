"""
mmio - Memory mapped I/O registers
"""

# Standard library imports

# Logging setup
import logging
log = logging.getLogger(__name__) # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

# Constants

# Functions

# Classes
class MMIO(object):
    """ Mock memory mapped I/O bank for MySNES. """
    def __getitem__(self, key):
        # log.debug("MMIO read 0x%04x", key)
        return 0
        
    def __setitem__(self, key, value):
        # log.debug("MMIO write 0x%04x -> 0x%02x", key, value)
        pass
        