# CNBE Volume 基准报告

- 数据：Linux 程序设计（第4版），280,766 字
- 卷大小：411,315 B vs 原文 842,298 B（48.83%），vs gzip 283,031 B（145.33%）
- 页大小：4096

| 操作 | CNBE Volume | gzip 全文解压后读取 |
|---|---:|---:|
| seek(100000) | 0.001 ms | - |
| extract 100 字 | 0.019 ms | 1.785 ms（解压后切片） |
| random_passage(500) | 0.574 ms | - |
| search(radix=38, struct=1) | 49.408 ms | 不支持 |
| 全文流式扫描 | 0.062 s | 0.002 s（仅解压） |

## 说明

CNBE Volume 将整篇 gzip 解压时间分摊为按页 O(1) 解压；gzip 单次读
取需要先全文解压。结构化检索（部首/结构/笔画）为 CNBE Volume 独有能力。