# SCNet CNBE-MoE 镜像构建包

## 内容

- `Dockerfile`：PyTorch 2.4.1 + CUDA 12.4 运行镜像
- `src/`：CNBE-MoE 原型代码（复制自 `experiments/2026-08-03_cnbe_moe/cnbe_moe_base/src`）
- `scripts/train_scnet.py`：单进程训练入口，支持 smoke / 全量
- `config/scnet_moe_config_a.yaml`：推荐配置 A
- `entrypoint.sh`：容器入口

## 在 SCNet 镜像管理创建

1. 打开 `https://www.scnet.cn/ui/console/index.html#/image-management/create`；
2. 镜像名建议：`cnbe-moe-scnet`，标签：`0.1`；
3. 构建源选择本目录 `scnet_cnbe_moe_bundle/`（或上传 `scnet_cnbe_moe_bundle.tar.gz`）；
4. Dockerfile 路径：`Dockerfile`；
5. 提交构建。

## 本地构建（有 Docker 时）

```bash
docker build -t cnbe-moe-scnet:0.1 ./scnet_cnbe_moe_bundle
```

本项目已在 Ubuntu-26.04 + Docker 29.1.3 完成构建，
并用真实 `zzjh_294.cnbe` 跑通 5 步 smoke 训练。

## 本地 smoke 测试

```bash
docker run --rm --gpus all cnbe-moe-scnet:0.1   python scripts/train_scnet.py --smoke   --cnbe-paths /data/cnbe/zzjh_294.cnbe
```

## SCNet 作业启动命令

```bash
python scripts/train_scnet.py   --config /app/config/scnet_moe_config_a.yaml
```

smoke 验证：

```bash
python scripts/train_scnet.py   --smoke --cnbe-paths /data/cnbe/zzjh_294.cnbe
```

## 注意事项

- 数据文件不打包进镜像，训练时挂载 `/data/cnbe/`；
- 当前入口为单进程，多卡 DDP 入口会在下一阶段加入；
- 本地 GPU 透传需 `nvidia-container-toolkit`；SCNet 运行时自带 GPU 挂载，无需本地验证；
- 私有语料与训练代码不上传公开 GitHub。
