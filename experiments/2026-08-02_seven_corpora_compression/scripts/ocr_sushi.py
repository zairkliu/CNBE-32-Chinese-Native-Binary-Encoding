# -*- coding: utf-8 -*-
"""DJVU 扫描页 -> ddjvu 渲染 -> Ollama deepseek-ocr -> 行级去重纯文本。"""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image

PROMPT = "OCR the image"
OLLAMA_APP = r"C:\Users\zairk\AppData\Local\Programs\Ollama\ollama app.exe"


def restart_ollama() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "ollama app.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([OLLAMA_APP], creationflags=0x08000000)
    for _ in range(90):
        time.sleep(1)
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as resp:
                if resp.status == 200:
                    return
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError("Ollama 重启失败")


def is_cjk(ch: str) -> bool:
    return (
        "\u3400" <= ch <= "\u4dbf"
        or "\u4e00" <= ch <= "\u9fff"
        or "\uf900" <= ch <= "\ufaff"
        or "\U00020000" <= ch <= "\U0002ebef"
    )


def render_page(ddjvu: str, djvu: str, page: int, scale: int) -> bytes:
    proc = subprocess.run(
        [ddjvu, f"-page={page}", f"-scale={scale}", "-format=pnm", djvu, "-"],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace"))
    return proc.stdout


def clean_text(text: str) -> str:
    lines = []
    seen_recent: list[str] = []
    counts: dict[str, int] = {}
    for raw in text.replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if re.fullmatch(r"[|\-_:：\s]+", line):
            continue
        tokens = line.split()
        if tokens and all(t == tokens[0] for t in tokens):
            line = tokens[0]
        else:
            collapsed: list[str] = []
            token_counts: dict[str, int] = {}
            for tok in tokens:
                token_counts[tok] = token_counts.get(tok, 0) + 1
                if token_counts[tok] > 3:
                    continue
                if collapsed and collapsed[-1] == tok:
                    continue
                collapsed.append(tok)
            line = " ".join(collapsed)
        if not line:
            continue
        if line in seen_recent[-4:]:
            continue
        counts[line] = counts.get(line, 0) + 1
        if counts[line] > 3:
            continue
        lines.append(line)
        seen_recent.append(line)
    return "\n".join(lines)


def ocr_page(image_png: bytes, model: str, timeout: int = 240) -> str:
    b64 = base64.b64encode(image_png).decode("ascii")
    body = json.dumps(
        {
            "model": model,
            "prompt": PROMPT,
            "images": [b64],
            "stream": False,
            "options": {"temperature": 0.0},
        }
    ).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data.get("response", "").strip()
            if not text:
                raise RuntimeError(f"空响应: {data.get('error') or data}")
            return text
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"OCR 失败: {last_err}")


def main() -> int:
    parser = argparse.ArgumentParser(description="DJVU 诗集批量 OCR")
    parser.add_argument("--djvu", default="sushi_source.djvu")
    parser.add_argument("--ddjvu", default=r"C:\Program Files (x86)\DjVuLibre\ddjvu.exe")
    parser.add_argument("--out-dir", default="outputs")
    parser.add_argument("--state", default="sushi_ocr.json")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--end-page", type=int, default=132)
    parser.add_argument("--scale", type=int, default=60)
    parser.add_argument("--scales", default="60")
    parser.add_argument("--min-cjk", type=int, default=30)
    parser.add_argument("--restart-every", type=int, default=12)
    parser.add_argument("--model", default="deepseek-ocr")
    args = parser.parse_args()
    scales = [int(s) for s in args.scales.split(",") if s.strip()]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / args.state
    state = []
    if state_path.exists():
        state = [
            r
            for r in json.loads(state_path.read_text(encoding="utf-8"))
            if (r.get("text") and r.get("chars", 0) > 0) or r.get("failed")
        ]
        done = {r["page"] for r in state}
    else:
        done = set()

    processed = 0
    for page in range(args.start_page, args.end_page + 1):
        if page in done:
            print(f"skip page {page}", flush=True)
            continue
        if args.restart_every > 0 and processed > 0 and processed % args.restart_every == 0:
            print("restarting ollama", flush=True)
            restart_ollama()
        t0 = time.perf_counter()
        text = ""
        cjk = 0
        used_scale = args.scale
        for scale in scales:
            used_scale = scale
            try:
                png = render_page(args.ddjvu, args.djvu, page, scale)
                img = Image.open(io.BytesIO(png)).convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                raw_text = ocr_page(buf.getvalue(), args.model)
            except Exception as exc:  # noqa: BLE001
                print(f"page {page} scale {scale} error: {exc}", flush=True)
                continue
            text = clean_text(raw_text)
            cjk = sum(1 for ch in text if is_cjk(ch))
            print(f"page {page} scale {scale}: raw {len(raw_text)}, clean {len(text)}, cjk {cjk}", flush=True)
            if cjk >= args.min_cjk:
                break
        state = [r for r in state if r["page"] != page]
        entry = {"page": page, "scale": used_scale, "text": text, "chars": cjk}
        if cjk < args.min_cjk:
            entry["failed"] = True
        state.append(entry)
        state.sort(key=lambda r: r["page"])
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
        processed += 1
        print(
            f"page {page} done: {len(text)} chars, {cjk} CJK, scale {used_scale}, {time.perf_counter() - t0:.1f}s",
            flush=True,
        )

    raw = "\n".join(r["text"] for r in state)
    (out_dir / "sushi_raw.txt").write_text(raw, encoding="utf-8")
    chars = "".join(ch for ch in raw if is_cjk(ch))
    (out_dir / "sushi.chars.txt").write_text(chars, encoding="utf-8")
    print(f"total pages: {len(state)}, raw: {len(raw):,}, chars: {len(chars):,}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
