#!/usr/bin/env python3
"""DeepSeek V4 API structured-output client.

Key resolution order: DEEPSEEK_API_KEY env, OPENAI_API_KEY env, then
OPENAI_API_KEY in ~/.codex/auth.json. Keys are never written to disk.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


def load_api_key() -> str:
    for env_name in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    auth = Path.home() / ".codex" / "auth.json"
    if auth.exists():
        data = json.loads(auth.read_text(encoding="utf-8"))
        value = str(data.get("OPENAI_API_KEY", "")).strip()
        if value:
            return value
    return ""


@dataclass
class LLMResponse:
    text: str
    elapsed: float
    usage: dict
    status: str = "ok"


class DeepSeekV4Client:
    def __init__(
        self,
        model: str = "deepseek-v4-flash",
        base_url: str = "https://api.deepseek.com/v1/responses",
        max_output_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.key = load_api_key()

    @property
    def available(self) -> bool:
        return bool(self.key)

    def chat(self, prompt: str) -> LLMResponse:
        if not self.available:
            return LLMResponse(text="", elapsed=0.0, usage={}, status="no_key")
        payload = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "reasoning": {"effort": "low"},
        }
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:500]
            return LLMResponse(
                text="", elapsed=time.perf_counter() - t0, usage={}, status=f"http_{exc.code}:{body}"
            )
        elapsed = time.perf_counter() - t0
        text = self._extract_text(data)
        return LLMResponse(text=text, elapsed=elapsed, usage=data.get("usage", {}))

    @staticmethod
    def _extract_text(data: dict) -> str:
        out = []
        for item in data.get("output", []):
            for content in item.get("content", []) or []:
                if content.get("type") == "output_text" and content.get("text"):
                    out.append(content["text"])
        return "\n".join(out).strip()

    @staticmethod
    def parse_json(text: str) -> dict:
        cleaned = text.strip()
        fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.S)
        if fence:
            cleaned = fence.group(1).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end < start:
            raise ValueError("no JSON object found in response")
        return json.loads(cleaned[start : end + 1])


def main() -> int:
    client = DeepSeekV4Client()
    if not client.available:
        print("NO_KEY")
        return 1
    resp = client.chat("返回 JSON：{\"ok\": true}")
    print("status:", resp.status)
    print("elapsed:", round(resp.elapsed, 2))
    try:
        print("parsed:", client.parse_json(resp.text))
    except ValueError as exc:
        print("parse_error:", exc)
        print("raw:", resp.text[:300])
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
