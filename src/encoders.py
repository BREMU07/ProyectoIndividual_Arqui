"""Codificadores RV32I: ParsedInstruction -> palabra de 32 bits.
"""
from collections import namedtuple

from parser import ParsedInstruction

InstrDef = namedtuple("InstrDef", ["opcode", "funct3", "funct7"])

INSTR_TABLE: dict[str, InstrDef] = {
    "add":  InstrDef(0b0110011, 0b000, 0b0000000),
    "sub":  InstrDef(0b0110011, 0b000, 0b0100000),
    "and":  InstrDef(0b0110011, 0b111, 0b0000000),
    "or":   InstrDef(0b0110011, 0b110, 0b0000000),
    "addi": InstrDef(0b0010011, 0b000, None),
    "andi": InstrDef(0b0010011, 0b111, None),
    "lw":   InstrDef(0b0000011, 0b010, None),
    "lb":   InstrDef(0b0000011, 0b000, None),
    "sw":   InstrDef(0b0100011, 0b010, None),
    "sb":   InstrDef(0b0100011, 0b000, None),
    "beq":  InstrDef(0b1100011, 0b000, None),
    "bne":  InstrDef(0b1100011, 0b001, None),
}


def to_unsigned(value: int, bits: int) -> int:
    """Convierte un entero con signo a su representacion sin signo en 'bits' bits (two's complement)."""
    return value & ((1 << bits) - 1)


def extract_bits(value: int, hi: int, lo: int) -> int:
    """Extrae el rango de bits [hi:lo] (inclusive) de 'value'."""
    return (value >> lo) & ((1 << (hi - lo + 1)) - 1)


def encode_r(instr: ParsedInstruction) -> int:
    d = INSTR_TABLE[instr.mnemonic]
    return (
        (d.funct7 << 25)
        | (instr.rs2 << 20)
        | (instr.rs1 << 15)
        | (d.funct3 << 12)
        | (instr.rd << 7)
        | d.opcode
    )


def encode_i(instr: ParsedInstruction) -> int:
    d = INSTR_TABLE[instr.mnemonic]
    imm = to_unsigned(instr.imm, 12)
    return (
        (imm << 20)
        | (instr.rs1 << 15)
        | (d.funct3 << 12)
        | (instr.rd << 7)
        | d.opcode
    )


def encode_s(instr: ParsedInstruction) -> int:
    d = INSTR_TABLE[instr.mnemonic]
    imm = to_unsigned(instr.imm, 12)
    imm_11_5 = extract_bits(imm, 11, 5)
    imm_4_0 = extract_bits(imm, 4, 0)
    return (
        (imm_11_5 << 25)
        | (instr.rs2 << 20)
        | (instr.rs1 << 15)
        | (d.funct3 << 12)
        | (imm_4_0 << 7)
        | d.opcode
    )


def encode_b(instr: ParsedInstruction) -> int:
    d = INSTR_TABLE[instr.mnemonic]
    imm = to_unsigned(instr.imm, 13)
    imm_12 = extract_bits(imm, 12, 12)
    imm_10_5 = extract_bits(imm, 10, 5)
    imm_4_1 = extract_bits(imm, 4, 1)
    imm_11 = extract_bits(imm, 11, 11)
    return (
        (imm_12 << 31)
        | (imm_10_5 << 25)
        | (instr.rs2 << 20)
        | (instr.rs1 << 15)
        | (d.funct3 << 12)
        | (imm_4_1 << 8)
        | (imm_11 << 7)
        | d.opcode
    )


_ENCODERS = {
    "R": encode_r,
    "I": encode_i,
    "S": encode_s,
    "B": encode_b,
}


def encode(instr: ParsedInstruction) -> int:
    """Codifica una ParsedInstruction ya parseada a su palabra de 32 bits."""
    return _ENCODERS[instr.fmt](instr)
