"""
cpu - 65c816 CPU

https://en.wikipedia.org/wiki/WDC_65816/65802
http://6502.org/tutorials/65c816opcodes.html
https://en.wikibooks.org/wiki/Super_NES_Programming/65c816_reference
http://www.defence-force.org/computing/oric/coding/annexe_2/index.htm
"""

# Standard library imports
import struct
from ctypes import Structure, Union, c_ushort, c_ubyte

# Logging setup
import logging
log = logging.getLogger(__name__) # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

# Constants

# Functions
SIGNED_BYTE = struct.Struct("<b")
UNSIGNED_BYTE = struct.Struct("<B")
def signed_byte(value):
    """ Interpret an unsigned byte as a signed byte. """
    return SIGNED_BYTE.unpack(UNSIGNED_BYTE.pack(value))[0]
    
# Classes
class ByteRegisters(Structure):
    """ Structure for byte access to registers. """
    _fields_ = [
        ("A", c_ubyte),
        ("B", c_ubyte),
        ("XL", c_ubyte),
        ("XH", c_ubyte),
        ("YL", c_ubyte),
        ("YH", c_ubyte),
        ("SPL", c_ubyte),
        ("SPH", c_ubyte),
        ("DPL", c_ubyte),
        ("DPH", c_ubyte),
        ("PCL", c_ubyte),
        ("PCH", c_ubyte),
        ("PBR", c_ubyte), # Program bank register
        ("DBR", c_ubyte), # Data bank register
    ]
    
class WordRegisters(Structure):
    """ Structure for word access to registers. """
    _fields_ = [
        ("C", c_ushort), # 16-bit accumulator
        ("X", c_ushort), # Index X
        ("Y", c_ushort), # Index Y
        ("SP", c_ushort), # Stack pointer
        ("DP", c_ushort), # Direct page register
        ("PC", c_ushort), # Program counter
    ]
    
class Registers(Union):
    """ Union for byte/word access to registers. """
    _anonymous_ = ("byte", "word")
    _fields_ = [
        ("byte", ByteRegisters),
        ("word", WordRegisters),
    ]
    
    def __init__(self):
        Union.__init__(self)
        
        # These are all initialized to zero by ctypes but this is done so PyLint isn't confused.
        # pylint: disable=invalid-name
        self.A = 0
        self.B = 0
        self.C = 0
        
        self.XL = 0
        self.XH = 0
        self.X = 0
        
        self.YL = 0
        self.YH = 0
        self.Y = 0
        
        self.SPL = 0
        self.SPH = 0
        self.SP = 0
        
        self.DPL = 0
        self.DPH = 0
        self.DP = 0
        
        self.PCL = 0
        self.PCH = 0
        self.PC = 0
        
        self.PBR = 0
        self.DBR = 0
        # pylint: enable=invalid-name
        
    def __getitem__(self, key):
        return getattr(self, key)
        
    def __setitem__(self, key, value):
        setattr(self, key, value)
        
