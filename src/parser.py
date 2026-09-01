"""Parser de instrucciones RV32I: texto -> ParsedInstruction."""
import re
from dataclasses import dataclass
from typing import Optional

R_MNEMONICS = {"add", "sub", "and", "or"}
I_ARITH_MNEMONICS = {"addi", "andi"}
I_LOAD_MNEMONICS = {"lw", "lb"}
S_MNEMONICS = {"sw", "sb"}
B_MNEMONICS = {"beq", "bne"}

SUPPORTED_MNEMONICS = (
    R_MNEMONICS | I_ARITH_MNEMONICS | I_LOAD_MNEMONICS | S_MNEMONICS | B_MNEMONICS
)

_REG = r"x(\d{1,2})"
_IMM = r"(-?\d+)"
_WS = r"\s*"

_R_RE = re.compile(rf"^{_REG}{_WS},{_WS}{_REG}{_WS},{_WS}{_REG}$")
_I_ARITH_RE = re.compile(rf"^{_REG}{_WS},{_WS}{_REG}{_WS},{_WS}{_IMM}$")
_MEM_RE = re.compile(rf"^{_REG}{_WS},{_WS}{_IMM}{_WS}\({_WS}{_REG}{_WS}\)$")
_B_RE = re.compile(rf"^{_REG}{_WS},{_WS}{_REG}{_WS},{_WS}{_IMM}$")


class InstructionParseError(ValueError):
    """Entrada no soportada o sintaxis inválida."""


@dataclass(frozen=True)
class ParsedInstruction:
    mnemonic: str
    fmt: str
    rd: Optional[int] = None
    rs1: Optional[int] = None
    rs2: Optional[int] = None
    imm: Optional[int] = None


def _reg(text: str, match: "re.Match", group: int) -> int:
    value = int(match.group(group))
    if not 0 <= value <= 31:
        raise InstructionParseError(
            f'registro fuera de rango "x{value}" en "{text}" (debe ser x0-x31)'
        )
    return value


def parse_instruction(instruction: str) -> ParsedInstruction:
    """Parsea una instrucción RV32I soportada y devuelve su representación intermedia."""
    stripped = instruction.strip()
    parts = stripped.split(maxsplit=1)
    if not parts:
        raise InstructionParseError("instrucción vacía")

    mnemonic = parts[0].lower()
    operands = parts[1].strip() if len(parts) > 1 else ""

    if mnemonic not in SUPPORTED_MNEMONICS:
        raise InstructionParseError(
            f'mnemónico no soportado: "{parts[0]}" (soportadas: {sorted(SUPPORTED_MNEMONICS)})'
        )

    if mnemonic in R_MNEMONICS:
        m = _R_RE.match(operands)
        if not m:
            raise InstructionParseError(f'sintaxis inválida para "{mnemonic}": "{instruction}"')
        return ParsedInstruction(
            mnemonic=mnemonic,
            fmt="R",
            rd=_reg(instruction, m, 1),
            rs1=_reg(instruction, m, 2),
            rs2=_reg(instruction, m, 3),
        )

    if mnemonic in I_ARITH_MNEMONICS:
        m = _I_ARITH_RE.match(operands)
        if not m:
            raise InstructionParseError(f'sintaxis inválida para "{mnemonic}": "{instruction}"')
        return ParsedInstruction(
            mnemonic=mnemonic,
            fmt="I",
            rd=_reg(instruction, m, 1),
            rs1=_reg(instruction, m, 2),
            imm=int(m.group(3)),
        )

    if mnemonic in I_LOAD_MNEMONICS:
        m = _MEM_RE.match(operands)
        if not m:
            raise InstructionParseError(f'sintaxis inválida para "{mnemonic}": "{instruction}"')
        return ParsedInstruction(
            mnemonic=mnemonic,
            fmt="I",
            rd=_reg(instruction, m, 1),
            rs1=_reg(instruction, m, 3),
            imm=int(m.group(2)),
        )

    if mnemonic in S_MNEMONICS:
        m = _MEM_RE.match(operands)
        if not m:
            raise InstructionParseError(f'sintaxis inválida para "{mnemonic}": "{instruction}"')
        return ParsedInstruction(
            mnemonic=mnemonic,
            fmt="S",
            rs2=_reg(instruction, m, 1),
            rs1=_reg(instruction, m, 3),
            imm=int(m.group(2)),
        )

    if mnemonic in B_MNEMONICS:
        m = _B_RE.match(operands)
        if not m:
            raise InstructionParseError(f'sintaxis inválida para "{mnemonic}": "{instruction}"')
        return ParsedInstruction(
            mnemonic=mnemonic,
            fmt="B",
            rs1=_reg(instruction, m, 1),
            rs2=_reg(instruction, m, 2),
            imm=int(m.group(3)),
        )

    raise InstructionParseError(f'mnemónico no manejado: "{mnemonic}"')
