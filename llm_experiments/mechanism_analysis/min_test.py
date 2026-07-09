import json, os, sys, urllib.request, concurrent.futures

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:0.8b"

# 2 cases, 3 critical encoders
CASES = [
    {"sentence": "北京是中国的首都", "question": "中国的首都是哪里？", "options": ["上海", "北京", "广州"], "answer": 1},
    {"sentence": "三角形有三个角", "question": "三角形有几个角？", "options": ["两个", "三个", "四个"], "answer": 1},
]

ENCODERS = ["unicode", "cnbe_full", "random_bitfield"]

# Pre-encode
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from cnbe32.db import lookup
import random

def encode_text(text, mode):
    result = []
    for ch in text:
        r = lookup(ch)
        if mode == "unicode":
            result.append(ch)
        elif mode == "cnbe_full":
            result.append(f"0x{r['cnbe']:08X}" if r else ch)
        elif mode == "random_bitfield":
            val = r["cnbe"] ^ random.randint(0, 0xFFFFFFFF) if r else random.randint(0, 0xFFFFFFFF)
            result.append(f"0x{val & 0xFFFFFFFF:08X}")
        elif mode == "radical_only":
            result.append(str(r.get("radix", 0)) if r else ch)
    return " ".join(result)

encoded = {enc: [encode_text(tc["sentence"], enc) for tc in CASES] for enc in ENCODERS}

def query_one(enc_name, idx, tc):
    prompt = f"编码文本: {encoded[enc_name][idx]}\n问题: {tc['question']}\n选项: {' '.join(f'{i}.{o}' for i,o in enumerate(tc['options']))}\n只输出选项编号(单个数字):"
    data = json.dumps({"model": MODEL, "messages": [{"role":"user","content":prompt}], "stream":False, "options":{"temperature":0}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type":"application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())["message"]["content"].strip()
    parsed = None
    for ch in r:
        if ch.isdigit() and 0 <= int(ch) < len(tc["options"]):
            parsed = int(ch); break
    return enc_name, parsed == tc["answer"]

# Run all 6 queries in parallel
print(f"Running: {len(ENCODERS)} encoders x {len(CASES)} cases = {len(ENCODERS)*len(CASES)} queries")
results = {enc: 0 for enc in ENCODERS}

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(query_one, enc, idx, tc) for enc in ENCODERS for idx, tc in enumerate(CASES)]
    for f in concurrent.futures.as_completed(futs):
        enc, ok = f.result()
        results[enc] += 1 if ok else 0
        print(f"  {enc}: {'OK' if ok else 'FAIL'}")

print(f"\nResults:")
for enc in ENCODERS:
    print(f"  {enc:20s}: {results[enc]}/{len(CASES)} = {results[enc]/len(CASES)*100:.0f}%")
