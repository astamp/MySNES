"""
debugger - Makes heads or tails of all of this.
"""

# Standard library imports

# Logging setup
import logging
log = logging.getLogger(__name__) # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

# Constants

# Functions

# Classes
class Debugger(object):
    """ Debug logging class, intentionally outside of cpu module for speed later. """
    def __init__(self, console):
        self.console = console
        self.cpu = console.cpu
        self.mem = console.mem
        
        self.should_break = False
        
    def poll(self):
        """ Run one iteration of the debugger, going interactive if single-stepping. """
        self.dump_regs()
        self.preview_next_instruction()
        log.debug("")
        
        if self.should_break:
            raw_input()
            
    def dump_regs(self):
        """ Dump all registers. """
        log.debug("B,A = 0x%02x,0x%02x C = 0x%04x", self.cpu.regs.B, self.cpu.regs.A, self.cpu.regs.C)
        log.debug("X = 0x%04x Y = 0x%04x", self.cpu.regs.X, self.cpu.regs.Y)
        log.debug("DBR = 0x%02x SP = 0x%04x DP = 0x%04x", self.cpu.regs.DBR, self.cpu.regs.SP, self.cpu.regs.DP)
        log.debug(
            "P = 0x%02x [%s|%s|%s|%s|%s|%s|%s|%s] %s",
            self.cpu.psr.value,
            "N" if self.cpu.psr.negative else "n",
            "O" if self.cpu.psr.overflow else "o",
            "-" if self.cpu.psr.emulation else ("M8" if self.cpu.psr.memory_select else "m16"),
            (("B" if self.cpu.psr.break_flag else "b") if self.cpu.psr.emulation else
             ("I8" if self.cpu.psr.memory_select else "i16")),
            "D" if self.cpu.psr.decimal else "d",
            "I" if self.cpu.psr.irq_disable else "i",
            "Z" if self.cpu.psr.zero else "z",
            "C" if self.cpu.psr.carry else "c",
            "Emulation" if self.cpu.psr.emulation else "Native",
        )
        log.debug("PBR:PC = %02x:%04x", self.cpu.regs.PBR, self.cpu.regs.PC)
        
    def preview_next_instruction(self):
        """ Read next opcode and decode to the mnemonic. """
        opcode = self.mem.read_byte(self.cpu.regs.PBR, self.cpu.regs.PC)
        
        opcode_handler = self.cpu.decode_table.get(opcode, None)
        if opcode_handler is not None:
            description = opcode_handler.__doc__.split(" - ")[0].strip()
        else:
            description = "UNKNOWN"
            
        log.debug("Next instruction: 0x%02x (%s)", opcode, description)
        