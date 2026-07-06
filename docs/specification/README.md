# CNBE-32 核心编码规范（v1.0）

本目录包含 CNBE-32（Chinese Native Binary Encoding, 32-bit）的完整技术规范。

## 规范文档

| 文档 | 内容 | 对应实验 |
|------|------|----------|
| [architecture.md](architecture.md) | 编码架构与设计哲学 | v6.0 Skill表 |
| [bit-layout.md](bit-layout.md) | 32位位域布局（核心定义）| v6.0 / 全系列 |
| [mapping-algorithm.md](mapping-algorithm.md) | Unicode→CNBE映射算法 | v6.0 |
| [domain-encodings.md](domain-encodings.md) | 跨领域编码方案汇总 | v9.0-v10.8 |
| [riscv-instructions.md](riscv-instructions.md) | RISC-V自定义指令接口 | v7.0-v7.2 |
| [validation.md](validation.md) | 编码验证标准 | 全系列 |

## 设计目标

1. **语义可计算**: 编码标识字符并描述结构属性
2. **硬件原生**: 位域设计便于CPU指令集提取运算
3. **AI友好**: 为JEPA等架构提供结构化先验
4. **跨领域通用**: 从汉字到物理/金融/社会系统的统一编码思想

## 状态

- **当前**: v1.0（核心位域已冻结，经 v1-v10.8 验证）
- **覆盖**: CJK 97,686 字 + 生态/气象/金融/生物/物理/社会/数学 9 领域
- **许可证**: Mulan PSL v2
