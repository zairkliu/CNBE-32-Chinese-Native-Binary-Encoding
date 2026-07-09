import json, os, sys, re, time, torch
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","src"))
from cnbe32.db import lookup
import random
rng = random.Random(42)

MODEL_PATH = r"C:\Users\zairk\cnbe-training1\outputs\cnbe-merged"
CASES = [
    ("北京是中国的首都","中国的首都是哪里？",["上海","北京","广州"],1),
    ("三角形有三个角","三角形有几个角？",["两个","三个","四个"],1),
    ("熊猫喜欢吃竹子","熊猫喜欢吃什么？",["竹子","肉类","水果"],0),
    ("苹果是一种水果","苹果是什么？",["水果","动物","工具"],0),
    ("太阳从东方升起","太阳从哪里升起？",["西方","东方","南方"],1),
    ("水在零度时会结冰","水在什么温度结冰？",["零度","一百度","五十度"],0),
    ("地球绕太阳公转一周需要一年","地球公转一周需要多久？",["一天","一月","一年"],2),
    ("孔子是中国古代伟大的思想家","孔子是哪国人？",["中国","日本","韩国"],0),
]
ENCODERS = ["unicode","cnbe_full","random_bitfield","radical_only"]

def encode(text,mode):
    out=[]
    for ch in text:
        r=lookup(ch)
        if mode=="unicode": out.append(ch)
        elif mode=="cnbe_full": out.append(f"0x{r['cnbe']:08X}" if r else ch)
        elif mode=="random_bitfield":
            v=r["cnbe"]^rng.randint(0,0xFFFFFFFF) if r else rng.randint(0,0xFFFFFFFF)
            out.append(f"0x{v&0xFFFFFFFF:08X}")
        elif mode=="radical_only": out.append(str(r.get("radix",0)) if r else ch)
    return " ".join(out)

print("Loading model...")
from transformers import AutoModelForCausalLM, AutoTokenizer
t0=time.time()
model=AutoModelForCausalLM.from_pretrained(MODEL_PATH, device_map="auto", torch_dtype=torch.float16)
tokenizer=AutoTokenizer.from_pretrained(MODEL_PATH)
print(f"Loaded in {time.time()-t0:.0f}s on {model.device}")

print("Pre-encoding...")
encoded={enc:[encode(tc[0],enc) for tc in CASES] for enc in ENCODERS}

results={}
t0=time.time()
for enc in ENCODERS:
    results[enc]={"ok":0,"n":0}
    for idx,tc in enumerate(CASES):
        prompt=f"编码文本: {encoded[enc][idx]}\n问题: {tc[1]}\n选项: {' '.join(f'{i}.{o}' for i,o in enumerate(tc[2]))}\n只输出选项编号:"
        
        text=tokenizer.apply_chat_template([{"role":"user","content":prompt}],tokenize=False,add_generation_prompt=True)
        inputs=tokenizer(text,return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs=model.generate(**inputs,max_new_tokens=5,do_sample=False)
        
        resp=tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        m=re.search(r"\d+",resp)
        parsed=int(m.group()) if m else None
        ok=(parsed==tc[3])
        results[enc]["ok"]+=1 if ok else 0
        results[enc]["n"]+=1
        print(f"  [{time.time()-t0:4.0f}s] {enc:20s} #{idx}: {'OK' if ok else 'FAIL'} (expect={tc[3]},got={parsed})")

print(f"\n{'='*45}")
print(f"RESULTS — merged LoRA model, {len(CASES)} cases")
print(f"{'='*45}")
for enc in sorted(results,key=lambda e:-results[e]["ok"]/max(results[e]["n"],1)):
    r=results[enc]; pct=r["ok"]/r["n"]*100
    print(f"  {enc:25s} {r['ok']}/{r['n']} = {pct:5.1f}%")
    
json.dump({"model":"cnbe-merged","cases":len(CASES),"results":results},
    open(os.path.join(os.path.dirname(__file__),"results","hf_mechanism.json"),"w"),indent=2)