class ProcessorStatusRegister(object):
    """ Processor status register "P". """
    CARRY = 0x01
    ZERO = 0x02
    IRQ_DISABLE = 0x04
    DECIMAL = 0x08
    BREAK_FLAG = INDEX_REGISTER_SELECT = 0x10
    MEMORY_SELECT = 0x20
    OVERFLOW = 0x40
    NEGATIVE = 0x80
    
    ALWAYS_ON_EMULATION = MEMORY_SELECT 
    
    def __init__(self):
        self.carry = False
        self.zero = False
        self.irq_disable = False
        self.decimal = False
        self.index_register_select = False # X (Native only) 1=8-bit 0=16-bit
        self.memory_select = False # M (Native Only) 1=8-bit 0=16-bit
        self.break_flag = False # B (Emulation only)
        self.overflow = False
        self.negative = False
        
        self.emulation = True # Boots into emulation mode.
        
    @property
    def value(self):
        """ Return the P register as a byte value. """
        value = 0x00
        
        if self.emulation:
            value |= self.ALWAYS_ON_EMULATION
            if self.break_flag:
                value |= self.BREAK_FLAG
        else:
            if self.index_register_select:
                value |= self.INDEX_REGISTER_SELECT
            if self.memory_select:
                value |= self.MEMORY_SELECT
                
        if self.carry:
            value |= self.CARRY
        if self.zero:
            value |= self.ZERO
        if self.irq_disable:
            value |= self.IRQ_DISABLE
        if self.decimal:
            value |= self.DECIMAL
        if self.overflow:
            value |= self.OVERFLOW
        if self.negative:
            value |= self.NEGATIVE
        
        return value
        
    @value.setter
    def value(self, value):
        """ Set the P register from a byte value. """
        if not self.emulation:
            self.index_register_select = bool(value & self.INDEX_REGISTER_SELECT)
            self.memory_select = bool(value & self.MEMORY_SELECT)
            
        self.carry = bool(value & self.CARRY)
        self.zero = bool(value & self.ZERO)
        self.irq_disable = bool(value & self.IRQ_DISABLE)
        self.decimal = bool(value & self.DECIMAL)
        self.overflow = bool(value & self.OVERFLOW)
        self.negative = bool(value & self.NEGATIVE)
        
    @property
    def byte_access(self):
        """ Are memory/accumulator accesses 8 bits wide? """
        return self.emulation or self.memory_select
    
    @property
    def word_access(self):
        """ Are memory/accumulator accesses 16 bits wide? """
        return not (self.emulation or self.memory_select)
        
    @property
    def byte_index(self):
        """ Are index registers (X/Y) 8 bits wide? """
        return self.emulation or self.index_register_select
    
    @property
    def word_index(self):
        """ Are index registers (X/Y) 16 bits wide? """
        return not (self.emulation or self.index_register_select)
        
    @property
    def borrow(self):
        """ The carry flag is 0 if a borrow is required and 1 if none is required. """
        return not self.carry
        
    @borrow.setter
    def borrow(self, value):
        """ Set to true if a borrow is required (left < right in subtraction). """
        self.carry = not value
        
    def set_nz_8(self, value):
        """ Set the N and Z flags from an 8-bit result. """
        self.zero = value == 0
        self.negative = bool(value & 0x80)
        
    def set_nz_16(self, value):
        """ Set the N and Z flags from a 16-bit result. """
        self.zero = value == 0
        self.negative = bool(value & 0x8000)
        
class InvalidOpcodeException(Exception):
    """ Exception raised when an invalid opcode is encountered. """
    def __init__(self, opcode, pbr, pc):
        super(InvalidOpcodeException, self).__init__()
        self.opcode = opcode
        self.pbr = pbr
        self.pc = pc
        
    def __str__(self):
        return "Invalid opcode: 0x%02x at %02x:%04x" % (self.opcode, self.pbr, self.pc)
        
