# CNBE-32: 中文原生二进制编码

**Chinese Native Binary Encoding, 32-bit** — 将汉字字形语义直接编码到 RISC-V 自定义指令的硬件加速方案。

## 概述

CNBE-32 是一种 32 位定长汉字编码方案，将汉字的部首、笔画、结构等字形特征直接映射到二进制位域中。已在 RISC-V Spike 模拟器上实现 6 条自定义指令，覆盖编码、解码、位域提取、语义距离计算等操作。

## 核心指标

| 指标 | 值 |
|------|----|
| 编码位数 | 32-bit 定长 |
| 覆盖字数 | 97,686 (CJK 全部统一汉字) |
| 编码唯一性 | 100% |
| 部首覆盖 | 214/214 |
| 结构类型 | 9/16 |
| 自定义指令 | 6 条 (RISC-V Custom-0) |
| 查表加速 | 二分 338x / 哈希 4044x |
| 国标兼容 | GB 18030-2022, GB/T 22320-2025 |

## 快速开始

```bash
# 1. 查看文档
cd docs/
cat 1_技术白皮书.md

# 2. 生成编码表
pip install openpyxl
python src/generate_cnbe_table.py

# 3. 运行性能模拟器
python src/cnbe_simulator.py

# 4. 打补丁到 Spike (需要 RISC-V GCC)
cd riscv-isa-sim
patch -p1 < ../hardware/spike-patches/encoding.h.patch
```

## 项目结构

```
cnbe-32/
├── README.md                   项目说明
├── LICENSE                     许可证 (MulanPSL v2)
├── docs/                       技术文档 (5 篇 + 白皮书)
├── src/                        源代码
│   ├── generate_cnbe_table.py  编码表生成器
│   ├── cnbe_table_fixed.h      C 编码头文件
│   └── cnbe_simulator.py       周期精确性能模拟器
├── hardware/                   硬件实现
│   ├── spike-patches/          Spike 补丁 + 6 条指令
│   └── verilog-cam/            CAM 模块 Verilog 代码
├── tests/                      测试程序
├── data/                       编码目录数据库
│   ├── cnbe_catalog_fixed.db.gz
│   └── CNBE_编码目录_修复完整版.xlsx
├── results/                    实验报告
└── experiments/                实验数据
```

## 许可证

本项目采用 [木兰宽松许可证，第2版（MulanPSL v2）](http://license.coscl.org.cn/MulanPSL2) 进行许可。
