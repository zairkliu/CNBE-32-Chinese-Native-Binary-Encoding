# 出版物训练语料入库报告

日期：2026-08-10
状态：已完成清洗、编码、合并与 assets 重建，等待上云训练

## 一、输入

| 项目 | 值 |
|---|---:|
| 压缩包 | `D:\训练语料\出版物训练.zip` |
| 压缩大小 | 1.18GB |
| 解压后 | 3.09GB |
| MD 文件 | 1,281 本（另有 index.md / corpus.md 不参与训练） |

## 二、清洗

清洗脚本：`repo/tools/clean_publication_markdown.py`

| 项目 | 值 |
|---|---:|
| 清洗文件 | 1,281 |
| 输入字符 | 594,165,740 |
| 输出字符 | 547,889,669 |
| 中文汉字 | 410,592,813 |
| 清理行数 | 262,059 |

质量过滤：

- 输出为 0 字符的损坏文件：9 本，已排除；
- 中文占比 < 30% 的英文/技术书：38 本，已排除；
- 实际入选：1,237 本。

## 三、CNBE 编码

编码脚本：`repo/tools/batch_encode_publications.py`

| 项目 | 值 |
|---|---:|
| 编码文件 | 1,237 |
| 总字符 | 519,621,832 |
| 未知码 | 112,394,541 |
| 覆盖率 | 78.37%（与既有 24M 口径一致，未知主要为标点与西文） |
| 码流大小 | 2.08GB |

## 四、合并 24M 语料

合并脚本：`scripts_src/merge_publication_corpus.py`

| 项目 | 值 |
|---|---:|
| 既有语料 | 7 个 .cnbe |
| 新出版物 | 1,237 个 .cnbe |
| 合并文件 | 1,244 |
| 总 tokens | 544,003,069 |
| 唯一 CNBE 码 | 17,474 |
| mapping 模板数 | 11,457 |

## 五、训练包

```text
D:\训练语料\merged_training_package\
├── data\      # 1244 个 .cnbe，约 2.18GB
└── assets\    # vocab.json / mapping_128/256.json / corpus_manifest.json
```

新增合并语料配置：

```text
config_src/scnet_moe_config_merged_dcu2.yaml           # 128 专家
config_src/scnet_moe_config_merged_dcu2_256.yaml       # 256 专家
config_src/scnet_moe_config_merged_dense_dcu2.yaml     # Dense 对照
config_src/scnet_moe_config_merged_unicode_dcu2.yaml   # Unicode 对照
```

## 五之二、上传包

```text
D:\训练语料\scnet_upload_package_MERGED_DCU.tar.gz   # 约 1.5GB
```

内含代码、1244 个 .cnbe、1237 本清洗文本、merged assets、4 份合并配置
与 `scnet_startup_dcu2.sh`。

## 六、下一步

1. 上传 `merged_training_package` 到 SCNet BW2 环境；
2. smoke 验证；
3. 跑合并语料 Dense / Unicode 对照；
4. 对照通过后跑 128 专家 MoE 训练；
5. 256 专家仅在对照与 128 专家结果都支持时启动。

注意：出版物正文、码流与合并 assets 均属私有数据，只放 `D:\训练语料\`，
不进 GitHub。
