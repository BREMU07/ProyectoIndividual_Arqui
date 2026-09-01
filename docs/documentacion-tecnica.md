# Documentación técnica — Codificador Educativo de Instrucciones RISC-V

CE-4301 Arquitectura de Computadores I — Proyecto Individual — TEC.

Herramienta de línea de comandos que traduce una instrucción del subconjunto
RV32I indicado abajo a su codificación binaria de 32 bits, mostrando el
formato identificado, el binario completo, el desglose de campos y una breve
explicación del rol de cada uno.

## Índice

1. [Instrucciones soportadas](#1-instrucciones-soportadas)
2. [Fuente de los campos (opcode/funct3/funct7)](#2-fuente-de-los-campos-opcodefunct3funct7)
3. [Arquitectura del código](#3-arquitectura-del-código)
4. [Instalación y uso de la herramienta](#4-instalación-y-uso-de-la-herramienta)
5. [Instalación del toolchain RISC-V (para validación)](#5-instalación-del-toolchain-risc-v-para-validación)
6. [Ejemplos de salida (uno por formato)](#6-ejemplos-de-salida-uno-por-formato)
7. [Evidencia de validación (36 casos)](#7-evidencia-de-validación-36-casos)

---

## 1. Instrucciones soportadas

Únicamente estas 12 instrucciones del subconjunto RV32I. No se traducen
programas completos ni se resuelven etiquetas. Cada invocación codifica una
sola instrucción con operandos numéricos ya resueltos.

| Formato | Instrucciones |
|---|---|
| R | `add`, `sub`, `and`, `or` |
| I (aritmética) | `addi`, `andi` |
| I (carga) | `lw`, `lb` |
| S | `sw`, `sb` |
| B | `beq`, `bne` |

Sintaxis de operandos aceptada (idéntica a la del ensamblador GNU):

```
add  rd, rs1, rs2       # ej. add x5, x6, x7
addi rd, rs1, imm       # ej. addi x10, x1, -12
lw   rd, imm(rs1)       # ej. lw x5, 100(x6)
sw   rs2, imm(rs1)      # ej. sw x8, -4(x2)
beq  rs1, rs2, imm      # ej. beq x1, x2, 8   (imm = offset en bytes, con signo)
```

Los registros se aceptan como `x0`–`x31`. `x0` es un caso válido y probado
explícitamente (siempre vale 0, tanto en `rd` como en `rs1`/`rs2`).

## 2. Fuente de los campos (opcode/funct3/funct7)

Los valores de `opcode`, `funct3` y `funct7` no vienen especificados en el
enunciado del proyecto — se extrajeron de *The RISC-V Instruction Set
Manual, Volume I: User-Level ISA*, versión 20191213, capítulo 2 (codificación
de las instrucciones base RV32I) y capítulo 24 (mapa de opcodes), y se
verificaron empíricamente ensamblando cada instrucción con el toolchain
oficial (`riscv64-unknown-elf-as` + `objdump -d`, ver §5 y §7).

| Instrucción | Formato | Opcode | funct3 | funct7 |
|---|---|---|---|---|
| `add` | R | `0110011` | `000` | `0000000` |
| `sub` | R | `0110011` | `000` | `0100000` |
| `and` | R | `0110011` | `111` | `0000000` |
| `or` | R | `0110011` | `110` | `0000000` |
| `addi` | I | `0010011` | `000` | — |
| `andi` | I | `0010011` | `111` | — |
| `lw` | I | `0000011` | `010` | — |
| `lb` | I | `0000011` | `000` | — |
| `sw` | S | `0100011` | `010` | — |
| `sb` | S | `0100011` | `000` | — |
| `beq` | B | `1100011` | `000` | — |
| `bne` | B | `1100011` | `001` | — |

### Inmediatos negativos

Los inmediatos de los formatos I, S y B se manejan en complemento a dos.
Python representa los enteros negativos con signo "infinito" internamente,
así que antes de insertar un inmediato en la palabra de 32 bits se convierte
a su representación sin signo de N bits (`to_unsigned`, ver §3) — ej.
`to_unsigned(-12, 12)` → `0xFF4`.

### Ensamblado de inmediatos en S y B

Los formatos S y B no colocan el inmediato en un solo campo contiguo — es el
punto donde más fácilmente se introduce un error silencioso (el bit se
codifica, pero en la posición equivocada, y el resultado igual "parece" un
hex válido). Los rangos usados aquí están verificados contra el manual y
contra el toolchain (§7):

- **S**: `imm[11:5]` en los bits `31-25`, `imm[4:0]` en los bits `11-7`. El
  campo `rd` (usado por R/I en `11-7`) no existe en S — S no escribe en
  ningún registro — así que ese espacio se reutiliza para los bits bajos del
  inmediato.
- **B**: `imm[12]` en el bit `31`, `imm[10:5]` en los bits `30-25`,
  `imm[4:1]` en los bits `11-8`, `imm[11]` en el bit `7`. El bit 0 del
  inmediato nunca se codifica (siempre vale 0, porque los offsets de salto
  son múltiplos de 2 — direcciones de instrucción alineadas a 2 bytes), así
  que el inmediato representa en realidad 13 bits de rango con solo 12 bits
  almacenados. El orden "revuelto" de los fragmentos no es arbitrario.
  Mantiene `funct3`/`rs1`/`rs2`/`opcode` alineados con la misma posición que
  en S, y el bit de signo (`imm[12]`) siempre en el bit 31 de la palabra,
  para que el hardware pueda hacer sign-extend directo sin necesidad de
  reordenar bits primero.

## 3. Arquitectura del código

```
src/
  parser.py            texto de instrucción -> ParsedInstruction
  encoders.py           ParsedInstruction -> palabra de 32 bits (int)
  encoder_skeleton.py    orquestador/CLI: parsea argumentos, arma la salida
                         (formato, binario, desglose, línea HEX:)
run.sh                  punto de entrada fijo: ./run.sh "<instruccion>"
```

**`parser.py`** — convierte el texto de la instrucción (ej. `"lw x5,
8(x6)"`) en un `ParsedInstruction` (dataclass inmutable) con el mnemónico,
el formato (R/I/S/B) y los operandos que apliquen (`rd`, `rs1`, `rs2`,
`imm`). Valida
sintaxis y rango de registros (`x0`-`x31`) en la frontera de entrada; errores
de instrucción no soportada o sintaxis inválida se señalizan con
`InstructionParseError`, capturado en `main()` para salir limpio (stderr +
código de salida 1, sin traceback).

**`encoders.py`** — lógica pura de codificación, sin dependencias de E/S:

- **`INSTR_TABLE`** (`dict[str, InstrDef]`, `namedtuple` con
  `opcode`/`funct3`/`funct7`): fuente única de los valores ISA de las 12
  instrucciones (`funct7=None` en las que no lo usan). Evita repetir los
  mismos bits en varios lugares del código.
- **`to_unsigned(value, bits)`**: convierte un inmediato con signo a su
  representación de N bits en complemento a dos.
- **`extract_bits(value, hi, lo)`**: extrae el rango `[hi:lo]` inclusive de
  un entero. La usan `encode_s`/`encode_b` para partir el inmediato en
  fragmentos, y también `encoder_skeleton.py` para desglosar la palabra ya
  codificada al presentarla.
- **`encode_r`**: caso más simple — todos los campos son contiguos
  (`funct7|rs2|rs1|funct3|rd|opcode`), cada uno desplazado (`<<`) a su
  posición y combinado con OR bit a bit.
- **`encode_i`**: el inmediato de 12 bits va completo en `[31:20]`, sin
  partir. Una sola función sirve para `addi`/`andi`/`lw`/`lb` — la
  distinción entre ellas ya la resuelve `INSTR_TABLE` (opcode/funct3
  correctos) y el parser (`lw`/`lb` normalizan la sintaxis `imm(rs1)` al
  mismo `ParsedInstruction` que usa `addi`/`andi`).
- **`encode_s`** / **`encode_b`**: parten el inmediato según §2, usando
  `extract_bits` sobre la representación sin signo del inmediato
  (`to_unsigned`, 12 bits para S, 13 para B).
- **`encode()`**: dispatch por diccionario (`{"R": encode_r, ...}`) sobre
  `instr.fmt`, en vez de una cadena `if/elif` — el formato ya lo determinó
  el parser.

**`encoder_skeleton.py`** — punto de entrada de la CLI:

- `encode_instruction(text)`: `parse_instruction` → `encode`.
- `CAMPOS_POR_FORMATO`: tabla puramente descriptiva (nombre de campo, rango
  de bits, rol) por formato — vive aquí y no en `encoders.py` porque es
  presentación, no codificación; no la usa ningún encoder.
- `explain_instruction(text, word)`: arma el texto de salida — formato,
  binario de 32 bits, tabla de campos (rango, binario, decimal, rol) leída
  con `extract_bits` sobre la palabra ya codificada, y, para S/B, una línea
  adicional con el inmediato reensamblado (tomado directamente de
  `parsed.imm`, el valor autoritativo que ya calculó el parser — no se
  reconstruye a mano a partir de los fragmentos, para no duplicar la lógica
  de ensamblado del inmediato en dos lugares distintos).
- `main()`: valida argumentos (`sys.argv`), fuerza `stdout`/`stderr` a UTF-8
  (el encoding por defecto depende del locale del sistema operativo — en
  Windows suele ser `cp1252`, lo que corrompe tildes/ñ en la salida si no se
  fuerza explícitamente), captura `InstructionParseError`, e imprime el
  resultado terminando siempre con la línea `HEX: 0x` + 8 dígitos
  hexadecimales en minúscula.

## 4. Instalación y uso de la herramienta

Requiere Python 3.10+ (usa sintaxis `dict[str, InstrDef]`) y `bash` (para
`run.sh`) — en Windows, Git Bash o WSL sirven.

```bash
git clone <url-del-repo>
cd ProyectoIndividual_Arqui
./run.sh "add x5, x6, x7"
```

No hay dependencias externas de Python para la herramienta en sí (solo la
biblioteca estándar). `requirements-dev.txt` (`pytest`) es únicamente para
correr la suite de tests, no hace falta para usar `./run.sh`:

```bash
pip install -r requirements-dev.txt
pytest tests/
```

`./run.sh "<instruccion>"` es el único punto de entrada soportado. Si la
instrucción no está soportada o tiene sintaxis inválida, el programa termina
con código de salida 1 y un mensaje de error en `stderr`, sin generar la
línea `HEX:`.

## 5. Instalación del toolchain RISC-V (para validación)

El toolchain **no** es una dependencia de la herramienta — solo se usa para
generar la codificación de referencia contra la cual se validó el
codificador propio (§7). Se instaló en WSL (Ubuntu 22.04):

```bash
wsl -e bash -c "sudo apt update && sudo apt install -y gcc-riscv64-unknown-elf"
```

Pese a que el paquete se llama `riscv64-unknown-elf`, es multilib y soporta
`rv32i` con las banderas correctas:

```bash
riscv64-unknown-elf-as -march=rv32i -mabi=ilp32 -o caso.o caso.s
riscv64-unknown-elf-objdump -d caso.o
```

Como verificación inicial del toolchain se ensambló y desensambló el caso
trivial `add x5, x6, x7`, dando `007302b3`. Coincide con la codificación
propia (el objeto generado usa el formato `elf32-littleriscv`).

`objdump -d` imprime los registros con sus nombres ABI (`t0`, `ra`, `sp`,
`a0`, `s0`, …) en vez de `x5`/`x1`/`x2`/`x10`/`x8`. Al comparar contra la
salida propia (que usa siempre `xN`) hay que mapear el nombre ABI al número
de registro correspondiente — no es una discrepancia real, solo una
diferencia de nomenclatura en la presentación de `objdump`.

Estos binarios son accesibles desde Windows invocándolos vía
`wsl -e bash -c "..."`, sin necesidad de abrir una terminal WSL aparte.

## 6. Ejemplos de salida (uno por formato)

Salida real de `./run.sh`, una instrucción de cada formato.

### R — `./run.sh "add x7, x20, x6"`

```
Instrucción: add x7, x20, x6  (add)
Formato: R
Binario (32 bits): 00000000011010100000001110110011

Campo         Bits    Binario       Decimal   Rol
funct7        31-25   0000000       0         Distingue variantes de la operación (ej. add/sub)
rs2           24-20   00110         6         Registro fuente 2
rs1           19-15   10100         20        Registro fuente 1
funct3        14-12   000           0         Selecciona la operación dentro del opcode
rd            11-7    00111         7         Registro destino
opcode        6-0     0110011       51        Identifica el formato de la instrucción
HEX: 0x006a03b3
```

### I — `./run.sh "addi x10, x1, -12"`

```
Instrucción: addi x10, x1, -12  (addi)
Formato: I
Binario (32 bits): 11111111010000001000010100010011

Campo         Bits    Binario       Decimal   Rol
imm[11:0]     31-20   111111110100  4084      Inmediato con signo (complemento a dos)
rs1           19-15   00001         1         Registro fuente 1 / base de memoria
funct3        14-12   000           0         Selecciona la operación
rd            11-7    01010         10        Registro destino
opcode        6-0     0010011       19        Identifica el formato de la instrucción
HEX: 0xff408513
```

`imm[11:0]` se muestra en decimal como el valor sin signo del campo de 12
bits (4084 = `0xFF4`); el inmediato con signo real (`-12`) se puede leer
directamente del texto de la instrucción — para I no hace falta
reensamblar nada porque el campo ya es contiguo.

### S — `./run.sh "sw x8, -4(x2)"`

```
Instrucción: sw x8, -4(x2)  (sw)
Formato: S
Binario (32 bits): 11111110100000010010111000100011

Campo         Bits    Binario       Decimal   Rol
imm[11:5]     31-25   1111111       127       Bits altos del inmediato (offset de memoria)
rs2           24-20   01000         8         Registro con el valor a almacenar
rs1           19-15   00010         2         Registro base de memoria
funct3        14-12   010           2         Selecciona el tamaño del store (word/byte)
imm[4:0]      11-7    11100         28        Bits bajos del inmediato
opcode        6-0     0100011       35        Identifica el formato de la instrucción

Inmediato reensamblado (fragmentos no contiguos): -4 (decimal, complemento a dos)
HEX: 0xfe812e23
```

### B — `./run.sh "beq x1, x2, 8"`

```
Instrucción: beq x1, x2, 8  (beq)
Formato: B
Binario (32 bits): 00000000001000001000010001100011

Campo         Bits    Binario       Decimal   Rol
imm[12|10:5]  31-25   0000000       0         Bit de signo + bits altos del offset de salto
rs2           24-20   00010         2         Registro fuente 2 (comparación)
rs1           19-15   00001         1         Registro fuente 1 (comparación)
funct3        14-12   000           0         Selecciona la condición de salto (beq/bne)
imm[4:1|11]   11-7    01000         8         Bits bajos del offset + bit 11
opcode        6-0     1100011       99        Identifica el formato de la instrucción

Inmediato reensamblado (fragmentos no contiguos): 8 (decimal, complemento a dos)
HEX: 0x00208463
```

## 7. Evidencia de validación (36 casos)

Evidencia de validación del codificador para las 12 instrucciones
soportadas, exigida en el enunciado del proyecto (mínimo 36 casos, 12
instrucciones × 3 casos cada una — positivo, negativo, límite — cubriendo
además `x0`, inmediatos máximo/mínimo representables y desplazamiento cero
en saltos).

Estos 36 casos son **propios**, diseñados específicamente para esta
evidencia — no son los mismos que `docs/kit/vectores_ejemplo.txt` (ese
archivo es solo para autochequeo rápido y no sustituye esta validación).

### Metodología

Para cada instrucción:

1. Se ensambló con el toolchain oficial (`riscv64-unknown-elf-as`, target
   `rv32i`/`ilp32`, corrido desde WSL con Ubuntu — el paquete
   `gcc-riscv64-unknown-elf` de apt, aunque su nombre diga "riscv64", es
   multilib y soporta `rv32i`, ver §5).
2. Se desensambló con `riscv64-unknown-elf-objdump -d` para obtener la
   codificación hexadecimal de referencia.
3. Se comparó bit a bit contra la salida de `encode_instruction()` (el mismo
   código que expone `./run.sh`) para la misma instrucción.

Las instrucciones de formato R, I y S no requieren ningún tratamiento
especial. Se ensamblan directamente como una sola instrucción porque sus
operandos son literales (registros e inmediatos), sin símbolos que el
ensamblador deba resolver.

#### Caso especial: `beq`/`bne`

Al validar manualmente se detectó que el ensamblador GNU **no** genera una
sola instrucción para `beq`/`bne` cuando el operando de desplazamiento es un
literal numérico "pelado" (ej. `beq x1, x2, 100`). Lo expande a un salto
invertido + `j`, porque trata ese operando como una expresión que podría
necesitar reubicación. El workaround usado aquí es ensamblar con una
**etiqueta real** ubicada exactamente al offset deseado, en vez del literal,
usando la directiva `.org` para posicionar la etiqueta (o la instrucción de
salto) en la dirección exacta dentro de la sección `.text` — así el offset
se resuelve localmente en tiempo de ensamblado y el ensamblador sí emite una
única instrucción de 4 bytes.

Ejemplo para `beq x1, x2, 100` (offset positivo):

```asm
.text
_start:
    beq x1, x2, target
    .org 100
target:
    nop
```

Para un offset negativo, la etiqueta se coloca antes y se usa `.org` para
avanzar el contador de ubicación hasta la dirección donde debe quedar la
instrucción de salto:

```asm
.text
_start:
target2:
    .org 100
    beq x3, x4, target2
```

Para el caso de desplazamiento cero (`beq x5, x6, 0`), la etiqueta apunta a
la propia instrucción de salto:

```asm
.text
_start:
target3:
    beq x5, x6, target3
```

Cada uno de los 6 casos de formato B se ensambló en su propio archivo `.s`
con esta técnica; los 30 casos de R/I/S se ensamblaron juntos en un solo
archivo (uno por línea) ya que no requieren etiquetas.

#### Comandos usados

```bash
riscv64-unknown-elf-as -march=rv32i -mabi=ilp32 -o caso.o caso.s
riscv64-unknown-elf-objdump -d caso.o
```

### Resultado: 36/36 coinciden

| Instrucción | Formato | Categoría | Codificación propia | Codificación toolchain (objdump) | Coincide |
|---|---|---|---|---|---|
| `add x5, x6, x7` | R | normal | `0x007302b3` | `0x007302b3` | sí |
| `add x0, x12, x13` | R | rd = x0 | `0x00d60033` | `0x00d60033` | sí |
| `add x31, x31, x31` | R | registros límite (x31) | `0x01ff8fb3` | `0x01ff8fb3` | sí |
| `sub x10, x20, x3` | R | normal | `0x403a0533` | `0x403a0533` | sí |
| `sub x15, x0, x9` | R | rs1 = x0 | `0x409007b3` | `0x409007b3` | sí |
| `sub x1, x31, x0` | R | rs2 = x0, registro límite | `0x400f80b3` | `0x400f80b3` | sí |
| `and x8, x14, x22` | R | normal | `0x01677433` | `0x01677433` | sí |
| `and x0, x5, x6` | R | rd = x0 | `0x0062f033` | `0x0062f033` | sí |
| `and x31, x0, x31` | R | rs1 = x0, registro límite | `0x01f07fb3` | `0x01f07fb3` | sí |
| `or x12, x18, x25` | R | normal | `0x01996633` | `0x01996633` | sí |
| `or x9, x0, x0` | R | rs1 = rs2 = x0 | `0x000064b3` | `0x000064b3` | sí |
| `or x31, x30, x29` | R | registros límite | `0x01df6fb3` | `0x01df6fb3` | sí |
| `addi x5, x6, 500` | I (aritmética) | positivo | `0x1f430293` | `0x1f430293` | sí |
| `addi x7, x8, -500` | I (aritmética) | negativo | `0xe0c40393` | `0xe0c40393` | sí |
| `addi x9, x10, 2047` | I (aritmética) | límite máximo (2¹¹−1) | `0x7ff50493` | `0x7ff50493` | sí |
| `andi x11, x12, 300` | I (aritmética) | positivo | `0x12c67593` | `0x12c67593` | sí |
| `andi x13, x14, -300` | I (aritmética) | negativo | `0xed477693` | `0xed477693` | sí |
| `andi x15, x16, -2048` | I (aritmética) | límite mínimo (−2¹¹) | `0x80087793` | `0x80087793` | sí |
| `lw x5, 100(x6)` | I (carga) | positivo | `0x06432283` | `0x06432283` | sí |
| `lw x7, -100(x8)` | I (carga) | negativo | `0xf9c42383` | `0xf9c42383` | sí |
| `lw x9, 2047(x10)` | I (carga) | límite máximo | `0x7ff52483` | `0x7ff52483` | sí |
| `lb x11, 50(x12)` | I (carga) | positivo | `0x03260583` | `0x03260583` | sí |
| `lb x13, -50(x14)` | I (carga) | negativo | `0xfce70683` | `0xfce70683` | sí |
| `lb x15, -2048(x16)` | I (carga) | límite mínimo | `0x80080783` | `0x80080783` | sí |
| `sw x5, 200(x6)` | S | positivo | `0x0c532423` | `0x0c532423` | sí |
| `sw x7, -200(x8)` | S | negativo | `0xf2742c23` | `0xf2742c23` | sí |
| `sw x9, 2047(x10)` | S | límite máximo | `0x7e952fa3` | `0x7e952fa3` | sí |
| `sb x11, 75(x12)` | S | positivo | `0x04b605a3` | `0x04b605a3` | sí |
| `sb x13, -75(x14)` | S | negativo | `0xfad70aa3` | `0xfad70aa3` | sí |
| `sb x15, -2048(x16)` | S | límite mínimo | `0x80f80023` | `0x80f80023` | sí |
| `beq x1, x2, 100` | B | positivo | `0x06208263` | `0x06208263` | sí |
| `beq x3, x4, -100` | B | negativo | `0xf8418ee3` | `0xf8418ee3` | sí |
| `beq x5, x6, 0` | B | desplazamiento cero | `0x00628063` | `0x00628063` | sí |
| `bne x7, x0, 20` | B | positivo, rs2 = x0 | `0x00039a63` | `0x00039a63` | sí |
| `bne x9, x10, 4094` | B | límite máximo (13 bits, offset par) | `0x7ea49fe3` | `0x7ea49fe3` | sí |
| `bne x11, x12, -4096` | B | límite mínimo (13 bits, offset par) | `0x80c59063` | `0x80c59063` | sí |

**36/36 casos coinciden bit a bit con la codificación del toolchain oficial.**

Para el formato R, al no tener campo de inmediato, la categorización
"positivo/negativo/límite" se adaptó a variaciones de registros (caso
normal, uso de `x0`, registros en el límite superior `x31`), que es donde
puede haber errores de codificación en ese formato.
