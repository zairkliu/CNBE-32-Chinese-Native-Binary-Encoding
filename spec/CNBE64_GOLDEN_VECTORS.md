# CNBE64 Golden Vectors

参考实现：`src/cnbe64/codec.py`

## 布局

```text
bits 63..60: version (4)
bits 59..39: gb18030_pointer (21)
bit  38:     gb18030_present (1)
bits 37..36: gb18030_status (2)
bits 35..32: reserved (4)
bits 31..0:  cnbe32 (32)
```

## 向量

| Unicode | 汉字 | CNBE32 | GB18030 Pointer | CNBE64 |
|---|---|---|---:|---|
| U+3400 | 㐀 | 0x01280000 | 12439 | 0x10184bc001280000 |
| U+6CA5 | 沥 | 0x55388470 | 12259 | 0x1017f1c055388470 |
| U+98A6 | 颦 | 0xB5A880B0 | 21578 | 0x102a2540b5a880b0 |
| U+7183 | 熃 | 0x56708170 | 5824 | 0x100b604056708170 |

验证：

```bash
PYTHONPATH=repo/src pytest tests/test_cnbe64.py
```
