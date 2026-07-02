# CNBE-32: 中文原生二进制编码

**Chinese Native Binary Encoding** · 部首 × 笔画 × 结构 → 32-bit → RISC-V 指令

![Python](https://img.shields.io/badge/python-3.9+-green)
![RISC-V](https://img.shields.io/badge/RISC-V-Custom_0-orange)
![CJK](https://img.shields.io/badge/CJK-97%2C686-brightgreen)
![Platform](https://img.shields.io/badge/platform-macOS_ARM64-lightgrey)

</div>

---

## 📖 中文文档

### 概述

CNBE-32 是一种 32 位定长汉字编码方案，将汉字的部首、笔画、结构等字形特征直接映射到二进制位域中。已在 RISC-V Spike 模拟器上实现 6 条自定义指令，使 CPU 可以直接提取汉字语义特征。

```
[31:24] 部首区 (8bit) → 214 个康熙部首
[23:19] 笔画区 (5bit) → 1-31 画
[18:15] 结构区 (4bit) → 9 种结构类型 (自动检测)
[14:4]  字库区 (11bit) → 组内索引
[3:0]   扩展区 (4bit) → 繁简/多音标志 (预留)
```

### 核心数据

| 指标 | 值 |
|:-----|:----|
| 汉字覆盖 | **97,686** 字 (CJK 全部统一汉字) |
| 编码唯一性 | **100%** (全部唯一) |
| 部首覆盖 | **214/214** (全部康熙部首) |
| 结构类型 | **9/16** 种 (自动检测，修复前仅 3 种) |
| RISC-V 指令 | **6 条** (Custom-0 opcode) |
| 查表加速 | **二分 338x** (零成本) / **哈希 4044x** (128KB) |
| 分类准确率 | **100.00%** (直接位域读取) |
| 国标兼容 | GB 18030-2022, GB/T 22320-2025 |

### 仓库结构

```
cnbe-32/
├── docs/                      9 篇技术文档
│   ├── 1_技术白皮书.md         白皮书 (核心)
│   ├── 2_实验说明.md          实验设计 + 方法
│   ├── 3_架构设计.md          六层全链路架构
│   ├── 4_编码方案设计.md       位域 + 索引设计
│   ├── 5_产出报告.md          交付清单
│   ├── CNBE32_CJK_完整白皮书.md  理论+技术+方案
│   ├── CNBE32_RISCV_技术白皮书.md  Spike 实现
│   ├── CNBE32_双版本对比白皮书.md  8105 vs 97K
│   └── CNBE32_标准引用附录.md    GB/T 标准对接
├── src/                      3 个源代码
│   ├── generate_cnbe_table.py   编码表生成器
│   ├── cnbe_simulator.py        周期精确性能模拟器
│   └── cnbe_table_fixed.h       编码 C 头文件 (3.8MB)
├── hardware/                  21 个硬件文件
│   ├── spike-patches/            16 个补丁
│   │   ├── encoding.h.patch      编码定义
│   │   ├── processor.h.patch     周期计数
│   │   ├── cnbe_enc/dec.h        编码/解码指令
│   │   └── cnbe_rad/str/struct/dist.h  部首/笔画/结构/距离
│   └── verilog-cam/              5 个 CAM 模块
│       └── cnbe_cam_top.sv       CAM 顶层 (8105 条目)
├── tests/                     5 个测试程序
│   ├── test_cnbe_full.c         8105 字全量集成测试
│   ├── test_clustering.c        聚类验证
│   ├── test_cnbe_unit.S         汇编单元测试
│   ├── perf_cycle_count.c       周期计数测试
│   └── test_perf.c              性能基准
├── results/                   3 篇实验报告
│   ├── CNBE32_EXP_CJK.md       CJK 全量 4 项实验
│   ├── CNBE32_TEST_REPORT_8105.md  8105 字验证
│   └── CNBE32_PERFORMANCE_REPORT.md  周期性能
├── data/                      编码目录数据库
│   ├── CNBE_编码目录_修复完整版.xlsx   (5.7 MB)
│   ├── cnbe_catalog_fixed.db.gz       (1.4 MB)
│   └── cnbe_catalog_fixed.csv.gz      (803 KB)
└── experiments/                t-SNE 特征数据
    └── cnbe_tsne_data.csv.gz          (51 KB, 10000 点)
```

### 快速开始

```bash
# 1. 生成编码表
pip install openpyxl
python src/generate_cnbe_table.py

# 2. 运行性能模拟器
python src/cnbe_simulator.py

# 3. 集成到 Spike (需要 RISC-V GCC)
cd riscv-isa-sim
patch -p1 < hardware/spike-patches/encoding.h.patch
cp hardware/spike-patches/*.h riscv/insns/
mkdir build && cd build
../configure --with-isa=rv64imafdc && make -j4 && make install
```

### 6 条 RISC-V 自定义指令

| 指令 | funct3 | 功能 | 硬件周期 |
|:----:|:------:|:-----|:--------:|
| `cnbe.enc` | 000 | Unicode → CNBE-32 (哈希 O(1)) | **2** |
| `cnbe.dec` | 001 | CNBE-32 → Unicode (线性) | ~4053 |
| `cnbe.rad` | 010 | 提取部首 (bits 31:24) | **1** |
| `cnbe.str` | 011 | 提取笔画 (bits 23:19) | **1** |
| `cnbe.struct` | 100 | 提取结构 (bits 18:15) | **1** |
| `cnbe.dist` | 101 | 加权语义距离 | **2** |

### 实验验证

| 实验 | 结果 |
|:-----|:----:|
| 部首分类 | **100.00%** (8,105 字) |
| 笔画分类 | **100.00%** (8,105 字) |
| 同部首距离 | 4.29 (97,686 字采样) |
| 跨部首距离 | 21.34 (97,686 字采样) |
| 聚类分离度 | **4.97x** |
| 平均语义距离 | 20.9 / 46 |
| 编码唯一性 | **97,686/97,686 ✓** |

### 引用

```bibtex
@software{cnbe32_2026,
  title = {CNBE-32: Chinese Native Binary Encoding},
  author = {Liu, Zairk},
  year = {2026},
  url = {https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding}
}
```

### 许可证

本项目采用 [木兰宽松许可证，第2版（MulanPSL v2）](http://license.coscl.org.cn/MulanPSL2) 进行许可。

---

## 📘 English Documentation

### Overview

CNBE-32 is a 32-bit fixed-length encoding scheme that embeds Chinese character structure information — radical, stroke count, and structure type — directly into binary bit fields. Implemented with 6 custom RISC-V instructions on the Spike simulator.

### Key Metrics

| Metric | Value |
|:-------|:------|
| Character coverage | **97,686** (All CJK Unified Ideographs) |
| Encoding uniqueness | **100%** |
| Radical coverage | **214/214** |
| Structure types | **9/16** (auto-detected) |
| Custom instructions | **6** (RISC-V Custom-0) |
| Lookup speedup | **338x** (binary search) / **4,044x** (hash) |
| Accuracy | **100.00%** (direct bitfield) |

### Project Structure

```
cnbe-32/
├── docs/         Technical documentation (9 papers, Chinese)
├── src/          Source code (generator + simulator)
├── hardware/     Spike patches + Verilog CAM
├── tests/        5 test programs
├── results/      Experiment reports
├── data/         Encoding database
└── experiments/  t-SNE feature vectors
```

### Quick Start

```bash
pip install openpyxl
python src/generate_cnbe_table.py
python src/cnbe_simulator.py
```

### Hardware Instructions

| Inst | funct3 | Function | Cycles |
|:----:|:------:|:---------|:------:|
| cnbe.enc | 000 | Unicode → CNBE-32 | 2 |
| cnbe.dec | 001 | CNBE-32 → Unicode | ~4053 |
| cnbe.rad | 010 | Extract radical | **1** |
| cnbe.str | 011 | Extract strokes | **1** |
| cnbe.struct | 100 | Extract structure | **1** |
| cnbe.dist | 101 | Semantic distance | **2** |

### Citation

```bibtex
@software{cnbe32_2026,
  title = {CNBE-32: Chinese Native Binary Encoding},
  author = {Liu, Zairk},
  year = {2026},
  url = {https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding}
}
```

### license

本项目采用 [木兰宽松许可证，第2版（MulanPSL v2）](http://license.coscl.org.cn/MulanPSL2) 进行许可。
