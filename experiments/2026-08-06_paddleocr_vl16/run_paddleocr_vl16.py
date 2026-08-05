#!/usr/bin/env python3
"""Submit Yongle page images to the PaddleOCR-VL-1.6 cloud API and download results.

Usage:
    PADDLEOCR_VL_TOKEN=<token> python3 run_paddleocr_vl16.py \
        --images-dir /path/to/images_full --pages 3..39

The script resumes from jobs.json and pages/ on rerun. Token is read from the
environment only and never written to disk.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
MODEL = "PaddleOCR-VL-1.6"


def submit_job(token: str, image_path: Path) -> str:
    headers = {"Authorization": f"bearer {token}"}
    data = {
        "model": MODEL,
        "optionalPayload": json.dumps(
            {
                "useDocOrientationClassify": False,
                "useDocUnwarping": False,
                "useChartRecognition": False,
            }
        ),
    }
    with open(image_path, "rb") as f:
        resp = requests.post(JOB_URL, headers=headers, data=data, files={"file": f}, timeout=180)
    resp.raise_for_status()
    return resp.json()["data"]["jobId"]


def get_job(token: str, job_id: str) -> dict:
    headers = {"Authorization": f"bearer {token}"}
    resp = requests.get(f"{JOB_URL}/{job_id}", headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()["data"]


def save_page_markdown(jsonl_url: str, page: str, pages_dir: Path, raw_dir: Path) -> bool:
    resp = requests.get(jsonl_url, timeout=180)
    resp.raise_for_status()
    text = resp.text.strip()
    if not text:
        return False
    first = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        first = json.loads(line)
        break
    if first is None or not first.get("result", {}).get("layoutParsingResults"):
        return False
    res = first["result"]["layoutParsingResults"][0]
    md = res.get("markdown", {}).get("text", "")
    pages_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / f"page_{page}.md").write_text(md, encoding="utf-8")
    (raw_dir / f"page_{page}.json").write_text(
        json.dumps(first, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    parser.add_argument("--pages", type=str, default="3-39")
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--max-wait", type=float, default=540.0)
    args = parser.parse_args()

    token = os.environ.get("PADDLEOCR_VL_TOKEN", "")
    if not token:
        print("PADDLEOCR_VL_TOKEN environment variable is required")
        sys.exit(1)

    lo, hi = (int(x) for x in args.pages.split("-"))
    pages = [f"{p:03d}" for p in range(lo, hi + 1)]
    jobs_file = args.out_dir / "jobs.json"
    pages_dir = args.out_dir / "pages"
    raw_dir = args.out_dir / "raw"
    pages_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    jobs: dict[str, str] = {}
    if jobs_file.exists():
        jobs = json.loads(jobs_file.read_text(encoding="utf-8"))

    for page in pages:
        if (pages_dir / f"page_{page}.md").exists():
            print(f"[skip] page {page}: markdown exists")
            continue
        image = args.images_dir / f"page_{page}.png"
        if not image.exists():
            print(f"[skip] page {page}: image missing")
            continue
        if page in jobs:
            print(f"[resume] page {page}: job {jobs[page]}")
            continue
        job_id = submit_job(token, image)
        jobs[page] = job_id
        jobs_file.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[submit] page {page}: job {job_id}")
        time.sleep(1.0)

    deadline = time.time() + args.max_wait
    while time.time() < deadline:
        pending = [p for p in pages if p in jobs and not (pages_dir / f"page_{p}.md").exists()]
        if not pending:
            break
        progress = []
        for page in pending:
            state = get_job(token, jobs[page])
            st = state.get("state")
            progress.append(f"{page}:{st}")
            if st == "done":
                url = state.get("resultUrl", {}).get("jsonUrl", "")
                if save_page_markdown(url, page, pages_dir, raw_dir):
                    print(f"[done] page {page}: markdown saved")
                else:
                    print(f"[warn] page {page}: done but no markdown parsed")
            elif st == "failed":
                print(f"[failed] page {page}: {state.get('errorMsg')}")
                jobs.pop(page, None)
                jobs_file.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[poll] {', '.join(progress)}")
        if all((pages_dir / f"page_{p}.md").exists() for p in pages):
            break
        time.sleep(args.poll_interval)

    remaining = [p for p in pages if not (pages_dir / f"page_{p}.md").exists()]
    if remaining:
        print(f"NOT_DONE: {remaining}")
        sys.exit(2)
    print("ALL_PAGES_DONE")


if __name__ == "__main__":
    main()
