# -*- coding: utf-8 -*-
"""CNBE-MoE Phase 0/1：真实数据上的 Dense vs CNBE-MoE 对比。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from src.cnbe_router import build_balanced_mapping
from src.data import CodeDataset, build_vocab, id_to_code_array, load_codes
from src.train import train_eval

ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="CNBE-MoE 原型对比")
    parser.add_argument("--cnbe-paths", nargs="+", default=[
        r"C:\Users\zairk\Documents\Codex\2026-07-27\https-github-com-zairkliu-cnbe-32\cnbe_compression_experiment\outputs\zzjh_294.cnbe",
        r"C:\Users\zairk\Documents\Codex\2026-07-27\https-github-com-zairkliu-cnbe-32\jinyong_repro\outputs\jinyong.cnbe",
        r"C:\Users\zairk\Documents\Codex\2026-07-27\https-github-com-zairkliu-cnbe-32\caixin_repro\outputs\caixin.cnbe",
        r"C:\Users\zairk\Documents\Codex\2026-07-27\https-github-com-zairkliu-cnbe-32\sushi_repro\outputs\sushi.cnbe",
    ])
    parser.add_argument("--mapping", default=r"C:\Users\zairk\Documents\Codex\2026-07-27\https-github-com-zairkliu-cnbe-32\cnbe_moe\outputs\struct_expert_map_16.json")
    parser.add_argument("--mapping64", default=r"C:\Users\zairk\Documents\Codex\2026-07-27\https-github-com-zairkliu-cnbe-32\cnbe_moe\outputs\struct_expert_map_64.json")
    parser.add_argument("--max-train-tokens", type=int, default=6_000_000)
    parser.add_argument("--max-eval-tokens", type=int, default=300_000)
    parser.add_argument("--seq-len", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--d-model", type=int, default=384)
    parser.add_argument("--d-ff", type=int, default=1536)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--experts", type=int, default=8)
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--aux-loss-weight", type=float, default=0.1)
    parser.add_argument("--compile", action="store_true", help="使用 torch.compile / Triton 加速")
    parser.add_argument("--triton-kernel", action="store_true", help="使用自写 Triton grouped GEMM kernel")
    parser.add_argument("--balance-weight", type=float, default=0.0, help="路由均衡损失权重")
    parser.add_argument("--router", choices=["table", "learned"], default="table")
    parser.add_argument("--only", default="", help="只运行指定配置，逗号分隔")
    parser.add_argument("--output", default="outputs/cnbe_moe_final_result_v2.json")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    print("加载 CNBE 流...", flush=True)
    codes = load_codes(args.cnbe_paths, args.max_train_tokens + args.max_eval_tokens)
    train_codes = codes[: args.max_train_tokens]
    eval_codes = codes[args.max_train_tokens : args.max_train_tokens + args.max_eval_tokens]
    vocab = build_vocab(codes)
    id_to_code = id_to_code_array(vocab).tolist()
    print(f"train={len(train_codes):,} eval={len(eval_codes):,} vocab={len(vocab):,}", flush=True)

    mapping8 = Path("outputs") / "struct_expert_map_8_phase01.json"
    mapping8.parent.mkdir(parents=True, exist_ok=True)
    mapping8.write_text(
        json.dumps(build_balanced_mapping(train_codes, 8), ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print("生成 8 专家均衡映射:", mapping8, flush=True)
    mapping64_3f = Path("outputs") / "struct_expert_map_64_3f_phase.json"
    mapping64_3f.write_text(
        json.dumps(build_balanced_mapping(train_codes, 64, mode=3), ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print("生成 64 专家三字段均衡映射:", mapping64_3f, flush=True)

    train_ds = CodeDataset(train_codes, vocab, args.seq_len)
    eval_ds = CodeDataset(eval_codes, vocab, args.seq_len)

    configs = [
        {"name": "Dense", "use_moe": False, "experts": args.experts, "top_k": args.top_k, "mapping": None},
        {"name": "MoE-8", "use_moe": True, "experts": 8, "top_k": args.top_k, "mapping": str(mapping8)},
        {"name": "MoE-16", "use_moe": True, "experts": 16, "top_k": args.top_k, "mapping": args.mapping},
        {"name": "MoE-64", "use_moe": True, "experts": 64, "top_k": args.top_k, "mapping": args.mapping64},
        {"name": "MoE-64-3f", "use_moe": True, "experts": 64, "top_k": args.top_k, "mapping": str(mapping64_3f)},
        {"name": "MoE-64-learned", "use_moe": True, "experts": 64, "top_k": args.top_k, "mapping": args.mapping64, "learned": True},
    ]
    if args.only:
        allow = {s.strip() for s in args.only.split(",") if s.strip()}
        configs = [c for c in configs if c["name"] in allow]
        print("仅运行:", [c["name"] for c in configs], flush=True)
    results = []
    for cfg in configs:
        print(f"\n=== {cfg['name']} ===", flush=True)
        r = train_eval(
            train_ds,
            eval_ds,
            len(vocab),
            id_to_code,
            use_moe=cfg["use_moe"],
            mapping_path=cfg["mapping"] or "",
            num_experts=cfg["experts"],
            top_k=cfg["top_k"],
            d_model=args.d_model,
            d_ff=args.d_ff,
            n_layers=args.layers,
            n_heads=args.heads,
            batch_size=args.batch_size,
            steps=args.steps,
            device=args.device,
            aux_loss_weight=args.aux_loss_weight,
            compile_model=args.compile,
            use_triton=args.triton_kernel,
            balance_weight=args.balance_weight,
            learned_router=cfg.get("learned", False),
        )
        r["name"] = cfg["name"]
        results.append(r)
        print(json.dumps(r, ensure_ascii=False, indent=2), flush=True)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"config": vars(args), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("保存:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
