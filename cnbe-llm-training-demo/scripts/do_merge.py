import os, torch
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "Qwen/Qwen3.5-0.8B"
ADAPTER = r"C:\Users\zairk\cnbe-training1\outputs\cnbe-lite"
OUTPUT = r"C:\Users\zairk\cnbe-training1\outputs\cnbe-merged"

print("Loading base model...")
base = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, trust_remote_code=True, device_map="auto")
tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True, use_fast=False)

print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(base, ADAPTER)

print("Merging weights...")
merged = model.merge_and_unload()
merged.save_pretrained(OUTPUT, safe_serialization=True)
tok.save_pretrained(OUTPUT)
print(f"Merged model saved to {OUTPUT}")
