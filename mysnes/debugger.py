"""
debugger - Makes heads or tails of all of this.
"""

from __future__ import print_function

# Standard library imports
import sys

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
        
        self.breakpoints = []
        self.single_step = False
        self.debugger_shortcut = []
        self.dump_enabled = False
        
    def poll(self):
        """ Run one iteration of the debugger, going interactive if single-stepping. """
        if self.dump_enabled:
            log.debug("")
            self.dump_regs()
            self.preview_next_instruction()
        
        if self.should_break():
            self.enter_debugger()
            
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
        
    def dump_stack(self, count):
        """ Read next opcode and decode to the mnemonic. """
        log.debug("Stack trace %u bytes:", count)
        for address in range(self.cpu.regs.SP, self.cpu.regs.SP + count):
            log.debug("00:%04x = 0x%02x", address, self.mem.read_byte(0x00, address))
            
    def should_break(self):
        """ Return True if we should break now. """
        return self.single_step or (self.cpu.regs.PBR, self.cpu.regs.PC) in self.breakpoints
        
    def enter_debugger(self):
        """ Interactive debugger menu. """
        while True:
            self.preview_next_instruction()
            
            if len(self.debugger_shortcut) != 0:
                print("[%s] >" % " ".join(self.debugger_shortcut), end=" ")
            else:
                print(">", end=" ")
                
            try:
                cmd = raw_input().lower().split()
            except KeyboardInterrupt:
                print("^C")
                continue
                
            try:
                resume = self.process_command(cmd)
                if resume:
                    break
            except Exception:
                log.exception("Unhandled exception processing: %r", cmd)
                
    def process_command(self, cmd):
        """ Actually process the command from the user. """
        if len(cmd) == 0 and len(self.debugger_shortcut) != 0:
            cmd = self.debugger_shortcut
            print("Using: %s" % " ".join(cmd))
        else:
            self.debugger_shortcut = cmd
            
        if len(cmd) == 0:
            return False
            
        if len(cmd) == 1 and cmd[0] in ("continue", "c"):
            self.single_step = False
            return True
            
        elif len(cmd) == 1 and cmd[0] in ("step", "s"):
            self.single_step = True
            return True
            
        elif len(cmd) == 1 and cmd[0] in ("quit", "q"):
            sys.exit(0)
            
        elif len(cmd) == 1 and cmd[0] in ("dump", "d"):
            self.dump_regs()
            
        elif len(cmd) == 2 and cmd[0] in ("stack", "st"):
            self.dump_stack(int(cmd[1]))
            
        elif len(cmd) >= 1 and cmd[0] == "info":
            self.debugger_shortcut = []
            if len(cmd) == 2 and cmd[1] in ("breakpoints", "break"):
                print("Breakpoints:")
                for breakpoint in self.breakpoints:
                    print("  %04x:%04x" % breakpoint)
                    
        elif len(cmd) == 2 and cmd[0] == "break":
            self.debugger_shortcut = []
            (pbr, pc) = cmd[1].split(":")
            self.breakpoints.append((int(pbr, 16), int(pc, 16)))
            
        elif len(cmd) == 2 and cmd[0] == "clear":
            self.debugger_shortcut = []
            if cmd[1] == "all":
                self.breakpoints = []
            elif cmd[1] == "dump":
                self.dump_enabled = False
            else:
                (pbr, pc) = cmd[1].split(":")
                self.breakpoints.remove((int(pbr, 16), int(pc, 16)))
                    
        elif len(cmd) >= 1 and cmd[0] == "set":
            self.debugger_shortcut = []
            if len(cmd) == 2 and cmd[1] == "dump":
                self.dump_enabled = True
                self.dump_regs()
                