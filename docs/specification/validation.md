# 编码验证标准

## 验证层级

### L1: 位域合法性

- STRUCT ≤ 15、STROKE ≤ 31、RADIX ≤ 255
- 编码冲突数为 0（v1-v6 验证通过）
- 覆盖 20902 个 CJK 字符

### L2: 语义一致性

- RADIX 对应真实存在的 214 康熙部首 + 41 现代扩展
- STROKE 与字符实际笔画数一致
- STRUCT 与字符实际结构一致

### L3: 跨模型可读性

| 模型 | 任务 | 准确率 | 实验 |
|------|------|--------|------|
| qwen3.5:0.8B | 单字分类 | 100% | v1 |
| qwen3.5:0.8B | 短句理解 | +81% | v2 |
| Gemma4:4B | 硬任务 | +17.4pp | v6.5.2 |
| TinyGPT | 数学推理 | 优于OneHot | v10.8 |

### L4: 跨领域通用性

CNBE 编码在 9 个领域验证有效（v9.0-v10.8）：
生态学→气象学→金融学→生物学→物理学→社会学→预训练底座→数学推理

## 验证套件

```bash
# 验证位域合法性
python tests/validate_bitfield.py

# 验证映射完整性
python tests/validate_mapping.py

# 复现实验
cd skill/scripts && python experiment.py v2 --model qwen3.5:0.8b
cd v10_8_math_reasoning && python run_v108.py
```
