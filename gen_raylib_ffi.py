#!/usr/bin/env python3
"""
gen_raylib_ffi.py`
Automatically generates a raylib binding for LuaJIT using FFI.
Usage: `python3 gen_raylib_ffi.py [path/to/raylib.h] [-o output.lua]
"""

import subprocess
import sys
import re
import argparse
from pathlib import Path


# Patterns to eliminate so FFI doesn't complain
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
-- Generated automatically by gen_raylib_ffi.py
-- DO NOT edit manually

local ffi = require("ffi")

ffi.cdef([[
{cdef}
]])

local rl = ffi.load("raylib")

return rl
'''


def preprocess_header(header_path: str) -> str:
    """
    Run gcc -E (WITH file markers) to find out
    which lines belong to the requested header vs system includes.
    """
    result = subprocess.run(
        ["gcc", "-E", "-x", "c", header_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Error preprocessing:", result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def extract_from_header(raw: str, header_path: str) -> str:
    """
    Use the `# lineno "archivo"` markers in `gcc -E` to keep only the lines that come 
    from the specified header.
    """
    abs_header = str(Path(header_path).resolve())
    lines = raw.splitlines()
    
    collecting = False
    result = []
    current_file = None
    
    for line in lines:
        # Detect file markers: # <num> "<file>" <flags>
        m = re.match(r'^#\s+\d+\s+"([^"]+)"', line)
        if m:
            current_file = str(Path(m.group(1)).resolve()) if m.group(1) not in ('<built-in>', '<command-line>') else m.group(1)
            collecting = (current_file == abs_header)
            continue
        
        if collecting:
            result.append(line)
    
    return "\n".join(result)


def clean_code(raw: str) -> str:
    """Clean the preprocessed code so that FFI will accept it."""
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
    print(f"[1/4] Processing {header_path}...")
    raw = preprocess_header(header_path)

    print("[2/4] Extracting only header declarations...")
    raylib_section = extract_from_header(raw, header_path)
    
    if not raylib_section.strip():
        print("⚠  No content was extracted — check the header path", file=sys.stderr)
        sys.exit(1)

    print("[3/4] Cleaning up code for FFI...")
    clean = clean_code(raylib_section)

    print(f"[4/4] Writing {output_path}...")
    lua_code = LUA_TEMPLATE.format(cdef=clean)

    Path(output_path).write_text(lua_code, encoding="utf-8")
    lines = len(clean.splitlines())
    print(f"\n✓ Done! Binding generated in: {output_path}")
    print(f"  cdef lines: {lines}")


def main():
    parser = argparse.ArgumentParser(description="Generate LuaJIT FFI binding for raylib")
    parser.add_argument(
        "header",
        nargs="?",
        default="/usr/include/raylib.h",
        help="Path to the raylib.h header (default: /usr/include/raylib.h)"
    )
    parser.add_argument(
        "-o", "--output",
        default="raylib_ffi.lua",
        help="Lua output file (default: raylib_ffi.lua)"
    )
    args = parser.parse_args()

    if not Path(args.header).exists():
        print(f"Error: The header was not found in {args.header}", file=sys.stderr)
        print("Install raylib with: sudo apt install libraylib-dev", file=sys.stderr)
        print("Or enter the route manually: python3 gen_raylib_ffi.py /ruta/a/raylib.h", file=sys.stderr)
        sys.exit(1)

    generate_ffi(args.header, args.output)


if __name__ == "__main__":
    main()
