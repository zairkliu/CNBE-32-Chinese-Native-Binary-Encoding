#!/usr/bin/env python3
"""Render pilot glyph images from a system CJK font."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]


def pick_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError("no CJK font found")


def render_char(ch: str, font: ImageFont.FreeTypeFont) -> tuple[Image.Image, int]:
    img = Image.new("RGB", (256, 256), "white")
    draw = ImageDraw.Draw(img)
    box = draw.textbbox((0, 0), ch, font=font)
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = (256 - w) // 2 - box[0]
    y = (256 - h) // 2 - box[1]
    draw.text((x, y), ch, fill="black", font=font)
    black = sum(1 for v in img.convert("L").getdata() if v < 128)
    return img, black


def main() -> int:
    scope = json.loads((EXP / "results" / "pilot_scope.json").read_text(encoding="utf-8"))["entries"]
    glyph_dir = EXP / "glyphs"
    glyph_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for entry in scope:
        ch = entry["char"]
        used_font = ""
        render_ok = False
        img = None
        for font_path in FONT_CANDIDATES:
            if not Path(font_path).exists():
                continue
            font = ImageFont.truetype(font_path, 180)
            candidate, black = render_char(ch, font)
            used_font = Path(font_path).name
            if black >= 100:
                img = candidate
                render_ok = True
                break
        if img is None:
            font = pick_font(180)
            img, _ = render_char(ch, font)
        out = glyph_dir / f"{entry['ucp']}.png"
        img.save(out)
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        manifest.append(
            {
                "ucp": entry["ucp"],
                "char": ch,
                "stratum": entry["stratum"],
                "image": str(out.relative_to(REPO)),
                "sha256": digest,
                "font": used_font,
                "render_ok": render_ok,
                "size": 256,
            }
        )
    (EXP / "glyphs" / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "count": len(manifest), "entries": manifest}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("rendered", len(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
