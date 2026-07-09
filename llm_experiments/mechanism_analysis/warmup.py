import urllib.request, json, time
data = json.dumps({"model":"qwen3.5:0.8b","messages":[{"role":"user","content":"你好"}],"stream":False}).encode()
req = urllib.request.Request("http://localhost:11434/api/chat", data=data, headers={"Content-Type":"application/json"})
t0 = time.time()
r = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())["message"]["content"].strip()
print(f"OK ({time.time()-t0:.0f}s)")
