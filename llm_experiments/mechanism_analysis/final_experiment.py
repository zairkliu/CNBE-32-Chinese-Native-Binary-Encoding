import json, os, urllib.request, time, re, sys

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:0.8b"
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

CASES = [
    ("北京是中国的首都", "中国的首都是哪里？", ["上海","北京","广州"], 1),
    ("三角形有三个角", "三角形有几个角？", ["两个","三个","四个"], 1),
]
ENCODERS = ["unicode", "cnbe_full", "random_bitfield"]

sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","src"))
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
            v = r["cnbe"] ^ rng.randint(0,0xFFFFFFFF) if r else rng.randint(0,0xFFFFFFFF)
            out.append(f"0x{v&0xFFFFFFFF:08X}")
    return " ".join(out)

encoded = {enc: [encode(s, enc) for s,_,_,_ in CASES] for enc in ENCODERS}

# Use persistent HTTP connection (reuse TCP connection)
conn = None
def ask(enc, idx):
    global conn
    s, q, opts, ans = CASES[idx]
    prompt = f"编码文本: {encoded[enc][idx]}\n问题: {q}\n选项: {' '.join(f'{i}.{o}' for i,o in enumerate(opts))}\n只输出选项编号:"
    data = json.dumps({"model":MODEL,"messages":[{"role":"user","content":prompt}],"stream":False,"options":{"temperature":0}}).encode()
    
    if conn is None:
        conn = http.client.HTTPConnection("localhost", 11434, timeout=120)
    
    conn.request("POST", "/api/chat", body=data, headers={"Content-Type":"application/json"})
    r = json.loads(conn.getresponse().read().decode())["message"]["content"].strip()
    
    m = re.search(r"\d+", r)
    parsed = int(m.group()) if m else None
    return parsed == ans, ans, parsed, r[:60]

import http.client

results = {}
t0 = time.time()

for enc in ENCODERS:
    results[enc] = {"ok":0, "n":0}
    for idx in range(len(CASES)):
        ok, ans, got, resp = ask(enc, idx)
        results[enc]["ok"] += 1 if ok else 0
        results[enc]["n"] += 1
        elapsed = time.time() - t0
        print(f"  [{elapsed:4.0f}s] {enc:20s} #{idx}: {'OK' if ok else 'FAIL'} (expect={ans}, got={got}) [{resp}]")

if conn: conn.close()

total_t = time.time() - t0
print(f"\nDone: {total_t:.0f}s for {sum(r['n'] for r in results.values())} queries")

print(f"\n{'='*50}")
print(f"RESULTS ({MODEL}, {len(CASES)} cases)")
print(f"{'='*50}")
for enc in sorted(results, key=lambda e: -results[e]["ok"]/max(results[e]["n"],1)):
    r = results[enc]
    pct = r["ok"]/r["n"]*100
    bar = "█" * int(pct/10)
    print(f"  {enc:25s} {r['ok']}/{r['n']} = {pct:5.1f}% {bar}")

json.dump({"model":MODEL,"cases":len(CASES),"results":results,"time_s":total_t},
    open(os.path.join(RESULTS_DIR,"mechanism_results.json"),"w"), indent=2)
print(f"\nSaved")
