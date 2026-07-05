"""
CNBE-32 Encoding Utility — Core encoding module for all experiments.
Usage: python encode.py <text> [--format A|C|D|F] [--table path/to/skill_table.npy]
       python encode.py --batch <file> [--format A|C|D|F]
"""

import numpy as np
import sys
import os

# Path relative to repo root
DEFAULT_TABLE = os.path.join(os.path.dirname(__file__), 
    "..", "..", "riscv", "skill_table", "skill_table_8105.npy")

def load_table(path=None):
    """Load CNBE skill table from .npy file."""
    if path is None:
        path = DEFAULT_TABLE
    if not os.path.exists(path):
        raise FileNotFoundError(f"Skill table not found at {path}. "
            "Pull the repo first: git clone https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding.git")
    return np.load(path)

def encode(text, table, fmt="A"):
    """
    Encode Chinese text with CNBE encoding.
    
    Formats:
      A - Per-character annotation: 中(丨,4画,独体)
      C - Bracket numeric: 中[039,08,02]
      D - Space separated: 中 039 08 02
      F - Bare packed: 中0390802
    """
    result = []
    for ch in text.strip():
        idx = ord(ch) - 0x4E00
        if 0 <= idx < len(table):
            code = int(table[idx])
            if code <= 0:
                result.append(ch)
                continue
            radical = (code >> 24) & 0xFF
            stroke = (code >> 19) & 0x1F
            structure = (code >> 15) & 0xF
            if fmt == "A":
                result.append(f"{ch}({radical:03d},{stroke:02d}画,{structure:02d}型)")
            elif fmt == "C":
                result.append(f"{ch}[{radical:03d},{stroke:02d},{structure:02d}]")
            elif fmt == "D":
                result.append(f"{ch} {radical:03d} {stroke:02d} {structure:02d}")
            elif fmt == "F":
                result.append(f"{ch}{radical:03d}{stroke:02d}{structure:02d}")
            else:
                result.append(ch)
        else:
            result.append(ch)
    return "".join(result)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CNBE-32 Encoder")
    parser.add_argument("text", nargs="?", help="Text to encode")
    parser.add_argument("--format", "-f", choices=["A","C","D","F"], default="A")
    parser.add_argument("--table", "-t", default=None)
    parser.add_argument("--batch", "-b", help="Batch encode from file")
    
    args = parser.parse_args()
    table = load_table(args.table)
    
    if args.batch:
        with open(args.batch, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    print(encode(line, table, args.format))
    elif args.text:
        print(encode(args.text, table, args.format))
    else:
        # Interactive test
        test = "你好世界"
        print(f"Original: {test}")
        print(f"Format A: {encode(test, table, 'A')}")
        print(f"Format C: {encode(test, table, 'C')}")
        print(f"Format F: {encode(test, table, 'F')}")
