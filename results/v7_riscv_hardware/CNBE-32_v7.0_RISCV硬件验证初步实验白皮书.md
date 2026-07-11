# CNBE-32 v7.0 RISC-V 硬件验证初步实验白皮书

> **版本**：v7.0  
> **日期**：2026-07-05  
> **环境**：WSL Ubuntu 26.04  
> **工具链**：riscv64-linux-gnu-gcc（RISC-V GCC）  
> **验证方式**：C 语言 Skill 查表 + x86 验证 + RISC-V 交叉编译  

---

## 1. 实验概述

v7.0 是 CNBE 从软件验证走向硬件验证的第一步。核心任务是将 v6.0 建立的 Skill 查表体系移植到 C 语言并交叉编译为 RISC-V 架构，验证硬件查表的可行性。

## 2. 环境搭建

| 组件 | 状态 |
|:----|:----:|
| WSL Ubuntu 26.04 | ✅ 运行中 |
| RISC-V GCC (riscv64-linux-gnu-gcc) | ✅ 已安装 |
| 原生 GCC (x86) | ✅ 已安装 |
| QEMU RISC-V | ⏳ 待安装 |
| Spike Simulator | ⏳ 待安装 |

## 3. C 语言实现

### 核心函数

```c
/* cnhe_lookup - 模拟 RISC-V cnhe.map 指令 */
uint32_t cnhe_lookup(uint32_t unicode) {
    if (unicode >= 0x4E00 && unicode <= 0x9FA5)
        return skill_table[unicode - 0x4E00];
    return 0;
}

/* cnhe_decode - 提取 CNBE 32-bit 编码的四个字段 */
void cnhe_decode(uint32_t code, uint32_t *radical, uint32_t *stroke,
                 uint32_t *structure, uint32_t *idx) {
    if (radical)   *radical   = (code >> 24) & 0xFF;
    if (stroke)    *stroke    = (code >> 19) & 0x1F;
    if (structure) *structure = (code >> 15) & 0xF;
    if (idx)       *idx       = (code >> 4)  & 0x7FF;
}
```

## 4. x86 验证结果

| 汉字 | Unicode | 部首区 | 笔画 | 结构 | 字库索引 | 状态 |
|:----:|:-------:|:------:|:----:|:----:|:--------:|:----:|
| 学 | U+5B66 | 39 | 8 | 3（上下）| 1 | ✅ 正确 |
| 电 | U+7535 | 102 | 5 | 1（左右）| 2 | ✅ 正确 |
| 中 | U+4E2D | 2 | 4 | 0（独体）| 1 | ✅ 正确 |
| 水 | U+6C34 | 85 | 4 | 1（左右）| 0 | ✅ 正确 |
| 氢 | U+6C22 | 84 | 9 | 1（左右）| 0 | ✅ 正确 |
| 锂 | U+9502 | 167 | 12 | 1（左右）| 15 | ✅ 正确 |
| 碳 | U+78B3 | 112 | 14 | 1（左右）| 3 | ✅ 正确 |
| 氧 | U+6C27 | 84 | 10 | 1（左右）| 0 | ✅ 正确 |
| 國 | U+570B | — | — | — | — | ⚠️ 8105表不含繁体 |
| 愛 | U+611B | — | — | — | — | ⚠️ 同上 |

## 5. 性能基准

| 测量项 | x86 原生 |
|:-------|:--------:|
| 查表条目 | 20,902 |
| 查表大小 | 81.6 KB |
| 总调用数 | 1,000,000 |
| 总耗时 | 796 μs |
| **单次查表** | **0.8 ns** |

## 6. RISC-V 交叉编译状态

| 步骤 | 状态 |
|:-----|:----:|
| riscv64-linux-gnu-gcc 安装 | ✅ 就绪 |
| test_cnbe.c 交叉编译 | ✅ 编译通过 |
| RISC-V 二进制 | ✅ 已生成（test_cnbe_riscv）|
| QEMU RISC-V 仿真运行 | ⏳ 需安装 qemu-user |
| Spike 周期级模拟 | ⏳ 需安装 Spike |

## 7. 结论与下一步

| 结论 | 说明 |
|:-----|------|
| Skill 查表可在 C 中正确实现 | cnhe_lookup/decode 函数验证通过 |
| 查表性能极高 | x86: 0.8ns/次，RISC-V 预期 2-5 周期 |
| RISC-V 交叉编译就绪 | 工具链可用，二进制已生成 |
| 下一步 | 安装 QEMU/Spike，运行 RISC-V 仿真验证 |

**产出文件**：`outputs/test_cnbe.c`（C 源码），`outputs/test_cnbe_riscv`（RISC-V 二进制）
