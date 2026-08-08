# SCNet CNBE-MoE 镜像构建报告

日期：2026-08-08

## 镜像

| 项目 | 值 |
|---|---|
| 镜像名 | `cnbe-moe-scnet:0.1` |
| 基础镜像 | `pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime` |
| 构建环境 | Ubuntu-26.04 WSL2 + Docker 29.1.3 |
| 镜像大小 | 约 9.36GB（内容 3.21GB） |

## 镜像内容

- `/app/entrypoint.sh`：容器入口，支持透传任意命令
- `/app/src/`：CNBE-MoE 原型源码（数据、路由、模型、训练、Triton kernel）
- `/app/scripts/train_scnet.py`：单进程训练入口，支持 `--smoke`
- `/app/config/scnet_moe_config_a.yaml`：推荐配置 A

## 验证结果

1. 入口验证：`docker run --rm cnbe-moe-scnet:0.1 python scripts/train_scnet.py --help` 通过。
2. Smoke 训练：挂载真实 `zzjh_294.cnbe`，执行 5 步训练，输出 `smoke_metrics.json`：
   - 训练吞吐：106 steps/s（CPU 小模型）
   - 专家负载 Gini：0.0813
   - 参数量：567,480

## 如何在 SCNet 创建镜像

1. 打开 `https://www.scnet.cn/ui/console/index.html#/image-management/create`；
2. 镜像名：`cnbe-moe-scnet`，标签：`0.1`；
3. 构建源选择 `scnet_cnbe_moe_bundle/`，或上传 `scnet_cnbe_moe_bundle.tar.gz`；
4. Dockerfile 路径：`Dockerfile`；
5. 提交构建。

## 产物

- 构建包：`scnet_cnbe_moe_bundle/`
- 上传包：`scnet_cnbe_moe_bundle.tar.gz`
- 生成脚本：`prepare_scnet_image_bundle.py`

## 备注

- 本地未安装 `nvidia-container-toolkit`，GPU 透传未在本机验证；SCNet 运行时自带 GPU 挂载。
- 当前入口为单进程；DDP 多卡入口将在购买算力后加入。
