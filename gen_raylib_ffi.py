#!/usr/bin/env python3
"""
gen_raylib_ffi.py
Genera automáticamente un binding de raylib para LuaJIT usando FFI.
Uso: python3 gen_raylib_ffi.py [ruta/al/raylib.h] [-o salida.lua]
"""

import subprocess
import sys
import re
import argparse
from pathlib import Path


# Patrones a eliminar para que FFI no se queje
REMOVE_PATTERNS = [
    re.compile(r'__attribute__\s*\(\(.*?\)\)', re.DOTALL),
    re.compile(r'__extension__\s*'),
    re.compile(r'\b__restrict\b'),
    re.compile(r'\b__inline__\b'),
    re.compile(r'\b__inline\b'),
    re.compile(r'\b__const\b'),
    re.compile(r'\b__signed__\b'),
    re.compile(r'__asm__\s*\(.*?\)', re.DOTALL),
    re.compile(r'__nonnull\s*\(.*?\)'),
    re.compile(r'\b__wur\b'),
    re.compile(r'\b__THROW\b'),
    re.compile(r'\b__nothrow__\b'),
]

LUA_TEMPLATE = '''\
-- raylib_ffi.lua
-- Generado automáticamente por gen_raylib_ffi.py
-- NO editar manualmente

local ffi = require("ffi")

ffi.cdef([[
{cdef}
]])

local rl = ffi.load("raylib")

return rl
'''


def preprocess_header(header_path: str) -> str:
    """
    Corre gcc -E (CON marcadores de archivo) para saber
    qué líneas pertenecen al header pedido vs includes del sistema.
    """
    result = subprocess.run(
        ["gcc", "-E", "-x", "c", header_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Error al preprocesar:", result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def extract_from_header(raw: str, header_path: str) -> str:
    """
    Usa los marcadores # lineno "archivo" de gcc -E para quedarse
    SOLO con las líneas que provienen del header indicado.
    """
    abs_header = str(Path(header_path).resolve())
    lines = raw.splitlines()
    
    collecting = False
    result = []
    current_file = None
    
    for line in lines:
        # Detectar marcadores de archivo: # <num> "<archivo>" <flags>
        m = re.match(r'^#\s+\d+\s+"([^"]+)"', line)
        if m:
            current_file = str(Path(m.group(1)).resolve()) if m.group(1) not in ('<built-in>', '<command-line>') else m.group(1)
            collecting = (current_file == abs_header)
            continue
        
        if collecting:
            result.append(line)
    
    return "\n".join(result)


def clean_code(raw: str) -> str:
    """Limpia el código preprocesado para que FFI lo acepte."""
    lines = raw.splitlines()
    cleaned = []

    for line in lines:
        if line.startswith("#"):
            continue
        for pattern in REMOVE_PATTERNS:
            line = pattern.sub("", line)
        cleaned.append(line)

    code = "\n".join(cleaned)
    code = re.sub(r'\n{3,}', '\n\n', code)
    return code.strip()


def generate_ffi(header_path: str, output_path: str):
    print(f"[1/4] Preprocesando {header_path}...")
    raw = preprocess_header(header_path)

    print("[2/4] Extrayendo solo declaraciones del header...")
    raylib_section = extract_from_header(raw, header_path)
    
    if not raylib_section.strip():
        print("⚠  No se extrajo contenido — revisá la ruta del header", file=sys.stderr)
        sys.exit(1)

    print("[3/4] Limpiando código para FFI...")
    clean = clean_code(raylib_section)

    print(f"[4/4] Escribiendo {output_path}...")
    lua_code = LUA_TEMPLATE.format(cdef=clean)

    Path(output_path).write_text(lua_code, encoding="utf-8")
    lines = len(clean.splitlines())
    print(f"\n✓ Listo! Binding generado en: {output_path}")
    print(f"  Líneas de cdef: {lines}")


def main():
    parser = argparse.ArgumentParser(description="Genera binding LuaJIT FFI para raylib")
    parser.add_argument(
        "header",
        nargs="?",
        default="/usr/include/raylib.h",
        help="Ruta al header raylib.h (default: /usr/include/raylib.h)"
    )
    parser.add_argument(
        "-o", "--output",
        default="raylib_ffi.lua",
        help="Archivo Lua de salida (default: raylib_ffi.lua)"
    )
    args = parser.parse_args()

    if not Path(args.header).exists():
        print(f"Error: No se encontró el header en {args.header}", file=sys.stderr)
        print("Instalá raylib con: sudo apt install libraylib-dev", file=sys.stderr)
        print("O pasá la ruta manualmente: python3 gen_raylib_ffi.py /ruta/a/raylib.h", file=sys.stderr)
        sys.exit(1)

    generate_ffi(args.header, args.output)

    print("\nUso en LuaJIT:")
    print('  local rl = require("raylib_ffi")')
    print('  rl.InitWindow(800, 450, "Mi ventana")')


if __name__ == "__main__":
    main()
