import json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from encoder import get_all_encoders

OLLAMA_URL = "http://localhost:11434/api/chat"
TIMEOUT = 90
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

TEST_CASES = [
    {"sentence": "苹果是一种水果", "question": "苹果是什么？", "options": ["水果", "动物", "工具"], "answer": 0},
    {"sentence": "太阳从东方升起", "question": "太阳从哪里升起？", "options": ["西方", "东方", "南方"], "answer": 1},
    {"sentence": "北京是中国的首都", "question": "中国的首都是哪里？", "options": ["上海", "北京", "广州"], "answer": 1},
    {"sentence": "三角形有三个角", "question": "三角形有几个角？", "options": ["两个", "三个", "四个"], "answer": 1},
    {"sentence": "水在零度时会结冰", "question": "水在什么温度结冰？", "options": ["零度", "一百度", "五十度"], "answer": 0},
    {"sentence": "熊猫喜欢吃竹子", "question": "熊猫喜欢吃什么？", "options": ["竹子", "肉类", "水果"], "answer": 0},
    {"sentence": "孔子是中国古代伟大的思想家", "question": "孔子是哪国人？", "options": ["中国", "日本", "韩国"], "answer": 0},
    {"sentence": "地球绕太阳公转一周需要一年", "question": "地球公转一周需要多久？", "options": ["一天", "一月", "一年"], "answer": 2},
    {"sentence": "他用毛笔写字", "question": "他用什么写字？", "options": ["铅笔", "毛笔", "钢笔"], "answer": 1},
    {"sentence": "妈妈做的菜很好吃", "question": "菜的味道怎么样？", "options": ["好吃", "难吃", "很咸"], "answer": 0},
]

def query_ollama(model, prompt):
    data = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
        "stream": False, "options": {"temperature": 0}}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))["message"]["content"].strip()
    except Exception as e:
        return f"[ERR:{type(e).__name__}]"

def build_prompt(encoded, question, options):
    opts_str = " ".join(f"{i}.{o}" for i, o in enumerate(options))
    return f"编码文本: {encoded}\n问题: {question}\n选项: {opts_str}\n只输出选项编号(单个数字):"

if __name__ == "__main__":
    import sys as _sys
    quick = "--quick" in _sys.argv
    models = ["qwen3.5:0.8b"]
    if "--all-models" in _sys.argv:
        models = ["qwen3.5:0.8b", "qwen3.5:2b", "qwen2.5:0.5b"]

    encoders = get_all_encoders()
    cases = TEST_CASES[:5] if quick else TEST_CASES
    n_cases = len(cases)

    print(f"CNBE-32 Mechanism Analysis")
    print(f"Models: {models}")
    print(f"Encoders: {[e.name for e in encoders]}")
    print(f"Test cases: {n_cases}")
    print()

    # Pre-encode all cases in main thread (avoids SQLite threading issues)
    print("Pre-encoding all test cases...")
    encoded_texts = {}
    for enc in encoders:
        encoded_texts[enc.name] = [enc.encode(tc["sentence"]) for tc in cases]
    print("Done.\n")

    results = {}
    for model in models:
        print(f"Model: {model}")
        print("-" * 50)
        model_results = {}
        for enc in encoders:
            print(f"  Encoding: {enc.name}...", end=" ", flush=True)
            correct = 0
            details = []
            for i, tc in enumerate(cases):
                prompt = build_prompt(encoded_texts[enc.name][i], tc["question"], tc["options"])
                resp = query_ollama(model, prompt)

                parsed = None
                for ch in resp:
                    if ch.isdigit() and 0 <= int(ch) < len(tc["options"]):
                        parsed = int(ch)
                        break
                is_correct = (parsed == tc["answer"])
                if is_correct:
                    correct += 1
                details.append({"sentence": tc["sentence"], "answer": tc["answer"], "got": parsed, "resp": resp[:80]})

            acc = correct / n_cases * 100
            bar = "█" * int(acc / 4)
            print(f"{correct}/{n_cases} = {acc:5.1f}% {bar}")
            model_results[enc.name] = {"accuracy": round(acc/100, 4), "correct": correct, "total": n_cases, "details": details}

        results[model] = model_results

    # Summary table
    print(f"\n{'='*60}")
    print(f"SUMMARY — {n_cases} test cases")
    print(f"{'='*60}")
    print(f"{'Encoder':20s}", end="")
    for model in models:
        print(f"  {model:>15s}", end="")
    print()
    print("-" * 60)
    for enc in encoders:
        print(f"{enc.name:20s}", end="")
        for model in models:
            r = results.get(model, {}).get(enc.name, {})
            acc = r.get("accuracy", 0) * 100
            print(f"  {acc:>5.1f}%         ", end="")
        print()

    # Save results
    out = os.path.join(RESULTS_DIR, f"mechanism_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "test_cases": n_cases, "models": models,
            "encoders": [e.name for e in encoders],
            "results": results
        }, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {out}")
