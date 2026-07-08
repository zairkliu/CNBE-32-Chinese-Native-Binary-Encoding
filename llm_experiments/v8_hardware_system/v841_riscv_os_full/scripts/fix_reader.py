#!/usr/bin/env python3
import os

path = os.path.expanduser("~/v84_riscv_os_full/src/editor/reader.c")
c = open(path).read()

if "LOAD-DDJ" in c:
    # Remove all lines containing LOAD-DDJ
    lines = c.split("\n")
    new_lines = []
    for line in lines:
        if "LOAD-DDJ" in line or "/* debug */" in line:
            continue
        if 'extern void uart_puts' in line and '//' not in line.split('extern')[0]:
            continue
        new_lines.append(line)
    c = "\n".join(new_lines)
    open(path, "w").write(c)
    print("Fixed: reverted debug code")
else:
    print("No LOAD-DDJ found, checking function...")

# Verify the reader_load_daodejing function
c = open(path).read()
if "reader_load_daodejing" in c:
    idx = c.find("void reader_load_daodejing(void)")
    if idx >= 0:
        snippet = c[idx:idx+300]
        print("reader_load_daodejing:")
        print(snippet[:200])
