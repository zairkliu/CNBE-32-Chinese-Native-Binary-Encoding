# Ollama Model Setup

## Installation

**Linux (WSL/macOS)**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows**: Download from https://ollama.com/download

## Verify Installation
```bash
ollama --version
ollama serve    # start server (daemon on Linux/macOS)
```

## Pull Models

Tested and recommended models:

```bash
# Qwen family (Alibaba, recommended for CNBE)
ollama pull qwen3.5:0.8b    # ~0.8B, best for seeing CNBE effect
ollama pull qwen3.5:2b      # ~2B, moderate CNBE benefit
ollama pull qwen3.5:4b      # ~4B, inflection point
ollama pull qwen3.5:9b      # ~9B, minimal CNBE benefit

# Gemma (Google, CNBE-friendly)
ollama pull gemma4:4b       # ~4B, CNBE > Unicode in tests

# DeepSeek
ollama pull deepseek-r1:8b  # ~8B, thinking mode requires raw: True

# OPT/GPT-OSS
ollama pull opt-oss:20b     # ~20B, weaker Chinese ability
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Connection refused" | `ollama serve` first |
| Timeout on large models | Increase `timeout` in script or use `--samples 3` |
| Model not found | `ollama pull <model-name>` |
| Chinese garbled | Ensure terminal/font supports UTF-8 |
| Ollama uses GPU (Linux) | `ollama run <model>` to verify |
| WSL network issues | Check `Test-NetConnection localhost -Port 11434` |
