import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from encoder_skeleton import encode_instruction  # noqa: E402
from encoders import extract_bits, to_unsigned  # noqa: E402

KIT_VECTORS_PATH = Path(__file__).resolve().parents[1] / "docs" / "kit" / "vectores_ejemplo.txt"


def _load_kit_vectors():
    vectors = []
    for line in KIT_VECTORS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        instr, expected = line.split(";")
        vectors.append((instr.strip(), int(expected.strip(), 16)))
    return vectors


@pytest.mark.parametrize(
    "value, bits, expected",
    [
        (0, 12, 0x000),
        (2047, 12, 0x7FF),
        (-1, 12, 0xFFF),
        (-2048, 12, 0x800),
        (-12, 12, 0xFF4),
    ],
)
def test_to_unsigned(value, bits, expected):
    assert to_unsigned(value, bits) == expected


@pytest.mark.parametrize(
    "value, hi, lo, expected",
    [
        (0xFF4, 11, 5, 0x7F),
        (0xFF4, 4, 0, 0x14),
        (0b1_0101010_1_0101, 12, 12, 1),
        (0b1_0101010_1_0101, 10, 5, 0b101010),
    ],
)
def test_extract_bits(value, hi, lo, expected):
    assert extract_bits(value, hi, lo) == expected


@pytest.mark.parametrize("instruction, expected", _load_kit_vectors())
def test_encode_instruction_matches_kit_vectors(instruction, expected):
    assert encode_instruction(instruction) == expected


def test_encode_instruction_treats_x0_as_zero():
    assert encode_instruction("add x28, x15, x0") == 0x00078E33
