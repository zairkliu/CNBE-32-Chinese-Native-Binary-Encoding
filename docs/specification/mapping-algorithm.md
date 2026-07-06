# Unicode → CNBE 映射算法

## 映射流程

```
输入: Unicode码点 (U+XXXX)
输出: cnbe32 (32位整数)

1. 查部首表 → radix_id (8bit)
2. 查笔画数据库 → stroke_count (5bit)
3. 结构判定器 → struct_type (4bit)
4. 查字库索引 → cjk_index (11bit)
5. 扩展属性 → ext_flags (4bit)
6. 组装编码
```

## Python 参考实现

```python
import numpy as np

SKILL_TABLE_PATH = "skill/skill_table_8105.npy"
skill_table = np.load(SKILL_TABLE_PATH)

def unicode_to_cnbe(char):
    code_point = ord(char)
    if 0x4E00 <= code_point <= 0x9FA5:
        idx = code_point - 0x4E00
        if idx < len(skill_table):
            return skill_table[idx]
    return 0

def cnbe_decode(code):
    return {
        'radix': (code >> 24) & 0xFF,
        'stroke': (code >> 19) & 0x1F,
        'structure': (code >> 15) & 0xF,
        'cjk_index': (code >> 4) & 0x7FF,
        'extension': code & 0xF,
    }
```

## C 参考实现

```c
#include <stdint.h>
#define TABLE_SIZE 20902

static uint32_t skill_table[TABLE_SIZE];

uint32_t cnhe_map(uint32_t unicode) {
    if (unicode < 0x4E00 || unicode > 0x9FA5)
        return 0;
    return skill_table[unicode - 0x4E00];
}

uint32_t cnhe_extract(uint32_t code, uint32_t field) {
    switch (field) {
        case 0: return (code >> 24) & 0xFF;  // 部首
        case 1: return (code >> 19) & 0x1F;  // 笔画
        case 2: return (code >> 15) & 0xF;   // 结构
        default: return 0;
    }
}

uint32_t cnhe_cmp(uint32_t a, uint32_t b) {
    uint32_t ra = (a>>24)&0xFF, rb = (b>>24)&0xFF;
    uint32_t sa = (a>>19)&0x1F, sb = (b>>19)&0x1F;
    uint32_t ta = (a>>15)&0xF, tb = (b>>15)&0xF;
    return abs(ra-rb)*8 + abs(sa-sb)*5 + abs(ta-tb)*4;
}
```

## Skill 表格式

```
Binary file: skill_table_8105.bin (83,608 bytes)
Format: uint32[20902] (每个Unicode码点映射为1个32位编码)
索引: Unicode码点 - 0x4E00 (0x4E00→U+4E00)
```

**数据来源**: 8105 个通用规范汉字（《通用规范汉字表》）
**生成工具**: `scripts/gen_skill_table.py`
