@echo off
title CNBE-32 RISC-V Simulation Setup
echo === CNBE-32 RISC-V Instruction Verification ===
echo.
echo This script will guide you through setting up and running
echo the CNBE RISC-V verification experiments.
echo.
echo Step 1: Install WSL2 Ubuntu (required for RISC-V toolchain)
echo   From PowerShell (Admin): wsl --install -d Ubuntu-22.04
echo.
echo Step 2: In WSL2 Ubuntu terminal, run:
echo   sudo apt update
echo   sudo apt install -y gcc-riscv64-linux-gnu binutils-riscv64-linux-gnu
echo   sudo apt install -y spike pk
echo.
echo Step 3: Navigate to the riscv directory and build:
echo   cd /mnt/c/Users/zairk/Documents/Codex/2026-06-22/ni/outputs/riscv
echo   riscv64-linux-gnu-gcc -O2 -march=rv32im_zicsr test_cnbe_full.c -o test_cnbe_full.elf
echo.
echo Step 4: Run on Spike simulator:
echo   spike pk test_cnbe_full.elf
echo.
echo Step 5: Visualize on Ripes (Windows native):
echo   Download from: https://github.com/mortbopet/Ripes/releases
echo   Load test_cnbe_full.elf and observe pipeline execution.
echo.
echo Python simulation already completed! See result.txt for data.
echo.
echo Files in this directory:
dir /B *.h *.c *.py *.sh *.bat *.json 2>nul
echo.
pause
