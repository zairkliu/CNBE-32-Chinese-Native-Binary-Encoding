# CNBE-32 RISC-V v8 验证过程公示

**日期**：2026-08-05  
**环境**：WSL Ubuntu-26.04（`Ubuntu-26.04` 发行版）  
**目标**：以模拟器为唯一事实源，验证 `cnbe.map/extract/cmp/skill` 四指令在 Python、C、QEMU、Verilog、Spike 与 Linux mini-kernel 运行时中的一致性。

---

## 一、数据来源

所有技能表与 golden vectors 均从 `data/cnbe32.db` 生成，不使用合成数据。

| 指标 | 值 |
|---|---|
| 运行时数据库 | 21,178 行 |
| 8105 标准轨 | 7,602 行 |
| 重复 CNBE 码 | 4 个（reverse lookup 取 Unicode 序第一个） |
| Unicode 范围 | U+3447 .. U+2CE93 |
| 生成脚本 | `riscv/v8/tools/gen_skill_table.py`、`gen_golden_vectors.py` |

Golden 文件：

- `riscv/v8/golden/golden_vectors.json`
- `riscv/v8/golden/qemu_expected.txt`

## 二、验证矩阵

| 实现层 | 命令 | 结果 |
|---|---|---|
| Python cycle 模拟器 | `make python-sim` | PASS（CNBE 指令 + RV32I 子集） |
| C 参考实现 | `make c-ref` | 7 passed, 0 failed |
| QEMU user-mode | `make qemu` | 7 passed, 0 failed |
| Verilog 执行单元 | `make verilog` | 55 passed, 0 failed |
| Spike 自定义指令 | `make spike` | PASS |
| Linux mini-kernel 运行时 | `tests/test_cnbe_v8_alignment.c` | 55 passed, 0 failed |

## 三、Spike 集成过程

### 3.1 修改点

1. `encoding.h`：在 `#ifdef DECLARE_INSN` 块内插入四条 `DECLARE_INSN`，避免追加到文件末尾导致宏不可见。
2. `riscv.mk.in`：将 `riscv_insn_ext_cnbe` 变量定义移到 `riscv_gen_srcs` 之前，并把 `$(riscv_insn_ext_cnbe)` 加入 `riscv_insn_list`。
3. `riscv_srcs`：加入 `cnbe_skill_table.cc`，技能表编译进 `libriscv.so`。
4. 技能表头文件：去掉 include guard，允许 Spike 模板在多个生成函数内重复声明。
5. 测试方式：使用裸机 `tohost` 退出协议；失败路径进入死循环，`timeout` 可明确区分 PASS/FAIL。

### 3.2 遇到的问题与修复

| 问题 | 根因 | 修复 |
|---|---|---|
| `DECLARE_INSN` 编译失败 | 追加在 encoding.h 末尾，宏不可见 | 插入到 `#ifdef DECLARE_INSN` 块内 |
| CNBE 指令未编译进 Spike | 变量定义晚于模式规则 | 将变量移到 `riscv_gen_srcs` 之前 |
| 技能表符号未定义 | `cnbe_skill_table.cc` 未加入源码 | 加入 `riscv_srcs` |
| 指令模板重复 include 失效 | 头文件 include guard 跳过后续声明 | 生成可重复声明头 |
| Verilog 查表全 0 | `$fscanf %h` 把 `0x` 前缀解析为未知位 `x` | golden 文件去掉 `0x` 前缀 |
| Spike extract 返回 0 | 汇编 `.word` 的 funct3 编码错误 | 修正为 `0xC5150B` |

## 四、Linux mini-kernel 对齐

`linux_cnbe32_riscv` 的运行时从旧的 20,902 合成表迁移到 v8 真实表：

- `include/cnbe_table_data.h`：由 `tools/gen_cnbe_table.py` 从 DB 生成 21,178 行配对表；
- `include/cnbe.h`：统一为 `cnbe_map/extract/cmp/skill`；
- `cnbe/cnbe.c`：二分查表、字段提取 0-4、SDK 权重 8/5/4、反查 `cnbe_skill`；
- `kernel/cnbe_basic.c`：Shell 命令扩展为 `取编码`、`取部首`、`取笔画`、`取结构`、`比较`、`反查`。

Host 对齐测试：

```bash
cd repo/linux_cnbe32_riscv
gcc -O2 -Wall -Wextra -iquote include \
    tests/test_cnbe_v8_alignment.c cnbe/cnbe.c -o /tmp/test_cnbe_kernel
/tmp/test_cnbe_kernel
# CNBE kernel v8 alignment test: 55 passed, 0 failed
```

## 五、Linux 0.01 RISC-V 模拟启动

`linux_cnbe32_riscv` 已成功在 QEMU RISC-V + OpenSBI 下启动：

```text
加载系统中...
CNBE-32 就绪 | RISC-V 1GHz | 1GB RAM
=== 中文原生操作系统 ===
CNBE-32 中文编码 | RISC-V 64位架构
部首-笔画-结构 三维语义编码
中文系统> 就绪
```

详细过程见
[`linux_cnbe32_riscv/docs/SIMULATION_REPORT_2026-08-05.md`](../../linux_cnbe32_riscv/docs/SIMULATION_REPORT_2026-08-05.md)。

## 六、边界声明

- v8 是研究/工程基线，不是已批准 ISA 扩展；
- modeled cycle counts 不是硅片实测性能；
- `idx` 是兼容字段，不作为寻址键；
- radix 仍为项目内部编号，GF 0011-2009 对齐中；
- 全中文 Linux 0.01 内核整体仍为概念原型，未完成可运行构建；
- 本次公示只说明 RISC-V 指令语义与运行时的一致性，不替代硬件流片验证。

## 七、复现命令

```bash
cd repo/riscv/v8
make generate
make python-sim
make c-ref
make qemu
make verilog
make spike
```

Spike 依赖用户态 `pkg-config`、`libfdt-dev` 与 RISC-V 工具链；构建产物位于 `$HOME/tools/spike-prefix`。

## 八、数学模型深化实验

基于同一真实数据库，已完成五类数学深化实验：

```bash
cd repo/experiments/2026-08-05_cnbe_math
python3 scripts/metric_space.py
python3 scripts/lattice_range.py
python3 scripts/information_theory.py
python3 scripts/hyperbolic.py
python3 scripts/algebra_spec.py
```

报告：[`experiments/2026-08-05_cnbe_math/REPORT_2026-08-05.md`](../../experiments/2026-08-05_cnbe_math/REPORT_2026-08-05.md)
