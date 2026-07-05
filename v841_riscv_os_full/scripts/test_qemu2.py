import subprocess
import os
import time

HOME = os.path.expanduser("~")
KERNEL = os.path.join(HOME, "v84_riscv_os_full", "output", "kernel.bin")

# ASCII test first
print("=== ASCII test ===")
qemu = subprocess.Popen(
    ["qemu-system-riscv64", "-machine", "virt", "-bios", "none",
     "-device", "loader,file=" + KERNEL + ",addr=0x80000000",
     "-serial", "stdio", "-monitor", "none"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

time.sleep(0.5)

# Send 3 simple commands
qemu.stdin.write(b"test\r")
qemu.stdin.flush()
time.sleep(0.5)
qemu.stdin.write(b"输出(42)\r")
qemu.stdin.flush()
time.sleep(0.5)
qemu.stdin.write(b"帮助\r")
qemu.stdin.flush()
time.sleep(0.5)

# Read all output
try:
    qemu.kill()
except:
    pass
stdout, _ = qemu.communicate(timeout=2)
print(stdout.decode("utf-8", errors="replace"))
print("=== END ===")
