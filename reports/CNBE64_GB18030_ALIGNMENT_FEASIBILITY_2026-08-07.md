# CNBE64 承载 GB18030 对齐可行性报告（2026-08-07）

## 问题

CNBE-32 的 11 位 `idx` 无法承载 GB18030 指针（需 19 bit，全量序号需 17 bit）。本报告验证 64 位编码承载 GB18030 对齐的可行性。

## 实测结果

对 `data/cnbe_catalog_fixed.csv.gz` 97,686 行打包测试：

| 指标 | 结果 |
|---|---:|
| 总字符 | 97,686 |
| CNBE64 唯一编码 | 97,686 |
| GB18030 可编码 | 97,686 |
| 最大 GB18030 指针 | 329,207 |
| 指针所需位宽 | 19 bit |
| 21 bit 指针字段覆盖 | 是 |
| MAPPED（指针唯一） | 91,061 |
| CONFLICT（指针重复） | 6,625 |
| MISSING | 0 |

## 建议布局

```text
bits 63..60: version (4)          # 布局版本
bits 59..39: gb18030_pointer (21) # GB18030 线性指针
bit  38:     gb18030_present (1)
bits 37..36: mapping_status (2)   # 0=MAPPED 1=CONFLICT 2=MISSING 3=UNKNOWN
bits 35..32: reserved (4)
bits 31..0:  CNBE32 (32)          # 保留原结构编码
```

合计 4+21+1+2+4+32 = 64 bit；实际信息量 56 bit 已够，64 bit 用于对齐与后续扩展。

## 结论

**CNBE64 承载 GB18030 对齐可行**，且比复用 `idx` 更符合治理边界：

1. 低 32 位保留 CNBE32，现有结构语义、golden vectors 与 RISC-V 字段不改变；
2. 高 32 位提供完整 GB18030 指针空间（21 bit 覆盖最大 1.59M 指针范围）；
3. 可携带映射状态，重复指针不会冒充唯一键；
4. 与仓库既定 CNBE64/CNBE128 证据档案方向一致。

## 边界

- Unicode 仍是唯一字符标识；GB18030 指针只作为对齐元数据，不作为地址键。
- 实测 6,625 个重复指针，因此 CONFLICT 行必须保留 Unicode 主键并单独裁决。
- Python codec 只用于可行性探针，不构成 GB18030-2022 官方映射权威。
- 64 位化需要同步更新 SDK、golden vectors、RISC-V 指令、数据库 schema 与测试，是独立工程轮次。
- 若未来还要在编码内携带完整 Unicode、笔画序、拆字树等证据，应使用 CNBE128 证据档案，而不是继续压缩 CNBE64。

## 下一步

1. 以本布局起草 CNBE64 RFC 草案；
2. 用权威 GB18030-2022 映射表回填 `gb18030_map`，区分 MAPPED / CONFLICT / MISSING；
3. 对比 97,686 目录与 GB18030 字集差异；
4. 对 6,625 个冲突行建立裁决队列；
5. 治理授权后实现 CNBE64 SDK 与 golden vectors，保持低 32 位兼容。