class Cpu65c816(object):
    """ 65c816 CPU for MySNES. """
    def __init__(self, console):
        self.console = console
        self.psr = ProcessorStatusRegister()
        self.regs = Registers()
        
        self.decode_table = {
            0x08 : self.opcode_php,
            0x10 : self.opcode_bpl,
            0x18 : self.opcode_clc,
            0x1B : self.opcode_tcs,
            0x20 : self.opcode_jsr,
            0x38 : self.opcode_sec,
            0x5B : self.opcode_tcd,
            0x78 : self.opcode_sei,
            0x8D : self.opcode_sta_absolute,
            0x8F : self.opcode_sta_absolute_long,
            0x98 : self.opcode_tya,
            0x9C : self.opcode_stz_absolute,
            0x9F : self.opcode_sta_absolute_long_x,
            0xA0 : self.opcode_ldy_immediate,
            0xA2 : self.opcode_ldx_immediate,
            0xA8 : self.opcode_tay,
            0xA9 : self.opcode_lda_immediate,
            0xC2 : self.opcode_rep,
            0xCA : self.opcode_dex,
            0xCD : self.opcode_cmp_absolute,
            0xE2 : self.opcode_sep,
            0xE9 : self.opcode_sbc_immediate,
            0xFB : self.opcode_xce,
        }
        
    # ********** Instruction fetch and decode functions **********
    def read_instruction_byte(self):
        """ Fetch the next byte from PBR:PC and increment PC. """
        value = self.console.mem.read_byte(self.regs.PBR, self.regs.PC)
        self.regs.PC += 1
        return value
        
    def read_instruction_word(self):
        """ Fetch the next word from PBR:PC and increment PC. """
        value = self.console.mem.read_word(self.regs.PBR, self.regs.PC)
        self.regs.PC += 2
        return value
        
    def fetch(self):
        """ Fetch, decode, and execute the next instruction at PBR:PC. """
        pbr, pc = self.regs.PBR, self.regs.PC
        opcode = self.read_instruction_byte()
        
        opcode_handler = self.decode_table.get(opcode, None)
        if opcode_handler is not None:
            opcode_handler()
        else:
            raise InvalidOpcodeException(opcode, pbr, pc)
        
    # ********** Stack management functions **********
    def _push_byte(self, value):
        """ Pushes the given byte onto the stack. """
        self.console.mem.write_byte(0x00, self.regs.SP, value)
        self.regs.SP -= 1

    def _push_word(self, value):
        """ Pushes the given word onto the stack. """
        self.console.mem.write_word(0x00, self.regs.SP, value)
        self.regs.SP -= 2
        
    # ********** Opcode handler functions **********
    def opcode_sei(self):
        """ SEI - Set the interrupt disable flag. """
        self.psr.irq_disable = True
        return 2
        
    def opcode_clc(self):
        """ CLC - Clear the carry flag. """
        self.psr.carry = False
        return 2
        
    def opcode_sec(self):
        """ SEC - Set the carry flag. """
        self.psr.carry = True
        return 2
        
    def opcode_rep(self):
        """ REP - Clear processor status bits from mask. """
        value = self.read_instruction_byte()
        self.psr.value = self.psr.value & (~value)
        return 3
        
    def opcode_sep(self):
        """ SEP - Set processor status bits from mask. """
        value = self.read_instruction_byte()
        self.psr.value = self.psr.value | value
        return 3
        
    def opcode_xce(self):
        """ XCE - Exchange the carry and emulation flag. """
        old_emulation = self.psr.emulation
        self.psr.emulation = self.psr.carry
        self.psr.carry = old_emulation
        return 2
        
    def opcode_stz_absolute(self):
        """ STZ abs - Store zero absolute. """
        address = self.read_instruction_word()
        if self.psr.byte_access:
            self.console.mem.write_byte(self.regs.DBR, address, 0x00)
            return 4
        else:
            self.console.mem.write_word(self.regs.DBR, address, 0x0000)
            return 5
            
    def opcode_lda_immediate(self):
        """ LDA imm - Load accumulator with immediate. """
        if self.psr.byte_access:
            self.regs.A = self.read_instruction_byte()
            self.psr.set_nz_8(self.regs.A)
            return 2
        else:
            self.regs.C = self.read_instruction_word()
            self.psr.set_nz_16(self.regs.C)
            return 3
            
    def opcode_ldx_immediate(self):
        """ LDX imm - Load X with immediate. """
        if self.psr.byte_index:
            self.regs.XL = self.read_instruction_byte()
            self.psr.set_nz_8(self.regs.XL)
            return 2
        else:
            self.regs.X = self.read_instruction_word()
            self.psr.set_nz_16(self.regs.X)
            return 3
            
    def opcode_ldy_immediate(self):
        """ LDY imm - Load Y with immediate. """
        if self.psr.byte_index:
            self.regs.YL = self.read_instruction_byte()
            self.psr.set_nz_8(self.regs.YL)
            return 2
        else:
            self.regs.Y = self.read_instruction_word()
            self.psr.set_nz_16(self.regs.Y)
            return 3
            
    def opcode_sta_absolute(self):
        """ STA abs - Store memory absolute. """
        address = self.read_instruction_word()
        if self.psr.byte_access:
            self.console.mem.write_byte(self.regs.DBR, address, self.regs.A)
            return 4
        else:
            self.console.mem.write_word(self.regs.DBR, address, self.regs.C)
            return 5
            
    def opcode_sta_absolute_long(self):
        """ STA long - Store memory absolute long. """
        address = self.read_instruction_word()
        bank = self.read_instruction_byte()
        if self.psr.byte_access:
            self.console.mem.write_byte(bank, address, self.regs.A)
            return 5
        else:
            self.console.mem.write_word(bank, address, self.regs.C)
            return 6
            
    def opcode_sta_absolute_long_x(self):
        """ STA long - Store memory absolute long + X. """
        address = self.read_instruction_word() + self.regs.X
        bank = self.read_instruction_byte()
        if self.psr.byte_access:
            self.console.mem.write_byte(bank, address, self.regs.A)
            return 5
        else:
            self.console.mem.write_word(bank, address, self.regs.C)
            return 6
            
    def opcode_tcd(self):
        """ TCD - Transfer 16-bit accumulator to direct page register. """
        self.regs.DP = self.regs.C
        return 2
        
    def opcode_tcs(self):
        """ TCS - Transfer 16-bit accumulator to stack register. """
        self.regs.SP = self.regs.C
        return 2
        
    def opcode_tya(self):
        """ TYA - Transfer Y to accumulator. """
        if self.psr.byte_access:
            self.regs.A = self.regs.YL
            self.psr.set_nz_8(self.regs.A)
        else:
            self.regs.C = self.regs.Y
            self.psr.set_nz_16(self.regs.C)
        return 2
        
    def opcode_tay(self):
        """ TAY - Transfer accumulator to Y. """
        if self.psr.byte_index:
            self.regs.YL = self.regs.A
            self.psr.set_nz_8(self.regs.YL)
        else:
            self.regs.Y = self.regs.C
            self.psr.set_nz_16(self.regs.Y)
        return 2
        
    def opcode_sbc_immediate(self):
        """ SBC imm - Subtract with borrow from accumulator. """
        assert not self.psr.decimal, "Not implemented yet!"
        if self.psr.byte_access:
            value = self.read_instruction_byte()
            self.regs.A = (self.regs.A - value) - (0 if self.psr.carry else 1)
            self.psr.set_nz_8(self.regs.A)
            return 2
        else:
            value = self.read_instruction_word()
            self.regs.C = (self.regs.C - value) - (0 if self.psr.carry else 1)
            self.psr.set_nz_16(self.regs.C)
            return 3
            
    def opcode_cmp_absolute(self):
        """ CMP abs - Compares the accumulator with the value at the given address. """
        address = self.read_instruction_word()
        if self.psr.byte_access:
            value = self.console.mem.read_byte(self.regs.DBR, address)
            result = self.regs.A - value
            self.psr.set_nz_8(self.regs.A)
            self.psr.borrow = self.regs.A < value
            return 4
        else:
            value = self.console.mem.read_word(self.regs.DBR, address)
            result = self.regs.C - value
            self.psr.set_nz_16(self.regs.C)
            self.psr.borrow = self.regs.C < value
            return 5
            
    def opcode_dex(self):
        """ DEX - Decrement X. """
        if self.psr.byte_index:
            self.regs.XL = self.regs.XL - 1
            self.psr.set_nz_8(self.regs.XL)
        else:
            self.regs.X = self.regs.X - 1
            self.psr.set_nz_16(self.regs.X)
        return 2
        
    def opcode_bpl(self):
        """ BPL - Branch if plus. """
        offset = self.read_instruction_byte()
        if not self.psr.negative:
            self.regs.PC += signed_byte(offset)
            return 3 # TODO: +1 for page boundary?
        else:
            return 2
            
    def opcode_jsr(self):
        """ JSR - Jump subroutine absolute. """
        destination = self.read_instruction_word()
        self._push_word(self.regs.PC)
        self.regs.PC = destination
        return 6
        
    def opcode_php(self):
        """ PHP - Push processor status register. """
        self._push_byte(self.psr.value)
        return 3
        