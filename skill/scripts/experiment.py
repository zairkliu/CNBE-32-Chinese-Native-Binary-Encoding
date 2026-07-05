#!/usr/bin/env python3
"""
CNBE-32 Experiment Runner — Reproduce v1-v7 experiments with Ollama models.
Usage: python experiment.py <experiment_id> [options]

Experiments:
  v2    Sentence understanding (100 sentences, with/without CNBE)
  v4    Long text understanding (22 paragraphs from On Protracted War)
  v6    Numerical format comparison (C/D/F vs Unicode)
  v65   Hard task: rare chars, traditional Chinese, chemistry
  list  List supported models and experiments

Options:
  --model, -m    Ollama model name (default: qwen3.5:0.8b)
  --format, -f   Encoding format: A|C|D|F (default: A)
  --samples, -n  Number of test samples (default: all)
  --output, -o   Output results file (default: auto-generated)
  --dry-run      Print test prompts without calling API

Models (tested): qwen3.5:0.8b, qwen3.5:2b, qwen3.5:4b, qwen3.5:9b,
                 deepseek-r1:8b, gemma4:4b, opt-oss:20b

Examples:
  python experiment.py list
  python experiment.py v2 --model qwen3.5:0.8b
  python experiment.py v4 --model gemma4:4b --samples 5
  python experiment.py v65 --model deepseek-r1:8b --dry-run
"""

import sys, os, json, time, random
from datetime import datetime

# Add parent directory for encode module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from encode import load_table, encode

###############################################################################
# Test Data
###############################################################################

# v2: 10 representative test sentences (full 100 from v2 whte paper)
V2_SENTENCES = [
    ("古典", "岂曰无衣？与子同裳。"),
    ("古典", "学而时习之，不亦说乎？"),
    ("古典", "道可道，非常道；名可名，非常名。"),
    ("古典", "人生自古谁无死？留取丹心照汗青。"),
    ("现代", "今天天气很好，适合出去散步。"),
    ("现代", "人工智能正在改变我们的生活方式。"),
    ("现代", "这篇文章讨论了环境保护的重要性。"),
    ("现代", "科技创新是推动经济发展的核心动力。"),
    ("现代", "坚持就是胜利，不要轻易放弃。"),
    ("现代", "教育是立国之本，强国之基。"),
]

# v4: 10 key paragraphs from On Protracted War (full 22 in whte paper)
V4_PARAGRAPHS = [
    "中国会亡吗？答复：不会亡，最后胜利是中国的。中国能够速胜吗？答复：不能速胜，抗日战争是持久战。",
    "第一阶段，是敌之战略进攻、我之战略防御的时期。第二阶段，是敌之战略保守、我之准备反攻的时期。第三阶段，是我之战略反攻、敌之战略退却的时期。",
    "战争的伟力之最深厚的根源，存在于民众之中。",
    "武器是战争的重要的因素，但不是决定的因素，决定的因素是人不是物。",
    "亡国论者看敌人如神物，看自己如草芥，速胜论者看敌人如草芥，看自己如神物，这些都是错误的。",
    "我们的战争是神圣的、正义的，是进步的、求和平的。",
    "政治是不流血的战争，战争是流血的政治。",
    "中国由劣势到平衡到优势，日本由优势到平衡到劣势。",
    "兵民是胜利之本。",
    "抗日战争的政治目的是驱逐日本帝国主义，建立自由平等的新中国。",
]

# v6: numerical format comparison samples
V6_SAMPLES = [
    "道可道非常道",
    "上善若水",
    "大学之道在明明德",
    "学而不思则罔",
    "有朋自远方来",
]

# v6.5: hard task samples
V65_HARD = [
    ("難", "繁体"),
    ("愛", "繁体"),
    ("學", "繁体"),
    ("體", "繁体"),
    ("H₂O", "化学"),
    ("CO₂", "化学"),
    ("NaOH", "化学"),
    ("C₆H₁₂O₆", "化学"),
    ("𠀀", "生僻"),
    ("𠱂", "生僻"),
]

###############################################################################
# Ollama API Helper
###############################################################################

def call_ollama(model, prompt, raw=True, timeout=30):
    """Call Ollama's chat API and return response text."""
    import urllib.request
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0.3, "num_predict": 256},
        "raw": raw
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = ""
            for line in resp.read().decode().strip().split("\n"):
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        result += chunk["message"]["content"]
            return result.strip()
    except Exception as e:
        return f"[ERROR] {e}"

def is_valid_response(text):
    """Check if response is non-empty and meaningful (>3 chars)."""
    return text and len(text) > 3 and not text.startswith("[ERROR]")

###############################################################################
# Experiment Runners
###############################################################################

