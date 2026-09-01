# Codificador Educativo de Instrucciones RISC-V

Proyecto Individual, CE-4301 Arquitectura de Computadores I, TEC, S2 2026.

Traduce una instrucción del subconjunto RV32I a su codificación binaria de
32 bits. Documentación técnica completa (instrucciones soportadas, fuentes
de los campos, arquitectura del código y evidencia de validación) en
`docs/documentacion-tecnica.md`.

## Requisitos

- Python 3.10 o superior.
- Una shell compatible con `bash` para correr `run.sh` (en Linux/macOS ya
  está disponible; en Windows sirve Git Bash o WSL).

No hay dependencias externas de Python para la herramienta en sí, solo la
biblioteca estándar.

## Preparación del entorno

```bash
git clone <url-del-repo>
cd ProyectoIndividual_Arqui
chmod +x run.sh
```

Con eso `./run.sh` queda listo para usarse.

### Dependencias de desarrollo (opcional, solo para correr los tests)

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## Verificación

```bash
./run.sh "add x5, x6, x7"
```

La última línea de la salida debe ser `HEX: 0x007302b3`.
