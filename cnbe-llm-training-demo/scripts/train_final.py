#!/usr/bin/env python3
"CNBE-32 LoRA Training - Final Lite (500 steps, CUDA supported)"
import os; os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import json, torch, time, sys
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from torch.optim import AdamW
import datetime, random

M = "Qwen/Qwen3.5-0.8B"
D = os.path.join(os.path.dirname(__file__), "..", "data", "cnbe_train_mini.jsonl")
O = os.path.join(os.path.dirname(__file__), "..", "outputs", "cnbe-lite")
S = 500; G = 4; E = 3; LR = 2e-4; L = 256; CK = 100

os.makedirs(O, exist_ok=True)
LG = os.path.join(O, "training_log.txt")

def log(m):
    t = datetime.datetime.now().strftime("%H:%M:%S")
    l = f"[{t}] {m}"
    print(l, flush=True)
    with open(LG, "a", encoding="utf-8") as f: f.write(l + "\n")

with open(LG, "w", encoding="utf-8") as f:
    f.write(f"CNBE-32 Lite Training - {datetime.datetime.now().isoformat()}\n" + "="*60 + "\n\n")

torch.manual_seed(42)
d = torch.device("cuda" if torch.cuda.is_available() else "cpu")
log(f"Device: {d} | CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    log(f"GPU: {torch.cuda.get_device_name(0)}")

log("Loading model...")
t0 = time.time()
model = AutoModelForCausalLM.from_pretrained(M, dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)
tok = AutoTokenizer.from_pretrained(M, trust_remote_code=True)
if tok.pad_token is None: tok.pad_token = tok.eos_token
log(f"Loaded in {time.time()-t0:.1f}s")

lc = LoraConfig(r=32, lora_alpha=64,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_dropout=0.1, bias="none", task_type="CAUSAL_LM")
model = get_peft_model(model, lc)
model.print_trainable_parameters()

data = [json.loads(line) for line in open(D, encoding="utf-8")]
log(f"Data: {len(data)} samples")

model.train()
opt = AdamW(model.parameters(), lr=LR)
gs = 0; ts = time.time()

for ep in range(E):
    random.shuffle(data)
    for idx, s in enumerate(data):
        if gs >= S: break
        t = f"{s['instruction']} Output: {s['output']}"
        enc = tok(t, truncation=True, max_length=L, padding=False, return_tensors="pt")
        ids, lb = enc["input_ids"].to(d), enc["input_ids"].clone().to(d)
        am = enc.get("attention_mask", torch.ones_like(ids)).to(d)
        ls = model(input_ids=ids, attention_mask=am, labels=lb).loss / G
        ls.backward()
        if (idx + 1) % G == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); opt.zero_grad()
            gs += 1
            if gs % CK == 0:
                model.save_pretrained(os.path.join(O, f"checkpoint-{gs}"))
                log(f"Step {gs}/{S} | Loss: {ls.item()*G:.4f} | {time.time()-ts:.1f}s | Checkpoint saved")
    if gs >= S: break

model.save_pretrained(O)
log(f"Done! {gs} steps in {time.time()-ts:.1f}s")
print("NNModel saved to:", O)