def run_v2(model, fmt="A", n_samples=None, dry_run=False):
    """v2: Sentence understanding with/without CNBE encoding."""
    sentences = V2_SENTENCES[:n_samples] if n_samples else V2_SENTENCES
    table = load_table()
    
    results = {"control": [], "cnbe": [], "model": model, "format": fmt}
    
    for cat, sent in sentences:
        # Control: pure text
        ctrl_prompt = f"用一句话概括这段文字的核心含义（20字以内）：{sent}"
        # CNBE: text + encoding
        encoded = encode(sent, table, fmt)
        cnbe_prompt = f"用一句话概括这段文字的核心含义（20字以内）：{encoded}"
        
        if dry_run:
            results["control"].append({"input": sent, "prompt": ctrl_prompt})
            results["cnbe"].append({"input": sent, "prompt": cnbe_prompt})
        else:
            ctrl_resp = call_ollama(model, ctrl_prompt)
            cnbe_resp = call_ollama(model, cnbe_prompt)
            results["control"].append({"input": sent, "response": ctrl_resp, "valid": is_valid_response(ctrl_resp)})
            results["cnbe"].append({"input": sent, "response": cnbe_resp, "valid": is_valid_response(cnbe_resp)})
            time.sleep(0.5)
    
    return results

def run_v4(model, fmt="A", n_samples=None, dry_run=False):
    """v4: Long text (On Protracted War) understanding."""
    paragraphs = V4_PARAGRAPHS[:n_samples] if n_samples else V4_PARAGRAPHS
    table = load_table()
    
    results = {"control": [], "cnbe": [], "model": model, "format": fmt}
    
    for p in paragraphs:
        # Control
        ctrl_prompt = f"用一句话概括这段文字的核心论点（30字以内）：{p}"
        # CNBE
        encoded = encode(p, table, fmt)
        cnbe_prompt = f"用一句话概括这段文字的核心论点（30字以内）：{encoded}"
        
        if dry_run:
            results["control"].append({"prompt": ctrl_prompt[:80] + "..."})
            results["cnbe"].append({"prompt": cnbe_prompt[:80] + "..."})
        else:
            ctrl_resp = call_ollama(model, ctrl_prompt)
            cnbe_resp = call_ollama(model, cnbe_prompt)
            results["control"].append({"response": ctrl_resp, "valid": is_valid_response(ctrl_resp)})
            results["cnbe"].append({"response": cnbe_resp, "valid": is_valid_response(cnbe_resp)})
            time.sleep(0.5)
    
    return results

def run_v6(model, fmt="F", n_samples=None, dry_run=False):
    """v6: Numerical format comparison (CNBE vs Unicode)."""
    samples = V6_SAMPLES[:n_samples] if n_samples else V6_SAMPLES
    table = load_table()
    
    results = {"cnbe": [], "unicode": [], "model": model, "format": fmt}
    
    for s in samples:
        # CNBE numerical
        c_code = encode(s, table, fmt)
        # Unicode numerical (decimal code points)
        u_code = " ".join(f"{ch} {ord(ch)}" for ch in s)
        
        task = "列出这句话中每个字的意思"
        c_prompt = f"{task}：{c_code}"
        u_prompt = f"{task}：{u_code}"
        
        if dry_run:
            results["cnbe"].append({"prompt": c_prompt[:80] + "..."})
            results["unicode"].append({"prompt": u_prompt[:80] + "..."})
        else:
            c_resp = call_ollama(model, c_prompt)
            u_resp = call_ollama(model, u_prompt)
            results["cnbe"].append({"response": c_resp, "valid": is_valid_response(c_resp)})
            results["unicode"].append({"response": u_resp, "valid": is_valid_response(u_resp)})
            time.sleep(0.5)
    
    return results

def run_v65(model, fmt="A", n_samples=None, dry_run=False):
    """v6.5: Hard task - rare chars, traditional, chemistry."""
    samples = V65_HARD[:n_samples] if n_samples else V65_HARD
    table = load_table()
    
    results = {"control": [], "cnbe": [], "model": model, "format": fmt}
    
    for ch, cat in samples:
        if len(ch) == 1 and '\u4e00' <= ch <= '\u9fff':
            encoded = encode(ch, table, fmt)
            ctrl_prompt = f"这是什么字？写出它的拼音和意思：{ch}"
            cnbe_prompt = f"这是什么字？写出它的拼音和意思：{encoded}"
        else:
            ctrl_prompt = f"这是什么化学式？解释它的含义：{ch}"
            cnbe_prompt = f"这是什么化学式？解释它的含义：{ch}"
        
        if dry_run:
            results["control"].append({"char": ch, "prompt": ctrl_prompt[:60]})
            results["cnbe"].append({"char": ch, "prompt": cnbe_prompt[:60]})
        else:
            ctrl_resp = call_ollama(model, ctrl_prompt)
            cnbe_resp = call_ollama(model, cnbe_prompt)
            results["control"].append({"char": ch, "response": ctrl_resp, "valid": is_valid_response(ctrl_resp)})
            results["cnbe"].append({"char": ch, "response": cnbe_resp, "valid": is_valid_response(cnbe_resp)})
            time.sleep(0.5)
    
    return results

