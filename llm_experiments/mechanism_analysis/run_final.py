import json, os, sys, urllib.request, time

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:0.8b"
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

CASES = [
    {"sentence": "北京是中国的首都", "question": "中国的首都是哪里？", "options": ["上海", "北京", "广州"], "answer": 1},
    {"sentence": "三角形有三个角", "question": "三角形有几个角？", "options": ["两个", "三个", "四个"], "answer": 1},
    {"sentence": "熊猫喜欢吃竹子", "question": "熊猫喜欢吃什么？", "options": ["竹子", "肉类", "水果"], "answer": 0},
    {"sentence": "苹果是一种水果", "question": "苹果是什么？", "options": ["水果", "动物", "工具"], "answer": 0},
    {"sentence": "太阳从东方升起", "question": "太阳从哪里升起？", "options": ["西方", "东方", "南方"], "answer": 1},
    {"sentence": "地球绕太阳公转一周需要一年", "question": "地球公转一周需要多久？", "options": ["一天", "一月", "一年"], "answer": 2},
    {"sentence": "水在零度时会结冰", "question": "水在什么温度结冰？", "options": ["零度", "一百度", "五十度"], "answer": 0},
    {"sentence": "孔子是中国古代伟大的思想家", "question": "孔子是哪国人？", "options": ["中国", "日本", "韩国"], "answer": 0},
]
ENCODERS = ["unicode", "cnbe_full", "random_bitfield", "radical_only", "stroke_only", "structure_only"]

# Pre-encode
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from cnbe32.db import lookup
import random
rng = random.Random(42)

def encode(text, mode):
    out = []
    for ch in text:
        r = lookup(ch)
        if mode == "unicode": out.append(ch)
        elif mode == "cnbe_full": out.append(f"0x{r['cnbe']:08X}" if r else ch)
        elif mode == "random_bitfield":
            v = r["cnbe"] ^ rng.randint(0, 0xFFFFFFFF) if r else rng.randint(0, 0xFFFFFFFF)
            out.append(f"0x{v & 0xFFFFFFFF:08X}")
        elif mode == "radical_only": out.append(str(r.get("radix",0)) if r else ch)
        elif mode == "stroke_only": out.append(str(r.get("strokes",0)) if r else ch)
        elif mode == "structure_only": out.append(str(r.get("struct_type",0)) if r else ch)
    return " ".join(out)

print("Pre-encoding...", end=" ", flush=True)
encoded = {enc: [encode(tc["sentence"], enc) for tc in CASES] for enc in ENCODERS}
print(f"{len(encoded)} encoders x {len(CASES)} cases")

def query(enc_name, idx, tc):
    prompt = f"编码文本: {encoded[enc_name][idx]}\n问题: {tc['question']}\n选项: {' '.join(f'{i}.{o}' for i,o in enumerate(tc['options']))}\n只输出选项编号(单个数字):"
    data = json.dumps({"model": MODEL, "messages": [{"role":"user","content":prompt}], "stream":False, "options":{"temperature":0}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type":"application/json"})
    t0 = time.time()
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())["message"]["content"].strip()
        dt = time.time() - t0
    except Exception as e:
        return enc_name, idx, tc["answer"], -1, f"ERR:{type(e).__name__}_{time.time()-t0:.0f}s"
    parsed = None
    for ch in r:
        if ch.isdigit() and 0 <= int(ch) < len(tc["options"]):
            parsed = int(ch); break
    return enc_name, idx, tc["answer"], parsed, f"{dt:.1f}s"

results = {}
t_start = time.time()
n_total = 0

for enc in ENCODERS:
    rng = random.Random(42)  # Reset per encoder
    results[enc] = {"correct": 0, "total": 0, "details": []}
    for idx, tc in enumerate(CASES):
        name, i, answer, parsed, dt = query(enc, idx, tc)
        ok = (parsed == answer)
        results[enc]["correct"] += 1 if ok else 0
        results[enc]["total"] += 1
        results[enc]["details"].append({"case": idx, "answer": answer, "got": parsed, "time": dt})
        n_total += 1
        elapsed = time.time() - t_start
        print(f"  [{n_total:2d}/{len(ENCODERS)*len(CASES)}] {enc:20s} #{idx}: {'OK' if ok else 'FAIL'} (got={parsed}) [{dt}] [{elapsed:.0f}s]")

total_t = time.time() - t_start
print(f"\nTime: {total_t:.0f}s for {n_total} queries ({total_t/max(n_total,1):.1f}s/query)")

# Print summary
print(f"\n{'='*50}")
print(f"RESULTS — {MODEL}, {len(CASES)} cases")
print(f"{'='*50}")
sorted_enc = sorted(results.items(), key=lambda x: -x[1]["correct"]/max(x[1]["total"],1))
for enc, data in sorted_enc:
    c, t = data["correct"], data["total"]
    pct = c/t*100
    bar = "█" * int(pct / 5)
    print(f"  {enc:25s} {c:2d}/{t:2d} = {pct:5.1f}% {bar}")

# Save
out = os.path.join(RESULTS_DIR, "mechanism_results.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"model": MODEL, "cases": len(CASES), "results": results}, f, ensure_ascii=False, indent=2)
print(f"\nResults saved to {out}")
