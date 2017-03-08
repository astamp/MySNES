"""
console - Essentially the top-level of mysnes.

http://www.smwiki.net/wiki/Vector_Info#Reset_vector
"""

# Standard library imports

# Local imports
from .cpu import Cpu65c816
from .rom import RomImage, RomType
from .mem import LoRomMemoryMap
from .debugger import Debugger

# Logging setup
import logging
log = logging.getLogger(__name__) # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

# Constants

# Functions

# Classes
class Console(object):
    """ Main console object containing all other components. """
    def __init__(self, filepath):
        self.cpu = Cpu65c816(self)
        self.rom = RomImage(filepath)
        assert self.rom.type == RomType.LO_ROM, "This is all we've got for now!"
        self.mem = LoRomMemoryMap(self.rom.data)
        
        # Must be after CPU and MEM.
        self.debugger = Debugger(self)
        
    def run(self):
        """ Main event loop for MySNES. """
        cpu = self.cpu
        debugger = self.debugger
        
        cpu.regs.PC = self.mem.read_word(0x00, 0xFFFC)
        while True:
            debugger.poll()
            cpu.fetch()
            