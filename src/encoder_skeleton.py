#!/usr/bin/env python3
"""
Esqueleto del Codificador Educativo de Instrucciones RISC-V.
CE4301 Arquitectura de Computadores I — Proyecto Individual — 2026-II

Este esqueleto ya implementa el contrato de línea de comandos y de salida
requerido por la especificación. Usted debe completar las dos funciones
marcadas con TODO; puede modificar el resto del archivo si lo necesita,
siempre que se preserve el contrato de invocación y la línea "HEX: 0x...".

No es obligatorio usar este esqueleto ni Python: puede implementar su
propia herramienta desde cero, en el lenguaje que prefiera, siempre que
respete el mismo contrato (ver especificación, sección "Modo de operación").
"""
import sys

from encoders import encode, extract_bits
from parser import InstructionParseError, parse_instruction

SOPORTADAS = ["add", "sub", "and", "or", "addi", "andi",
              "lw", "lb", "sw", "sb", "beq", "bne"]

# Tabla de presentación: nombre, bit_alto, bit_bajo, rol. Puramente
# descriptiva (no la usan los encoders) — describe cómo mostrar los
# campos ya codificados en 'word' para cada formato.
CAMPOS_POR_FORMATO = {
    "R": [
        ("funct7", 31, 25, "Distingue variantes de la operación (ej. add/sub)"),
        ("rs2", 24, 20, "Registro fuente 2"),
        ("rs1", 19, 15, "Registro fuente 1"),
        ("funct3", 14, 12, "Selecciona la operación dentro del opcode"),
        ("rd", 11, 7, "Registro destino"),
        ("opcode", 6, 0, "Identifica el formato de la instrucción"),
    ],
    "I": [
        ("imm[11:0]", 31, 20, "Inmediato con signo (complemento a dos)"),
        ("rs1", 19, 15, "Registro fuente 1 / base de memoria"),
        ("funct3", 14, 12, "Selecciona la operación"),
        ("rd", 11, 7, "Registro destino"),
        ("opcode", 6, 0, "Identifica el formato de la instrucción"),
    ],
    "S": [
        ("imm[11:5]", 31, 25, "Bits altos del inmediato (offset de memoria)"),
        ("rs2", 24, 20, "Registro con el valor a almacenar"),
        ("rs1", 19, 15, "Registro base de memoria"),
        ("funct3", 14, 12, "Selecciona el tamaño del store (word/byte)"),
        ("imm[4:0]", 11, 7, "Bits bajos del inmediato"),
        ("opcode", 6, 0, "Identifica el formato de la instrucción"),
    ],
    "B": [
        ("imm[12|10:5]", 31, 25, "Bit de signo + bits altos del offset de salto"),
        ("rs2", 24, 20, "Registro fuente 2 (comparación)"),
        ("rs1", 19, 15, "Registro fuente 1 (comparación)"),
        ("funct3", 14, 12, "Selecciona la condición de salto (beq/bne)"),
        ("imm[4:1|11]", 11, 7, "Bits bajos del offset + bit 11"),
        ("opcode", 6, 0, "Identifica el formato de la instrucción"),
    ],
}


def encode_instruction(instruction: str) -> int:
    """
    Recibe una instrucción como texto, p. ej. "add x5, x6, x7", y debe
    retornar su codificación de 32 bits como entero (0 <= valor < 2**32).

    Debe soportar únicamente las instrucciones en SOPORTADAS. Los valores
    de opcode/funct3/funct7 de cada una NO se proveen aquí: deben
    investigarse en el manual oficial de la ISA RISC-V (ver referencia en
    la especificación) y documentarse en el README.
    """
    parsed = parse_instruction(instruction)
    return encode(parsed)


def explain_instruction(instruction: str, word: int) -> str:
    """
    Debe retornar un texto (para imprimirse en pantalla) que muestre, de
    forma visual, los 32 bits de 'word' divididos en los campos del
    formato correspondiente (R, I, S o B) — indicando el rango de bits y
    el valor de cada campo — junto con una breve explicación de cada uno.
    El formato visual (colores, tabla, arte ASCII, etc.) queda a su
    criterio, siempre que sea claro.
    """
    parsed = parse_instruction(instruction)
    fmt = parsed.fmt

    lineas = [
        f"Instrucción: {instruction.strip()}  ({parsed.mnemonic})",
        f"Formato: {fmt}",
        f"Binario (32 bits): {word:032b}",
        "",
        f"{'Campo':<14}{'Bits':<8}{'Binario':<14}{'Decimal':<10}Rol",
    ]
    for nombre, hi, lo, rol in CAMPOS_POR_FORMATO[fmt]:
        ancho = hi - lo + 1
        valor = extract_bits(word, hi, lo)
        rango = f"{hi}-{lo}" if hi != lo else str(hi)
        lineas.append(
            f"{nombre:<14}{rango:<8}{valor:0{ancho}b}".ljust(14 + 8 + 14)
            + f"{valor:<10}{rol}"
        )

    if fmt in ("S", "B"):
        lineas.append("")
        lineas.append(
            f"Inmediato reensamblado (fragmentos no contiguos): {parsed.imm} "
            "(decimal, complemento a dos)"
        )

    return "\n".join(lineas)


def main():
    # Fuerza UTF-8 en stdout/stderr: el encoding por defecto depende del
    # locale del sistema (en Windows suele ser cp1252) y corrompe tildes/ñ.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    if len(sys.argv) != 2:
        print(f'Uso: {sys.argv[0]} "<instruccion>"', file=sys.stderr)
        print(f'Ejemplo: {sys.argv[0]} "add x5, x6, x7"', file=sys.stderr)
        sys.exit(2)

    instruction = sys.argv[1]
    try:
        word = encode_instruction(instruction) & 0xFFFFFFFF
    except InstructionParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(explain_instruction(instruction, word))

    # No modificar el formato de la siguiente línea: la especificación la
    # requiere, literal, para permitir la validación automática.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()
