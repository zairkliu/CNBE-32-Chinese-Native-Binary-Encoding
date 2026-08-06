#!/usr/bin/env python3
"""Verify trained-model GGUF/Ollama assets and run sample inference."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent

MODELS = {
    "cnbe-32": {
        "gguf": Path(r"C:\Users\zairk\Documents\Codex\2026-07-27\https-github-com-zairkliu-cnbe-32\work\CNBE-32_GGUF_v1.0_package\model-f16.gguf"),
        "expected_sha256": "542E5EDD7594194749DE13953BD7D00903EBB4FCDBAFDFA07C7FFC4B97EEF5F9",
    },
    "cnbe-qwen9b-punct": {
        "gguf": Path(r"D:\models\gguf\cnbe-qwen9b-punct-q4_k_m.gguf"),
    },
}


def ollama_show(model: str) -> str:
    return subprocess.run(
        ["ollama", "show", model], capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout


def ollama_generate(model: str, prompt: str) -> str:
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.0}},
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    report = {"models": {}}
    for name, cfg in MODELS.items():
        show = ollama_show(name)
        report["models"][name] = {"ollama_show": show[:500]}
        gguf = cfg["gguf"]
        if gguf.exists():
            size = gguf.stat().st_size
            digest = sha256(gguf) if "expected_sha256" in cfg else "SKIPPED_LARGE"
            report["models"][name]["gguf_size"] = size
            report["models"][name]["sha256"] = digest
            report["models"][name]["sha256_ok"] = (
                digest == cfg["expected_sha256"] if "expected_sha256" in cfg else None
            )

    sample_cnbe = ["好", "诗", "龍"]
    cnbe_outputs = []
    for ch in sample_cnbe:
        try:
            cnbe_outputs.append({"char": ch, "output": ollama_generate("cnbe-32", f"汉字：{ch}")[:300]})
        except Exception as exc:
            cnbe_outputs.append({"char": ch, "error": str(exc)})
    report["cnbe32_sample"] = cnbe_outputs

    punct_prompt = "古籍句读：\n子曰学而时习之不亦说乎有朋自远方来不亦乐乎\n答案：\n"
    report["qwen9b_punct_sample"] = ollama_generate("cnbe-qwen9b-punct", punct_prompt)[:300]

    out = EXP / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "gguf_ollama_verify.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: (v if k != "models" else {m: {kk: vv for kk, vv in vv.items() if kk != "ollama_show"} for m, vv in v.items()}) for k, v in report.items()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
