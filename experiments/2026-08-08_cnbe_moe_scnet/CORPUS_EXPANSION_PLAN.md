# CNBE-MoE 语料扩量计划

日期：2026-08-10
状态：规划中，待 L20 训练验证完成后执行

## 一、当前语料

| 语料 | 字符数 | 来源 |
|---|---:|---|
| zzjh_294 | 4,558,886 | 资治通鉴 胡注繁体直排本 MOBI |
| luxun_18 | 3,864,304 | 鲁迅全集 2005 版 MOBI |
| agatha | 7,804,198 | 阿加莎全集 EPUB |
| csbook | 280,766 | Linux 程序设计 AZW3 |
| jinyong | 7,558,400 | 金庸作品全集 AZW3 |
| caixin | 286,399 | 财新周刊合订 EPUB |
| sushi | 28,284 | 苏文忠公诗集 DJVU |
| 合计 | 24,381,237 | - |

当前 24M tokens 只能做架构验证，不足以训练可用语言模型。扩量目标建议分两期：

| 阶段 | 目标 | 用途 |
|---|---:|---|
| P1 | 100M tokens | 256 共享专家 + 更大 d_model 的正式验证 |
| P2 | 1B+ tokens | 接近可用的中文原生模型实验 |

## 二、扩量来源

### 古籍与经典（公版优先）

- 中国哲学书电子化计划（ctext.org）全文
- 识典古籍公开章节（已有抓取基础）
- 二十四史、全唐诗、全宋词、全元曲
- 四库全书公开子集、永乐大典影像校订文本
- 先秦诸子、经史子集常见公版整理本

### 现代中文公开语料

- CLUECorpus2020（约 100GB 原始文本）
- WuDaoCorpora / 悟道语料
- SkyPile 中文语料
- 中文维基百科 dump
- 国家语委现代汉语语料库公开子集
- 政府工作报告、法律法规、政策文件（公开文本）
- 公开新闻、杂志、小说、技术文档

### 合成语料（语义增强，推荐）

- OpenBMB/Ultra-FineWeb-L3（ModelScope / HuggingFace，Apache-2.0）
  - 总量 600B+ tokens，中文 200B+ tokens
  - 基于 Ultra-FineWeb 的 L3 精炼：问答对生成 + 多风格改写
  - 适合作为“语义学习”扩展数据，不适合直接全量下载训练

使用原则：

1. 只取中文子集，先抽 1-10 亿字验证管线；
2. 提取纯中文文本，过滤 QA 标记、Markdown、URL、英文片段；
3. 中文覆盖率达到 99% 后才进入正式训练；
4. 全量 200B 中文 token 需要 A800/DCU 集群和高效编码器，不能只靠
   L20 单卡。

### 自有 OCR 语料

- 永乐大典、宋集珍本丛刊等古籍 OCR 校订结果
- 识典古籍人工真值文本

### 出版物 Markdown（AZW3/EPUB 转换）

单本书质量通常很高，但入库前必须清洗，例如：

- 删除 YAML frontmatter、版权页、目录链接
- 删除 `![](media/...)` 图片链接和 `[数字](#...)` 脚注链接
- 删除仅含 `\` 的排版占位行与多余空行
- 保留正文段落，转成纯中文文本

注意版权：商业出版物只能用于个人/授权范围内的研究，不能进入公开语料；
公版书转换的 Markdown 可以进入正式语料。

## 三、编码管线

1. 原始文本统一转为 UTF-8 纯文本 `.txt`；
2. 清洗：去重、去空行、去乱码、统一换行；
3. 用 CNBE-32 编码脚本转成 4B/字码流：

```bash
python experiments/2026-08-02_seven_corpora_compression/scripts/2_cnbe_encode.py \
  new_corpus.txt new_corpus.cnbe \
  --db repo/data/cnbe32.db
```

合成语料下载示例：

```bash
pip install modelscope
modelscope download \
  --dataset OpenBMB/Ultra-FineWeb-L3 \
  --include 'zh*' \
  --local_dir data/ultra_fineweb_l3
```

下载后先检查字段结构，再抽取 `text` 字段中的中文文本。对超大规模
语料建议把 `2_cnbe_encode.py` 的逐字 `struct.pack` 换成 numpy 查表
批量编码，否则亿级语料编码耗时不可接受。

4. 记录覆盖率：

```json
{
  "corpus": "new_corpus",
  "total_chars": 123456789,
  "unknown": 321,
  "coverage": 0.999997,
  "bytes": 493827156,
  "seconds": 1234
}
```

5. 合并全部 `.cnbe`，重建 vocab 与专家映射：

```bash
python experiments/2026-08-08_cnbe_moe_scnet/scripts_src/build_data_assets.py \
  --cnbe-paths \
    data/zzjh_294.cnbe \
    data/luxun_18.cnbe \
    data/agatha.cnbe \
    data/csbook.cnbe \
    data/jinyong.cnbe \
    data/caixin.cnbe \
    data/sushi.cnbe \
    data/new_corpus.cnbe \
  --output-dir assets \
  --experts 128 256
```

6. 更新训练配置中的 `cnbe_paths`，重新打包上传。

清洗出版物 Markdown 的通用步骤：

```bash
# 删除 YAML frontmatter 与图片/脚注链接
sed -i '/^---$/,/^---$/d' book.md
sed -i 's/!\[[^]]*\]([^)]*)//g' book.md
sed -i 's/\[[0-9]*\](#[^)]*)//g' book.md
sed -i '/^\\$/d' book.md
sed -i '/^$/N;/^\n$/D' book.md
```

## 四、质量门槛

每条新语料必须满足：

| 指标 | 门槛 |
|---|---:|
| CNBE 覆盖率 | ≥ 99% |
| 未知字 | 记录并人工复核 |
| 重复率 | 句级去重后 ≤ 5% 重复 |
| 乱码/控制字符 | 0 |
| 语种 | 中文为主，外文占比 ≤ 5% |

若生僻字覆盖率不足，优先补录 CNBE 编码；32 位覆盖不了的汉字进入
CNBE-64 扩展实验，不作为当前 32 位训练主数据。

## 五、算力规划

- P1（100M tokens）：L20 单卡可完成，时间约 2-4 天；建议 A800 2 卡，约 1 天内完成
- P2（1B tokens）：必须 A800 2-8 卡，或后续国产 DCU 集群

## 六、下一步

1. 等当前 L20 128 共享专家训练出 `train_metrics.json`；
2. 确认 CNBE 编码可学习后，先补 1-2 个公开语料验证编码管线；
3. 建立语料清单与校验表，再批量扩量。
