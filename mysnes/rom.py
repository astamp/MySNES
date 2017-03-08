"""
rom - ROM loader

https://en.wikibooks.org/wiki/Super_NES_Programming/SNES_memory_map#The_SNES_header
"""

# Standard library imports
import struct

# Six imports
import six

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
LO_ROM_HEADER = 0x7FC0
HI_ROM_HEADER = 0xFFC0
ROM_TYPE_OFFSET = 0x15

# Functions

# Classes
class RomType(object):
    LO_ROM = 0x20
    HI_ROM = 0x21
    LO_ROM_FAST_ROM = 0x30
    HI_ROM_FAST_ROM = 0x31
    EX_LO_ROM = 0x32
    EX_HI_ROM = 0x35
    
    VALID_TYPES = (LO_ROM, HI_ROM, LO_ROM_FAST_ROM, HI_ROM_FAST_ROM, EX_LO_ROM, EX_HI_ROM)
    
class RomImage(object):
    def __init__(self, filepath):
        self.type = None
        
        with open(filepath, "rb") as fileptr:
            self.data = fileptr.read()
            
        # Determine if header present.
        if len(self.data) & 0x3FF == 512:
            self.header = self.data[0:512]
            self.data = self.data[512:]
            
        # No header present.
        elif len(self.data) & 0x3FF == 0:
            self.header = b""
            
        # File is bad.
        else:
            raise ValueError("Invalid SMC header!")
            
        # Determine type from header.
        lo_rom_type = six.indexbytes(self.data, LO_ROM_HEADER + ROM_TYPE_OFFSET)
        if lo_rom_type in RomType.VALID_TYPES:
            self.type = lo_rom_type
        else:
            hi_rom_type = six.indexbytes(self.data, HI_ROM_HEADER + ROM_TYPE_OFFSET)
            if lo_rom_type in RomType.VALID_TYPES:
                self.type = lo_rom_type
            else:
                raise ValueError("Unable to determine cartridge type!")
                
        log.debug("Header info: %r", self.data[0x7FC0 : 0x8000])
        