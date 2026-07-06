#!/usr/bin/env python3
"""CNBE-32 experiment runner"""
import subprocess, os, sys

EXPERIMENTS = {
    "v105": ("v10_5_blackhole", "run_v105.py"),
    "v106": ("v10_6_decision_center", "run_v106.py"),
    "v107": ("v10_7_pretrain_base", "src/train.py"),
    "v108": ("v10_8_math_reasoning", "run_v108.py"),
}

def run(exp_id):
    if exp_id not in EXPERIMENTS:
        print(f"Available: {list(EXPERIMENTS.keys())}"); return
    d, s = EXPERIMENTS[exp_id]
    p = os.path.join(os.path.dirname(__file__), "..", d, s)
    if os.path.exists(p):
        subprocess.run([sys.executable, p], cwd=os.path.dirname(p))
    else:
        print(f"Not found: {p}")

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "v108")
