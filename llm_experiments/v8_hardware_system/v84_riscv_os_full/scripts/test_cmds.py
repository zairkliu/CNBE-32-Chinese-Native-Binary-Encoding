#!/usr/bin/env python3
import sys
# Generate Chinese commands as raw bytes
cmds = b""
cmds += b"\xE8\xBE\x93\xE5\x87\xBA(42)\n"      # 输出(42)
cmds += b"\xE5\x8F\x96\xE7\xBC\x96\xE7\xA0\x81(27743)\n"  # 取编码(27743) = 江
cmds += b"\xE5\xB8\xAE\xE5\x8A\xA9()\n"        # 帮助()
sys.stdout.buffer.write(cmds)