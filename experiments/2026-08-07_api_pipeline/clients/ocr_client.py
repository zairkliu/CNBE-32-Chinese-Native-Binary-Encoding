#!/usr/bin/env python3
"""PaddleOCR-VL-1.6 batch OCR task client with resume and per-page cache.

Protocol is compatible with the 2026-08-06 PaddleOCR-VL-1.6 experiment:
submit image -> poll job state -> download JSONL -> save raw JSON + markdown.
Token is read from the environment and never written to disk.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests
from requests.exceptions import HTTPError

JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
DEFAULT_MODEL = "PaddleOCR-VL-1.6"


@dataclass
class BatchResult:
    submitted: list[str] = field(default_factory=list)
    done: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    remaining: list[str] = field(default_factory=list)


class PaddleOCRVLClient:
    """Async-job client for the PaddleOCR-VL cloud OCR service."""

    def __init__(
        self,
        token: str,
        model: str = DEFAULT_MODEL,
        poll_interval: float = 5.0,
        max_wait: float = 540.0,
    ) -> None:
        self.token = token
        self.model = model
        self.poll_interval = poll_interval
        self.max_wait = max_wait
        self.headers = {"Authorization": f"bearer {token}"}

    def submit(self, image_path: Path) -> str:
        data = {
            "model": self.model,
            "optionalPayload": json.dumps(
                {
                    "useDocOrientationClassify": False,
                    "useDocUnwarping": False,
                    "useChartRecognition": False,
                }
            ),
        }
        last_error: HTTPError | None = None
        for attempt in range(4):
            try:
                with open(image_path, "rb") as fh:
                    resp = requests.post(
                        JOB_URL, headers=self.headers, data=data, files={"file": fh}, timeout=180
                    )
                resp.raise_for_status()
                return resp.json()["data"]["jobId"]
            except HTTPError as exc:
                last_error = exc
                if exc.response is not None and exc.response.status_code in (400, 401, 403):
                    break
                time.sleep(2 * (attempt + 1))
        raise last_error if last_error else RuntimeError("submit failed")

    def poll(self, job_id: str) -> dict:
        resp = requests.get(f"{JOB_URL}/{job_id}", headers=self.headers, timeout=60)
        resp.raise_for_status()
        return resp.json()["data"]

    def save_result(self, state: dict, page: str, pages_dir: Path, raw_dir: Path) -> bool:
        url = state.get("resultUrl", {}).get("jsonUrl", "")
        if not url:
            return False
        resp = requests.get(url, timeout=180)
        resp.raise_for_status()
        lines = [ln.strip() for ln in resp.text.splitlines() if ln.strip()]
        if not lines:
            return False
        payload = json.loads(lines[0])
        results = payload.get("result", {}).get("layoutParsingResults", [])
        if not results:
            return False
        md = results[0].get("markdown", {}).get("text", "")
        pages_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        (pages_dir / f"page_{page}.md").write_text(md, encoding="utf-8")
        (raw_dir / f"page_{page}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True

    def run_batch(
        self,
        images_dir: Path,
        out_dir: Path,
        pages: list[str] | None = None,
        sleep_between_submits: float = 1.0,
    ) -> BatchResult:
        pages_dir = out_dir / "pages"
        raw_dir = out_dir / "raw"
        jobs_file = out_dir / "jobs.json"
        pages_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)

        jobs: dict[str, str] = {}
        if jobs_file.exists():
            jobs = json.loads(jobs_file.read_text(encoding="utf-8"))

        if pages is None:
            pages = sorted(p.stem.replace("page_", "") for p in images_dir.glob("page_*.png"))
        result = BatchResult()

        for page in pages:
            if (pages_dir / f"page_{page}.md").exists():
                result.skipped.append(page)
                continue
            image = images_dir / f"page_{page}.png"
            if not image.exists():
                print(f"[missing] page {page}: image not found")
                continue
            if page in jobs:
                print(f"[resume] page {page}: job {jobs[page]}")
                continue
            job_id = self.submit(image)
            jobs[page] = job_id
            jobs_file.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
            result.submitted.append(page)
            print(f"[submit] page {page}: job {job_id}")
            time.sleep(sleep_between_submits)

        deadline = time.time() + self.max_wait
        while time.time() < deadline:
            pending = [p for p in pages if p in jobs and not (pages_dir / f"page_{p}.md").exists()]
            if not pending:
                break
            for page in pending:
                state = self.poll(jobs[page])
                st = state.get("state")
                print(f"[poll] page {page}: {st}")
                if st == "done":
                    if self.save_result(state, page, pages_dir, raw_dir):
                        result.done.append(page)
                        print(f"[done] page {page}")
                    else:
                        print(f"[warn] page {page}: done but no markdown parsed")
                elif st == "failed":
                    result.failed.append(page)
                    print(f"[failed] page {page}: {state.get('errorMsg')}")
                    jobs.pop(page, None)
                    jobs_file.write_text(
                        json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
            if all((pages_dir / f"page_{p}.md").exists() for p in pages):
                break
            time.sleep(self.poll_interval)

        result.remaining = [
            p for p in pages if not (pages_dir / f"page_{p}.md").exists()
        ]
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="PaddleOCR-VL-1.6 batch task client")
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--pages", type=str, default="")
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--max-wait", type=float, default=540.0)
    args = parser.parse_args()

    token = os.environ.get("PADDLEOCR_VL_TOKEN", "")
    if not token:
        print("PADDLEOCR_VL_TOKEN is required")
        return 1
    pages = None
    if args.pages:
        raw = [p.strip() for p in args.pages.split(",") if p.strip()]
        expanded = []
        for token in raw:
            if "-" in token:
                lo, hi = (int(x) for x in token.split("-", 1))
                expanded.extend(str(i) for i in range(lo, hi + 1))
            else:
                expanded.append(token)
        pages = [
            f"{int(p):03d}" if p.isdigit() else p
            for p in expanded
        ]
    client = PaddleOCRVLClient(token, poll_interval=args.poll_interval, max_wait=args.max_wait)
    result = client.run_batch(args.images_dir, args.out_dir, pages=pages)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0 if not result.remaining else 2


if __name__ == "__main__":
    raise SystemExit(main())
