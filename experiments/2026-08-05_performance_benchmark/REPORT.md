# CNBE-32 Performance Benchmark

日期：2026-08-05

## 环境

| 项 | 值 |
|---|---|
| 系统 | Ubuntu 26.04 (WSL2, Linux 6.18.33.2-microsoft-standard-WSL2) |
| CPU | x86_64，WSL2 主机 CPU（未固定频率） |
| Python | 3.14.4 |
| gcc | 15.2.0 |
| 数据库 | `repo/data/cnbe32.db`（21,178 行，位于 /mnt/c） |
| 表 | 8105 行 Unicode→CNBE 排序表（C 微基准） |

## 方法

- Python 基准：预热 3 次，取 7 次中位数，单位为 ns/op；
- C 基准：`gcc -O2 -std=c99`，`clock_gettime(CLOCK_MONOTONIC)`；
- SQLite 查找与批量查找走 SDK 公开 API（`cnbe32.lookup` / `cnbe32.batch`）；
- 原始结果：`results.json`；复现：`bash run_benchmark.sh`。

## Python SDK

| 操作 | ns/op | 说明 |
|---|---:|---|
| encode（位域组装） | 778 | 含字段校验与 dataclass 分配 |
| decode（位域拆解） | 680 | 含字段校验 |
| field weighted distance | 1,857 / 对 | 加权形态距离 |
| bit Hamming distance | 1,561 / 对 | 32 位 XOR + popcount |
| lookup（SQLite 单字） | 1,606,646 | 每字一次 SQL 查询 |
| batch（SQLite 批量） | 1,428,421 / 字 | 每唯一字一次 SQL 查询 |
| Python `ord()` 基线 | 46.5 | 纯内建函数参考 |

## C 核心

| 操作 | ns/op |
|---|---:|
| encode（inline 位运算） | 0.891 |
| decode（inline 位运算） | 1.547 |
| bit Hamming distance | 1.880 / 对 |
| binary search lookup（8105 表） | 30.453 |

## 数据库、内存与存储

| 指标 | 值 |
|---|---:|
| SQLite connect + COUNT(*) | 13.3 ms |
| 加载 21,178 行后 RSS 增量 | 18.3 MB |
| 数据库文件 | 1.86 MB |
| CNBE 二进制（4 B/字） | 84.7 KB |
| UTF-8 字符文本 | 63.7 KB（3.01 B/字） |
| JSON（5,000 行，含全字段） | 1.01 MB |

## 结论

1. **C 核心是计算层的真实成本**：encode/decode 约 1-2 ns/op，固定位宽可直接单周期提取；Python SDK 的 700 ns 主要来自字段校验与对象分配，不是位运算本身。
2. **SQLite 按字查询不是热路径**：单字 1.6 ms、批量 1.4 ms/字；生产批量场景应一次载入内存表（C 二分查找 30 ns），或改用 `numpy` 数组。
3. **CNBE 不是以体积取胜**：BMP CJK 的 UTF-8 为 3 字节，CNBE 定长 4 字节，二进制体积 +33%；扩展区 4 字节 UTF-8 场景两者持平。其价值在结构可计算、固定宽度与 O(1) 字段访问。
4. **边界声明**：数据库位于 `/mnt/c`，WSL 跨文件系统 I/O 会抬高 SQLite 延迟；面向外部的绝对性能数字应在原生 Ubuntu 上复跑本脚本。
