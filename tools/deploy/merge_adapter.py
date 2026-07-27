import os, sys, torch, argparse
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def merge(adapter_path, output_path, model_path=None):
    if model_path is None:
        model_path = "/opt/cnbe-training/models/deepseek-r1-1.5b"
    print(f"Loading base: {model_path}")
    base = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True)
    print(f"Loading adapter: {adapter_path}")
    model = PeftModel.from_pretrained(base, adapter_path)
    print("Merging...")
    merged = model.merge_and_unload()
    print(f"Saving to {output_path}")
    merged.save_pretrained(output_path, safe_serialization=True)
    AutoTokenizer.from_pretrained(model_path, trust_remote_code=True).save_pretrained(output_path)
    print("Done!")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--adapter", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--model")
    args = p.parse_args()
    merge(args.adapter, args.output, args.model)
