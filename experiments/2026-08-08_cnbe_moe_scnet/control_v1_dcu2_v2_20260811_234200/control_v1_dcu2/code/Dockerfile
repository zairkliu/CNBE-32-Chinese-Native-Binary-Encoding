ARG BASE_IMAGE=pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime
FROM ${BASE_IMAGE}

WORKDIR /app

COPY requirements.txt .
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} -r requirements.txt

COPY src ./src
COPY scripts ./scripts
COPY config ./config
COPY notebooks ./notebooks
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV TORCH_HOME=/app/.cache/torch

ENTRYPOINT ["/app/entrypoint.sh"]
