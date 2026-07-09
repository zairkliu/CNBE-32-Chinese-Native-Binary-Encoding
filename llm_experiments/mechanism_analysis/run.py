import json, os, sys, time, urllib.request, urllib.error, concurrent.futures
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from encoder import get_all_encoders

OLLAMA_URL = "http://localhost:11434/api/chat"
TIMEOUT = 120
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
MODEL = "qwen3.5:0.8b"

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

def query_one(model, enc_name, idx, tc, encoded_text):
    prompt = f"编码文本: {encoded_text}\n问题: {tc['question']}\n选项: {' '.join(f'{i}.{o}' for i,o in enumerate(tc['options']))}\n只输出选项编号(单个数字):"
    data = json.dumps({"model": model, "messages": [{"role":"user","content":prompt}], "stream":False, "options":{"temperature":0}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            r = json.loads(resp.read().decode())["message"]["content"].strip()
    except Exception as e:
        return enc_name, idx, tc["answer"], -1, f"[ERR:{type(e).__name__}]"
    parsed = None
    for ch in r:
        if ch.isdigit() and 0 <= int(ch) < len(tc["options"]):
            parsed = int(ch); break
    return enc_name, idx, tc["answer"], parsed, r[:80]

if __name__ == "__main__":
    quick = "--quick" in sys.argv
    cases = TEST_CASES[:5] if quick else TEST_CASES
    n_cases = len(cases)

    print(f"CNBE-32 Mechanism Analysis — Parallel Mode")
    print(f"Model: {MODEL}")
    print(f"Cases: {n_cases}")
    print()

    # Pre-encode in main thread
    print("Pre-encoding...", end=" ", flush=True)
    encoded_texts = {}
    for enc in get_all_encoders():
        encoded_texts[enc.name] = [enc.encode(tc["sentence"]) for tc in cases]
    print(f"{len(encoded_texts)} encoders done")

    # Run all queries in parallel (pre-encoded, no DB access in workers)
    all_tasks = []
    for enc in get_all_encoders():
        for i, tc in enumerate(cases):
            encoded = encoded_texts[enc.name][i]
            all_tasks.append((enc.name, i, tc, encoded))

    print(f"Querying Ollama ({len(all_tasks)} queries)...")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {executor.submit(query_one, MODEL, e, i, tc, enc_text): (e, i) for e, i, tc, enc_text in all_tasks}
        done = 0
        for f in concurrent.futures.as_completed(future_map):
            enc_name, idx, answer, parsed, resp = f.result()
            if enc_name not in results:
                results[enc_name] = {"correct": 0, "total": 0, "details": []}
            results[enc_name]["total"] += 1
            if parsed == answer:
                results[enc_name]["correct"] += 1
            results[enc_name]["details"].append({
                "sentence": cases[idx]["sentence"], "question": cases[idx]["question"],
                "answer": answer, "parsed": parsed, "response": resp
            })
            done += 1
            if done % 5 == 0:
                print(f"  [{done}/{len(all_tasks)}]", flush=True)

    # Print results
    print(f"\n{'='*50}")
    print(f"RESULTS — {n_cases} cases, {MODEL}")
    print(f"{'='*50}")
    sorted_enc = sorted(results.items(), key=lambda x: -x[1]["correct"]/max(x[1]["total"],1))
    for enc_name, data in sorted_enc:
        acc = data["correct"] / data["total"] * 100
        bar = "█" * int(acc / 4)
        print(f"  {enc_name:20s} {data['correct']:2d}/{data['total']} = {acc:5.1f}% {bar}")

    # Save
    outfile = os.path.join(RESULTS_DIR, "mechanism_results.json")
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump({"model": MODEL, "test_cases": n_cases, "results": results}, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {outfile}")
