#!/usr/bin/env python3
"""Test v8.4.1 OS interactively via QEMU serial."""
import subprocess
import os
import time
import select

HOME = os.path.expanduser("~")
KERNEL = os.path.join(HOME, "v84_riscv_os_full", "output", "kernel.bin")


def read_output(qemu, timeout=0.5):
    """Read available QEMU output with timeout."""
    data = b""
    end = time.time() + timeout
    while time.time() < end:
        r, _, _ = select.select([qemu.stdout], [], [], 0.1)
        if r:
            d = qemu.stdout.read(4096)
            if not d:
                break
            data += d
        else:
            break
    return data


def test():
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
    read_output(qemu, 0.3)  # Drain boot output

    def send(cmd_utf8, label, wait=0.5):
        qemu.stdin.write(cmd_utf8 + b"\r")
        qemu.stdin.flush()
        time.sleep(wait)
        out = read_output(qemu, 0.5)
        print(f"--- {label} ---")
        text = out.decode("utf-8", errors="replace")
        print(text[-300:] if len(text) > 300 else text)

    send(b"test", "test")
    send(b"\xe8\xbe\x93\xe5\x87\xba(42)", "output")  # output(42)
    send(b"\xe6\x98\xbe\xe7\xa4\xba", "display")  # display
    send(b"\xe7\xbb\x9f\xe8\xae\xa1", "stats")  # stats

    qemu.kill()
    qemu.wait()
    print("=== DONE ===")


if __name__ == "__main__":
    test()
