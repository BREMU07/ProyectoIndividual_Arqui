import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parser import InstructionParseError, ParsedInstruction, parse_instruction  # noqa: E402


@pytest.mark.parametrize(
    "instruction, expected",
    [
        ("add x5, x6, x7", ParsedInstruction("add", "R", rd=5, rs1=6, rs2=7)),
        ("sub x5, x6, x7", ParsedInstruction("sub", "R", rd=5, rs1=6, rs2=7)),
        ("and x5, x6, x7", ParsedInstruction("and", "R", rd=5, rs1=6, rs2=7)),
        ("or x5, x6, x7", ParsedInstruction("or", "R", rd=5, rs1=6, rs2=7)),
        ("addi x10, x1, -12", ParsedInstruction("addi", "I", rd=10, rs1=1, imm=-12)),
        ("andi x10, x1, 15", ParsedInstruction("andi", "I", rd=10, rs1=1, imm=15)),
        ("lw x5, 8(x6)", ParsedInstruction("lw", "I", rd=5, rs1=6, imm=8)),
        ("lb x5, -1(x6)", ParsedInstruction("lb", "I", rd=5, rs1=6, imm=-1)),
        ("sw x8, -4(x2)", ParsedInstruction("sw", "S", rs1=2, rs2=8, imm=-4)),
        ("sb x8, 0(x2)", ParsedInstruction("sb", "S", rs1=2, rs2=8, imm=0)),
        ("beq x1, x2, 8", ParsedInstruction("beq", "B", rs1=1, rs2=2, imm=8)),
        ("bne x1, x2, -8", ParsedInstruction("bne", "B", rs1=1, rs2=2, imm=-8)),
    ],
)
def test_parses_each_supported_instruction(instruction, expected):
    assert parse_instruction(instruction) == expected


def test_tolerates_extra_whitespace():
    assert parse_instruction("add   x5 ,x6,  x7") == ParsedInstruction("add", "R", rd=5, rs1=6, rs2=7)
    assert parse_instruction("lw x5, 8 ( x6 )") == ParsedInstruction("lw", "I", rd=5, rs1=6, imm=8)


def test_mnemonic_is_case_insensitive():
    assert parse_instruction("ADD x5, x6, x7") == ParsedInstruction("add", "R", rd=5, rs1=6, rs2=7)


def test_x0_is_a_valid_register():
    assert parse_instruction("add x0, x0, x0") == ParsedInstruction("add", "R", rd=0, rs1=0, rs2=0)


def test_x31_is_a_valid_register():
    assert parse_instruction("add x31, x31, x31") == ParsedInstruction("add", "R", rd=31, rs1=31, rs2=31)


@pytest.mark.parametrize(
    "instruction",
    [
        "xor x5, x6, x7",  # mnemónico no soportado
        "add x32, x6, x7",  # registro fuera de rango
        "add 5, x6, x7",  # falta el prefijo x
        "addi x10, x1, abc",  # inmediato no numérico
        "addi x10, x1, 0x5",  # inmediato hexadecimal, no soportado
        "add x5, x6",  # faltan operandos
        "add x5, x6, x7, x8",  # sobran operandos
        "lw x5, 8 x6",  # paréntesis mal formados
        "",  # instrucción vacía
    ],
)
def test_rejects_invalid_instructions(instruction):
    with pytest.raises(InstructionParseError):
        parse_instruction(instruction)
