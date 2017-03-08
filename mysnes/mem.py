"""
mem - Memory map

https://en.wikibooks.org/wiki/Super_NES_Programming/SNES_memory_map#LoROM
http://www.emulatronia.com/doctec/consolas/snes/SNESMem.txt
http://www.cs.umb.edu/~bazz/snes/cartridges/lorom.html
"""

# Standard library imports
import array

# Local imports
from .mmio import MMIO

# Logging setup
import logging
log = logging.getLogger(__name__) # pylint: disable=C0103
log.addHandler(logging.NullHandler())

# Constants
LOW_RAM_SIZE = 0x2000
HIGH_RAM_SIZE = 0x6000
EXT_RAM_SIZE = 0x18000
SRAM_SIZE = 0x8000

# Functions

# Classes
class LoRomMemoryMap(object):
    """ Memory bank/address decoder for "LoROM" cartridges. """
    def __init__(self, rom_data):
        self.mmio = MMIO()
        self.lo_rom = array.array("B", rom_data)
        self.low_ram = array.array("B", (0,) * LOW_RAM_SIZE)
        self.high_ram = array.array("B", (0,) * HIGH_RAM_SIZE)
        self.extended_ram = array.array("B", (0,) * EXT_RAM_SIZE)
        self.cartridge_sram = array.array("B", (0,) * SRAM_SIZE)
        
    def decode(self, bank, address):
        """ Returns object/offset/writable for the given bank/address pair. """
        masked_bank = bank & 0x7F
        if masked_bank < 0x40: # 0x00-0x3F,0x80-0xBF
            if address < 0x2000:
                return self.low_ram, address, True
            elif address < 0x8000:
                return self.mmio, address, True
            else:
                return self.lo_rom, (masked_bank * 0x8000) + (address & 0x7FFF), False
        elif masked_bank < 0x70: # 0x40-0x6F,0xC0-0xEF
            if address < 0x8000:
                return None, 0, True
            else:
                return self.lo_rom, (masked_bank * 0x8000) + (address & 0x7FFF), False
        elif 0x70 <= masked_bank <= 0x7D: # 0x70-0x7D,0xF0-0xFD
            if address < 0x8000:
                # Max 32k, repeated in each bank.
                return self.cartridge_sram, address, True
            else:
                return self.lo_rom, (masked_bank * 0x8000) + (address & 0x7FFF), False
                
        elif bank == 0x7E: # NOTE: not masked
            if address < 0x2000:
                return self.low_ram, address, True
            elif address < 0x8000:
                return self.high_ram, address - 0x2000, True
            else:
                return self.extended_ram, address - 0x8000, True
                
        elif bank == 0x7F: # NOTE: not masked
            return self.extended_ram, address + 0x8000, True
            
        elif bank == 0xFE or bank == 0xFF: # NOTE: not masked
            if address < 0x8000:
                # Max 32k, repeated in each bank.
                return self.cartridge_sram, address, True
            else:
                return self.lo_rom, (masked_bank * 0x8000) + (address & 0x7FFF), False
                
    def read_byte(self, bank, address):
        """ Read a byte from the given bank/address pair. """
        memory, offset, _writable = self.decode(bank, address)
        # log.debug("read_byte(%02x:%04x) -> %d, %r", bank, address, offset, writable)
        return memory[offset]
        
    def read_word(self, bank, address):
        """ Read a word from the given bank/address pair. """
        memory, offset, _writable = self.decode(bank, address)
        # log.debug("read_word(%02x:%04x) -> %d, %r", bank, address, offset, writable)
        return memory[offset + 1] << 8 | memory[offset]
        
    def write_byte(self, bank, address, value):
        """ Write a byte to the given bank/address pair. """
        memory, offset, writable = self.decode(bank, address)
        # log.debug("write_byte(%02x:%04x) -> %d, %r", bank, address, offset, writable)
        if writable:
            memory[offset] = value
        
    def write_word(self, bank, address, value):
        """ Write a word to the given bank/address pair. """
        memory, offset, writable = self.decode(bank, address)
        # log.debug("write_word(%02x:%04x) -> %d, %r", bank, address, offset, writable)
        if writable:
            memory[offset] = value & 0xFF
            memory[offset + 1] = value >> 8
            
        