import json, urllib.request, time

url = "http://localhost:11434/api/chat"
headers = {"Content-Type":"application/json", "Connection":"keep-alive"}
base = {"model":"qwen3.5:0.8b","stream":False,"keep_alime":-1,"options":{"temperature":0}}

for i in range(5):
    data = {**base, "messages":[{"role":"user","content":"你好"}]}
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    t0 = time.time()
    r = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
    dt = time.time() - t0
    print(f"Query {i}: {dt:.1f}s")
