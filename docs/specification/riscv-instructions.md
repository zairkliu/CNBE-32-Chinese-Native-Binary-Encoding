# RISC-V 自定义指令接口

## 三条核心指令

| 指令 | 功能 | C等价函数 | 周期 | 验证 |
|------|------|----------|:----:|:----:|
| `cnhe.map` | Unicode→CNBE查表 | `cnhe_map()` | 1 | Spike+QEMU(v7.1.1) |
| `cnhe.extract` | 位域提取 | `cnhe_extract()` | 1 | Spike(v7.1.1) |
| `cnhe.cmp` | 加权汉明距离 | `cnhe_cmp()` | 1-2 | Spike(v7.1.1) |

## 指令编码

| 指令 | OPCODE | FUNCT3 | MATCH | MASK |
|------|:------:|:------:|:-----:|:----:|
| cnhe.map | 0x0B | 0 | 0x0000000B | 0xFE00707F |
| cnhe.extract | 0x0B | 1 | 0x0000100B | 0xFE00707F |
| cnhe.cmp | 0x0B | 2 | 0x0000200B | 0xFE00707F |

## Skill 表硬件映射

| 属性 | 值 |
|------|------|
| 表大小 | 81.6 KB (20902 × 4 bytes) |
| L2缓存 | 完全容纳（典型L2 ≥ 256KB）|
| 查表延迟 | x86: 0.8ns, QEMU: 2.5ns, 真实RISC-V(1GHz): 2-5ns |
| FPGA实现 | 1周期（BRAM）| 验证于 v7.2 |

## Spike 集成

三条指令已集成至 Spike RISC-V 模拟器（v7.1.1）：
- `riscv/insns/cnhe_map.h`
- `riscv/insns/cnhe_extract.h`
- `riscv/insns/cnhe_cmp.h`
