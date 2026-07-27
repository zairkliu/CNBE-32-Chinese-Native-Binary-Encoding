#!/usr/bin/env python3
"""Validate the evidence gate for a CNBE experimental run manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_STATUSES = {"blocked_evidence_incomplete", "verified"}
VERIFIED_REQUIREMENTS = (
    "immutable model or adapter hash linked to the GGUF artifact",
    "base-model revision and license",
    "training configuration and software lockfile",
    "input dataset hash",
    "deterministic train/validation/test split with seed",
    "raw evaluation outputs and executable command",
    "baseline comparison",
    "human review of claim wording",
)


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("manifest root must be a JSON object")
    return payload


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    require(manifest.get("schema_version") == "1.0", "schema_version must be 1.0", errors)
    status = manifest.get("status")
    require(status in ALLOWED_STATUSES, "status must be blocked_evidence_incomplete or verified", errors)

    policy = manifest.get("claim_policy")
    require(isinstance(policy, dict), "claim_policy must be an object", errors)
    if status == "blocked_evidence_incomplete":
        require(
            isinstance(policy, dict) and policy.get("public_performance_claims") == "prohibited",
            "blocked manifests must prohibit public_performance_claims",
            errors,
        )

    artifact = manifest.get("artifact")
    require(isinstance(artifact, dict), "artifact must be an object", errors)
    if isinstance(artifact, dict):
        require(
            isinstance(artifact.get("sha256"), str) and SHA256_RE.fullmatch(artifact["sha256"]) is not None,
            "artifact.sha256 must be a lowercase SHA-256 digest",
            errors,
        )
        require(
            isinstance(artifact.get("size_bytes"), int) and artifact["size_bytes"] > 0,
            "artifact.size_bytes must be a positive integer",
            errors,
        )

    lineages = manifest.get("lineages")
    require(isinstance(lineages, list) and lineages, "lineages must be a non-empty list", errors)
    for lineage in lineages if isinstance(lineages, list) else []:
        require(isinstance(lineage, dict), "each lineage must be an object", errors)
        if not isinstance(lineage, dict):
            continue
        require(isinstance(lineage.get("id"), str) and lineage["id"], "lineage.id is required", errors)
        sources = lineage.get("source_files")
        require(isinstance(sources, list) and sources, f"{lineage.get('id', 'lineage')}: source_files required", errors)
        for source in sources if isinstance(sources, list) else []:
            require(isinstance(source, dict), "source file entry must be an object", errors)
            if isinstance(source, dict):
                require(bool(source.get("path")), "source file path is required", errors)
                require(
                    isinstance(source.get("git_blob_sha"), str) and len(source["git_blob_sha"]) == 40,
                    "source git_blob_sha must be a 40-character Git blob SHA",
                    errors,
                )

    if status == "verified":
        gate = manifest.get("release_gate")
        require(isinstance(gate, dict), "verified manifest requires release_gate", errors)
        completed = gate.get("completed") if isinstance(gate, dict) else None
        require(isinstance(completed, list), "verified manifest requires release_gate.completed", errors)
        if isinstance(completed, list):
            missing = [item for item in VERIFIED_REQUIREMENTS if item not in completed]
            require(not missing, f"verified manifest missing gate items: {', '.join(missing)}", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="path to a run manifest JSON file")
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"RUN MANIFEST INVALID: {error}", file=sys.stderr)
        return 2

    errors = validate(manifest)
    if errors:
        print("RUN MANIFEST INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"RUN MANIFEST PASS: status={manifest['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
