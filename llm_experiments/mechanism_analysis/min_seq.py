import json, os, sys, urllib.request, time

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:0.8b"

CASES = [
    {"sentence": "北京是中国的首都", "question": "中国的首都是哪里？", "options": ["上海", "北京", "广州"], "answer": 1},
    {"sentence": "三角形有三个角", "question": "三角形有几个角？", "options": ["两个", "三个", "四个"], "answer": 1},
    {"sentence": "熊猫喜欢吃竹子", "question": "熊猫喜欢吃什么？", "options": ["竹子", "肉类", "水果"], "answer": 0},
]
ENCODERS = ["unicode", "cnbe_full", "random_bitfield", "radical_only"]

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
    return " ".join(out)

encoded = {enc: [encode(tc["sentence"], enc) for tc in CASES] for enc in ENCODERS}

def query(enc_name, idx, tc):
    prompt = f"编码文本: {encoded[enc_name][idx]}\n问题: {tc['question']}\n选项: {' '.join(f'{i}.{o}' for i,o in enumerate(tc['options']))}\n只输出选项编号(单个数字):"
    data = json.dumps({"model": MODEL, "messages": [{"role":"user","content":prompt}], "stream":False, "options":{"temperature":0}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type":"application/json"})
    try:
        t0 = time.time()
        r = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())["message"]["content"].strip()
        dt = time.time() - t0
    except Exception as e:
        return enc_name, idx, tc["answer"], -1, f"[ERR:{type(e).__name__}_{time.time()-t0:.0f}s]"
    parsed = None
    for ch in r:
        if ch.isdigit() and 0 <= int(ch) < len(tc["options"]):
            parsed = int(ch); break
    return enc_name, idx, tc["answer"], parsed, dt

print(f"Running: {len(ENCODERS)} encoders x {len(CASES)} cases = {len(ENCODERS)*len(CASES)} queries")
print(f"Model: {MODEL}\n")

results = {enc: {"correct": 0, "total": 0} for enc in ENCODERS}
t_total = 0

for enc in ENCODERS:
    for idx, tc in enumerate(CASES):
        enc_name, i, answer, parsed, dt = query(enc, idx, tc)
        ok = (parsed == answer)
        results[enc]["correct"] += 1 if ok else 0
        results[enc]["total"] += 1
        t_total += dt if isinstance(dt, (int,float)) else 0
        print(f"  {enc:20s} case {idx}: {'OK' if ok else 'FAIL'} (got={parsed}, expect={answer}) [{dt:.1f}s]")
    print()

print(f"Total queries: {len(ENCODERS)*len(CASES)}, total time: {t_total:.0f}s, avg: {t_total/(len(ENCODERS)*len(CASES)):.1f}s")
print(f"\n{'='*50}")
print(f"RESULTS")
print(f"{'='*50}")
for enc in ENCODERS:
    c = results[enc]["correct"]
    t = results[enc]["total"]
    pct = c/t*100
    bar = "█" * int(pct/5)
    print(f"  {enc:20s} {c}/{t} = {pct:5.1f}% {bar}")
