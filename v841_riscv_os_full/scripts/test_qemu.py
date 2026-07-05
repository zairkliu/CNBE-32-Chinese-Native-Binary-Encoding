#!/usr/bin/env python3
'''Test v8.4.1 OS interactive commands via QEMU serial.'''

import subprocess
import os
import time
import select
import sys

HOME = os.path.expanduser("~")
KERNEL = os.path.join(HOME, "v84_riscv_os_full", "output", "kernel.bin")


def run_qemu(timeout=5):
    """Run QEMU, send commands, capture output."""
    qemu = subprocess.Popen(
        [
            "qemu-system-riscv64",
            "-machine", "virt",
            "-bios", "none",
            "-device", "loader,file=" + KERNEL + ",addr=0x80000000",
            "-serial", "stdio",
            "-monitor", "none",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    time.sleep(0.5)

    output = b""
    end_time = time.time() + timeout

    def read_output():
        nonlocal output
        while True:
            r, _, _ = select.select([qemu.stdout], [], [], 0.2)
            if r:
                data = qemu.stdout.read(8192)
                if not data:
                    break
                output += data
            else:
                break

    def send_cmd(cmd):
        nonlocal output
        qemu.stdin.write(cmd.encode() if isinstance(cmd, str) else cmd)
        qemu.stdin.flush()
        time.sleep(0.3)
        read_output()

    read_output()  # Read boot
    print("=== BOOT ===")
    print(output.decode("utf-8", errors="replace"))

    send_cmd("test\r")
    send_cmd("输出(42)\r")

    print("=== RESULT ===")
    print(output.decode("utf-8", errors="replace"))

    qemu.terminate()
    qemu.wait()
    return output


if __name__ == "__main__":
    run_qemu()