###############################################################################
# Summary
###############################################################################

def summarize(results):
    """Print a summary of experiment results."""
    name = results.get("model", "unknown")
    fmt = results.get("format", "A")
    
    if "control" in results and "cnbe" in results:
        ctrl_valid = sum(1 for r in results["control"] if r.get("valid"))
        cnbe_valid = sum(1 for r in results["cnbe"] if r.get("valid"))
        total = len(results["control"])
        print(f"\n{'='*50}")
        print(f"Experiment Results — Model: {name}, Format: {fmt}")
        print(f"{'='*50}")
        print(f"  Control (pure text):  {ctrl_valid}/{total} = {100*ctrl_valid//total}%")
        print(f"  CNBE (encoded):       {cnbe_valid}/{total} = {100*cnbe_valid//total}%")
        if total > 0:
            diff = cnbe_valid - ctrl_valid
            print(f"  Difference:            {diff:+d} ({100*diff//total:+.0f}%)")
            print(f"\n  {'Better' if diff > 0 else 'Worse' if diff < 0 else 'Same'} with CNBE encoding")
    
    if "cnbe" in results and "unicode" in results:
        cnbe_valid = sum(1 for r in results["cnbe"] if r.get("valid"))
        uni_valid = sum(1 for r in results["unicode"] if r.get("valid"))
        total = len(results["cnbe"])
        print(f"\n{'='*50}")
        print(f"CNBE vs Unicode — Model: {name}, Format: {fmt}")
        print(f"{'='*50}")
        print(f"  CNBE numerical:    {cnbe_valid}/{total} = {100*cnbe_valid//total}%")
        print(f"  Unicode numerical: {uni_valid}/{total} = {100*uni_valid//total}%")
        if total > 0:
            diff = cnbe_valid - uni_valid
            print(f"  Difference:         {diff:+d} ({100*diff//total:+.0f}%)")
    
    if all(not r.get("valid", True) for r in results.get("control", [])):
        print("\n  [Note] 0% valid - check if Ollama is running and model is installed")

###############################################################################
# Main
###############################################################################

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CNBE-32 Experiment Runner")
    parser.add_argument("experiment", nargs="?", default="list",
                       help="Experiment: v2, v4, v6, v65, list")
    parser.add_argument("--model", "-m", default="qwen3.5:0.8b",
                       help="Ollama model name")
    parser.add_argument("--format", "-f", choices=["A","C","D","F"], default="A",
                       help="Encoding format")
    parser.add_argument("--samples", "-n", type=int, default=None,
                       help="Number of samples")
    parser.add_argument("--output", "-o", default=None,
                       help="Output JSON file path")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print prompts without calling API")
    
    args = parser.parse_args()
    
    if args.experiment == "list":
        print("CNBE-32 Reproducible Experiments")
        print("=" * 40)
        print("  v2   - Sentence understanding (compare pure text vs CNBE)")
        print("  v4   - Long text / On Protracted War understanding")
        print("  v6   - Numerical format: CNBE vs Unicode")
        print("  v65  - Hard task: rare chars, traditional, chemistry")
        print("\nTested models:")
        print("  qwen3.5:0.8b, qwen3.5:2b, qwen3.5:4b, qwen3.5:9b")
        print("  deepseek-r1:8b, gemma4:4b, opt-oss:20b")
        print("\nExpected results (from published white papers):")
        print("  v2 on 0.8B:  Control ~48% -> CNBE ~87% (+81%)")
        print("  v4 on 0.8B:  Control ~91% -> CNBE ~100% (+9%)")
        print("  v6 Gemma 4B: CNBE +17.4pp vs Unicode")
        print("  Large models (>7B): CNBE marginal benefit ~0")
        return
    
    runners = {"v2": run_v2, "v4": run_v4, "v6": run_v6, "v65": run_v65}
    
    if args.experiment not in runners:
        print(f"Unknown experiment: {args.experiment}")
        print("Use 'python experiment.py list' to see available experiments")
        return
    
    print(f"Running {args.experiment} with {args.model}...")
    print(f"Format: {args.format}, Samples: {args.samples or 'all'}")
    if args.dry_run:
        print("DRY RUN: No API calls will be made\n")
    
    results = runners[args.experiment](args.model, args.format, args.samples, args.dry_run)
    
    summarize(results)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to {args.output}")
    elif not args.dry_run:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = f"cnbe_{args.experiment}_{args.model.replace(':','_')}_{ts}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nAuto-saved to {out_path}")

if __name__ == "__main__":
    main()
