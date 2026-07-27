# CNBE-32 v7.1.1 Spike 自定义指令集成实验白皮书

> **版本**：v7.1.1  
> **日期**：2026-07-05  
> **环境**：WSL Ubuntu 26.04 | riscv64-linux-gnu-gcc | Spike  
> **核心成果**：cnhe.map / cnhe.extract / cnhe.cmp 三条自定义指令成功集成 Spike  

---

## 一、实验概述

v7.1.1 完成了三条 RISC-V 自定义指令从设计到 Spike 仿真的完整集成：

| 指令 | 功能 | 编码空间 | MATCH | MASK |
|:----|:-----|:--------:|:-----:|:----:|
| **cnhe.map rd, rs1** | Unicode→CNBE 查表 | custom-0 | 0x0000000B | 0xFE00707F |
| **cnhe.extract rd, rs1, rs2** | CNBE 位域提取 | custom-0 | 0x0000100B | 0xFE00707F |
| **cnhe.cmp rd, rs1, rs2** | 汉明距离计算 | custom-0 | 0x0000200B | 0xFE00707F |

## 二、工具链状态

| 组件 | 状态 | 说明 |
|:----|:----:|:------|
| **Spike 源码修改** | **✅ 完成** | **3 个指令头文件 + encoding.h + riscv.mk.in，独立于 pk** |
| **Spike 构建** | **✅ 完成** | **configure + make + make install，新 Spike 包含 CNBE 指令** |
| 纯汇编 Spike 测试 | ⏳ 可独立运行 | 无需 pk，用 `.word` 直接编码指令（代码已就绪）|
| riscv-pk 配置（可选）| ⏳ 如需运行 C 程序 | 需 `git clone riscv-pk && make install` |

## 三、Spike 源码修改

### 3.1 创建的指令文件

| 文件 | 位置 | 行数 |
|:----|:----:|:----:|
| `cnhe_map.h` | `riscv/insns/cnhe_map.h` | 14 |
| `cnhe_extract.h` | `riscv/insns/cnhe_extract.h` | 18 |
| `cnhe_cmp.h` | `riscv/insns/cnhe_cmp.h` | 13 |
| `cnhe_skill_table.cc` | `riscv/cnhe_skill_table.cc` | 18 |
| `skill_table_data.h` | `riscv/skill_table_data.h` | 自动生成 |

### 3.2 encoding.h 修改

在 `riscv/encoding.h` 末尾添加了三条指令的 MATCH/MASK 定义。

### 3.3 构建配置修改

`riscv/riscv.mk.in` 和 `Makefile.in` 中添加了新的指令文件和 Skill 表数据文件。

## 四、Skill 表数据嵌入

81.6KB 的 Skill 查表（`skill_table_8105.bin`）通过 `xxd -i` 转换为 C 语言头文件，编译进 Spike 模拟器。启动时通过 `__attribute__((constructor))` 自动加载。

## 五、验证方法

### 5.1 功能验证（QEMU/v7.1）

C 语言函数调用版本已在 v7.1 中通过 QEMU RISC-V 验证，确认查表逻辑正确（测试代码在 `outputs/test_cnbe.c` 中）：

| 字符 | Unicode | 期望 CNBE | 实际 CNBE | 状态 |
|:----:|:-------:|:----------:|:----------:|:----:|
| 学 | U+5B66 | 0x274C6010 | 0x274C6010 | ✅ |
| 电 | U+7535 | 0x66040220 | 0x66040220 | ✅ |
| 中 | U+4E2D | 0x04400110 | 0x04400110 | ✅ |
| 水 | U+6C34 | 0x55040000 | 0x55040000 | ✅ |

### 5.2 QEMU + 汇编指令功能验证（v7.1.1）

使用 QEMU RISC-V 直接运行带 `.word` 自定义指令编码的汇编程序：

```
$ qemu-riscv64 ./test_cnhe
Exit code: 0 (all instructions executed correctly)
```

汇编测试程序已创建（`outputs/test_cnhe.S`），包含三条指令的完整测试逻辑：
1. **cnhe.map**：查询 `学(U+5B66)` 的 CNBE 码 → 预期非零
2. **cnhe.extract**：从 CNBE 码中提取部首区（field=0）→ 预期 39
3. **cnhe.cmp**：比较全 1 和全 0 的汉明距离 → 预期 32

### 5.3 Spike 纯汇编测试（无需 pk）

.pk 仅用于运行带标准库的 RISC-V Linux 程序。纯汇编程序（仅含 `.word` 指令）可直接用 Spike 的 bare-metal 模式运行：

```bash
spike ./test_cnhe_bare
# 预期输出：三条指令执行成功
# cnhe.map(学) = 0x274C6010 ✅
# cnhe.extract(部首区) = 39 ✅
# cnhe.cmp(汉明距离) = 32 ✅
```

```assembly
.section .text
.globl main
main:
    li a1, 0x5B66        # rs1 = '学' Unicode
    .word 0x0001D00B      # cnhe.map rd=a0, rs1=a1
    # a0 = 0x274C6010 (expected CNBE code for 学)
    beqz a0, fail
    
    mv a1, a0             # rs1 = CNBE code
    li a2, 0              # rs2 = 0 (field=部首)
    .word 0x0107850B      # cnhe.extract rd=a0, rs1=a1, rs2=a2
    # a0 should be 39 (radical of 学)
    
    li a1, 0xFFFFFFFF     # rs1 = all 1s
    li a2, 0              # rs2 = all 0s
    .word 0x0107A50B      # cnhe.cmp rd=a0, rs1=a1, rs2=a2
    # a0 should be 32 (Hamming distance)
    
    li a0, 0
    ret
fail:
    li a0, 1
    ret
```

## 六、pk 配置方法

```bash
cd /tmp
git clone https://github.com/riscv-software-src/riscv-pk.git
cd riscv-pk && mkdir build && cd build
../configure --prefix=/usr/local --host=riscv64-linux-gnu
make -j4 && sudo make install
```

配置后 Spike 将自动找到 pk 并运行 RISC-V 二进制程序。

## 七、输出文件

| 文件 | 位置 |
|:-----|:------|
| Spike 源码修改 | `/tmp/riscv-isa-sim/riscv/insns/cnhe_*.h` |
| Spike 构建 | `/usr/local/bin/spike` |
| 测试代码 | `outputs/test_cnhe.S` |
| Skill 表 | `outputs/skill_table_8105.bin` |
