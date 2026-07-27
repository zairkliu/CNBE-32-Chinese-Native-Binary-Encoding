import os, sys, re, torch, argparse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

RS, SS, STS = 24, 19, 15
app = FastAPI(title="CNBE-32 API")
model, tk = None, None

def load(mp, ap):
    global model, tk
    print(f"Load: {mp}")
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    base = AutoModelForCausalLM.from_pretrained(mp, quantization_config=bnb,
        device_map="auto", trust_remote_code=True, torch_dtype=torch.bfloat16)
    if ap:
        model = PeftModel.from_pretrained(base, ap)
    else:
        model = base
    model.eval()
    tk = AutoTokenizer.from_pretrained(mp, trust_remote_code=True)
    tk.pad_token = tk.eos_token
    print("Ready")

def dh(h):
    m = re.search(r"0x([0-9A-Fa-f]{8})", str(h))
    if not m: return None
    c = int(m.group(1), 16)
    return {"radix":(c>>RS)&0xFF,"stroke":(c>>SS)&0x1F,"struct":(c>>STS)&0x0F,"hex":f"0x{c:08X}"}

def ec(char):
    msgs = [{"role":"system","content":"CNBE-32编码专家。"},{"role":"user","content":f"汉字：{char}\n\n输出CNBE编码信息。"}]
    p = tk.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inp = tk(p, return_tensors="pt", truncation=True, max_length=512).to("cuda")
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=128, temperature=0.1, do_sample=False)
    r = tk.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True).strip()
    return {"char":char,"response":r,"cnbe":dh(r)}

class ER(BaseModel): char: str
class BR(BaseModel): chars: list[str]

@app.get("/health")
def health():
    return {"status":"ok","loaded":model is not None}
@app.post("/encode")
def encode(req: ER):
    if len(req.char)!=1: raise HTTPException(400,"Single char only")
    return ec(req.char)
@app.post("/batch")
def batch(req: BR):
    return [ec(c) for c in req.chars]

if __name__=="__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model",default="/opt/cnbe-training/output/merged-model")
    p.add_argument("--adapter")
    p.add_argument("--port",type=int,default=8000)
    args = p.parse_args()
    load(args.model, args.adapter)
    uvicorn.run(app, host="0.0.0.0", port=args.port)
