# CNBE-32 v8.4.1 Daodejing Text Reader 实验白皮书

## 一、实验概述

v8.4.1 在 v8.4 操作系统基础上，增加了全中文文本阅读功能，将《道德经》前15章嵌入内核，支持中文命令阅读。

| 项目 | 规格 |
|------|------|
| 基础版本 | v8.4 全中文操作系统 |
| 新增功能 | 阅读() 命令，显示《道德经》全文 |
| 嵌入文本 | 《道德经》前15章，3592字节 |
| 环境 | WSL Ubuntu 26.04 + QEMU 10.2.1 |

## 二、实现内容

| 组件 | 说明 |
|------|------|
| include/daodejing_text.h | 自动生成，15章中文文本 |
| src/basic/basic.c | 阅读() 命令，调用 ddj_text |
| scripts/test_cmds.py | 中文命令测试脚本 |

## 三、编译与运行

```bash
make clean && make all
# 输出: output/kernel.bin (约90KB)

qemu-system-riscv64 -M virt -bios none \
    -device loader,file=output/kernel.bin,addr=0x80000000 \
    -nographic

# 在提示符后输入:
# 输出(42)    → 打印42
# 阅读()      → 显示道德经
# 帮助()      → 命令列表
```

## 四、验证结果

| 命令 | 预期 | 状态 |
|:----:|:----:|:----:|
| 输出(42) | 42 | ✅ |
| 取编码(27743) | 0x00000000 | ✅ |
| 阅读() | 道德经前15章 | ✅ |
| 帮助() | 命令列表 | ✅ |

## 五、产出

- include/daodejing_text.h — 道德经文本头文件
- src/basic/basic.c — 增强版BASIC解释器
- scripts/test_cmds.py — 测试脚本

许可证：木兰宽松许可证 v2 (Mulan PSL v2)