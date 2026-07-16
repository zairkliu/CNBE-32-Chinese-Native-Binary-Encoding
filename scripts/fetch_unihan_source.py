#!/usr/bin/env python3
"""Verify or explicitly download the pinned Unicode 17.0.0 Unihan archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path("data/sources/unihan-17.0.0.json")
DEFAULT_OUTPUT = Path("build/sources/Unihan-17.0.0.zip")
CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read source manifest {path}: {exc}") from exc
    for key in ("official_url", "allowed_hosts", "size_bytes", "sha256"):
        if key not in manifest:
            raise ValueError(f"source manifest missing required key: {key}")
    return manifest


def validate_url(manifest: dict[str, Any]) -> str:
    url = str(manifest["official_url"])
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Unihan source URL must use HTTPS")
    if parsed.hostname not in set(manifest["allowed_hosts"]):
        raise ValueError(f"Unihan source host is not allowlisted: {parsed.hostname}")
    return url


def verify_archive(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"archive not found: {path}")
    size = path.stat().st_size
    digest = sha256_file(path)
    passed = size == int(manifest["size_bytes"]) and digest == str(manifest["sha256"])
    return {
        "path": str(path),
        "size_bytes": size,
        "expected_size_bytes": int(manifest["size_bytes"]),
        "sha256": digest,
        "expected_sha256": str(manifest["sha256"]),
        "status": "PASS" if passed else "FAIL",
    }


def download_archive(url: str, destination: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="unihan-", suffix=".zip", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "CNBE-32-source-audit/1"})
        with urllib.request.urlopen(request, timeout=60) as response, temporary_path.open("wb") as handle:
            shutil.copyfileobj(response, handle, length=CHUNK_SIZE)
        verification = verify_archive(temporary_path, manifest)
        if verification["status"] != "PASS":
            temporary_path.unlink(missing_ok=True)
            raise ValueError(
                "downloaded archive failed verification: "
                f"size={verification['size_bytes']} sha256={verification['sha256']}"
            )
        if destination.exists():
            existing = verify_archive(destination, manifest)
            if existing["status"] != "PASS":
                raise ValueError(f"refusing to overwrite nonmatching archive: {destination}")
            temporary_path.unlink(missing_ok=True)
            return existing
        os.replace(temporary_path, destination)
        return verify_archive(destination, manifest)
    except (urllib.error.URLError, TimeoutError) as exc:
        temporary_path.unlink(missing_ok=True)
        raise ValueError(f"download failed: {exc}") from exc
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--archive", type=Path, help="local Unihan.zip to verify")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--download", action="store_true", help="download the pinned archive after URL validation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = (repo_root / args.manifest).resolve() if not args.manifest.is_absolute() else args.manifest
    try:
        manifest = load_manifest(manifest_path)
        url = validate_url(manifest)
        if args.download:
            output = (repo_root / args.output).resolve() if not args.output.is_absolute() else args.output
            result = download_archive(url, output, manifest)
        else:
            if args.archive is None:
                raise ValueError("verify-only mode requires --archive; use --download only for explicit retrieval")
            archive = (repo_root / args.archive).resolve() if not args.archive.is_absolute() else args.archive
            result = verify_archive(archive, manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 1
    except ValueError as exc:
        print(f"UNIHAN SOURCE ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
