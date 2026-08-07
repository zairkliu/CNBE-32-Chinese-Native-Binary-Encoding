# RFC CNBE64 v1

## 状态

- 版本：v1（固定布局草案，未发布为正式标准）
- 角色：CNBE32 的 64 位档案/对齐扩展，承载 GB18030 对齐元数据
- 门禁：当前只允许 codec、golden vectors、测试与证据档案；不允许发布 SDK、替换运行时库

## 布局

```text
bits 63..60: version (4)          # 当前固定为 1
bits 59..39: gb18030_pointer (21) # GB18030 线性指针
bit  38:     gb18030_present (1)
bits 37..36: gb18030_status (2)   # 0=MAPPED 1=CONFLICT 2=MISSING 3=UNKNOWN
bits 35..32: reserved (4)
bits 31..0:  cnbe32 (32)          # 低 32 位原样保留
```

## 身份与对齐

- Unicode 是唯一字符身份，永远作为主键；
- CNBE64 的 GB18030 指针只是交换/对齐元数据，不是地址键；
- 实测 97,686 字中 6,625 字存在重复指针，重复行必须标记 `CONFLICT` 并单独裁决；
- CNBE32 字段语义继续遵循字段冻结 v1.1，不因 64 位化回退。

## 导入契约

新项目引入 CNBE64：

```bash
pip install -e .   # 或复制 src/cnbe64 到新项目
```

```python
from cnbe64 import pack, unpack, pointer_for_char, GB18030_STATUS

ptr, four = pointer_for_char("沥")
code = pack(cnbe32=0x55388470, gb18030_pointer=ptr, present=True, status=GB18030_STATUS.MAPPED)
fields = unpack(code)
```

## 证据边界

- Python `gb18030` codec 只用于可行性验证，不构成 GB18030-2022 官方映射权威；
- 语义/图像/多模态证据进入独立证据表，不写入位域；
- 64 位后的 SDK、golden vectors、RISC-V、数据库 schema 更新需另行治理授权。
