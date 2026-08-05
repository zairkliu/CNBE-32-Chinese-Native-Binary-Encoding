V8_DIR := $(CURDIR)
IVERILOG ?= iverilog
VVP ?= vvp

.PHONY: all generate python-sim c-ref qemu verilog spike clean

all: generate python-sim c-ref qemu

verify-all: generate python-sim c-ref qemu verilog spike

generate:
	python3 tools/gen_skill_table.py
	python3 tools/gen_golden_vectors.py

python-sim:
	python3 sim/python/test_sim.py

c-ref:
	gcc -O2 -Wall -Wextra -I sim/c qemu/test_cnbe_qemu.c sim/c/cnbe_ref.c -o /tmp/cnbe_qemu_host
	/tmp/cnbe_qemu_host generated/skill_table.bin golden/qemu_expected.txt

qemu:
	riscv64-linux-gnu-gcc -O2 -Wall -Wextra -static -I sim/c qemu/test_cnbe_qemu.c sim/c/cnbe_ref.c -o /tmp/cnbe_qemu_riscv
	qemu-riscv64 /tmp/cnbe_qemu_riscv generated/skill_table.bin golden/qemu_expected.txt

verilog:
	@if command -v $(IVERILOG) >/dev/null 2>&1; then \
		$(IVERILOG) -g2012 -I generated -o /tmp/cnbe_v8_tb verilog/cnbe_exec.sv verilog/tb_cnbe_exec.sv && \
		$(VVP) /tmp/cnbe_v8_tb; \
	else \
		echo "iverilog not installed; skip verilog test"; \
	fi

spike:
	bash spike/build_spike.sh

clean:
	rm -f /tmp/cnbe_qemu_host /tmp/cnbe_qemu_riscv /tmp/cnbe_v8_tb
