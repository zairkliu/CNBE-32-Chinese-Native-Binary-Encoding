#!/usr/bin/env python3
"""Consolidate all experiment JSON files into ALL_RESULTS.json."""

import json
import os

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(EXP, "results")

ORDER = [
    "metric_space.json",
    "lattice_range.json",
    "information_theory.json",
    "hyperbolic.json",
    "algebra_spec.json",
    "deep_results.json",
]


def main():
    all_data = {}
    for name in ORDER:
        path = os.path.join(RESULTS, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                all_data[name.replace(".json", "")] = json.load(fh)
    out = os.path.join(RESULTS, "ALL_RESULTS.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(all_data, fh, ensure_ascii=False, indent=2)
    print("wrote", out)


if __name__ == "__main__":
    main()
