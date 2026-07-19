#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNBE-32 Full Training - 5000 Steps with Cleaned Data
Uses full 178K formatted dataset with improved training parameters.
"""

import os
import json
import random
import time
import datetime
import logging
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

# Configuration
MODEL_NAME = "Qwen/Qwen3.5-0.8B"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cnbe_train_full_formatted.jsonl")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "cnbe-5k")

NUM_STEPS = 5000
GRAD_ACCUM = 4
BATCH_SIZE = 1
EFFECTIVE_BATCH = BATCH_SIZE * GRAD_ACCUM

LR = 1e-4
MIN_LR = 1e-5
WARMUP_STEPS = 200
CHECKPOINT_INTERVAL = 500
NUM_SAMPLES = 25000
SEED = 42

# Setup
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(OUTPUT_DIR, "training_5k.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

torch.manual_seed(SEED)
random.seed(SEED)
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load Data
logger.info(f"Loading data from: {DATA_PATH}")
t0 = time.time()
with open(DATA_PATH, "r", encoding="utf-8") as f:
    all_data = [json.loads(line) for line in f]
logger.info(f"Loaded {len(all_data)} samples in {time.time()-t0:.1f}s")

random.shuffle(all_data)
training_data = all_data[:NUM_SAMPLES]
del all_data
logger.info(f"Using {len(training_data)} diverse samples")

# Load Model
logger.info("Loading model...")
t0 = time.time()
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME, dtype=torch.bfloat16, device_map="auto", trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
logger.info(f"Model loaded in {time.time()-t0:.1f}s")
if torch.cuda.is_available():
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}, Mem: {torch.cuda.memory_allocated()/1e9:.2f}GB")

# LoRA Config
lora_config = LoraConfig(
    r=32, lora_alpha=64,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_dropout=0.1, bias="none", task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Optimizer & Scheduler
optimizer = AdamW(model.parameters(), lr=LR, weight_decay=0.01)
scheduler = CosineAnnealingLR(optimizer, T_max=NUM_STEPS - WARMUP_STEPS, eta_min=MIN_LR)

# Training Loop
model.train()
global_step = 0
step_losses = []
start_time = time.time()
data_index = 0

logger.info("=" * 60)
logger.info(f"Training: {NUM_STEPS} steps | batch={EFFECTIVE_BATCH} | lr={LR} -> {MIN_LR}")
logger.info(f"Checkpoints every {CHECKPOINT_INTERVAL} steps")

while global_step < NUM_STEPS:
    for i in range(0, len(training_data), BATCH_SIZE):
        if global_step >= NUM_STEPS:
            break
        
        sample = training_data[data_index % len(training_data)]
        data_index += 1
        
        input_ids = torch.tensor(sample["input_ids"]).unsqueeze(0).to(device)
        attention_mask = torch.tensor(sample["attention_mask"]).unsqueeze(0).to(device)
        labels = torch.tensor(sample["labels"]).unsqueeze(0).to(device)
        
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss / GRAD_ACCUM
        loss.backward()
        
        if (i + 1) % GRAD_ACCUM == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            if global_step >= WARMUP_STEPS:
                scheduler.step()
            optimizer.zero_grad()
            global_step += 1
            
            step_losses.append(outputs.loss.item())
            
            if global_step % 50 == 0:
                avg_loss = sum(step_losses[-50:]) / min(len(step_losses[-50:]), 50)
                current_lr = scheduler.get_last_lr()[0] if global_step >= WARMUP_STEPS else LR
                elapsed = time.time() - start_time
                eta = (elapsed / global_step) * (NUM_STEPS - global_step)
                logger.info(f"Step {global_step}/{NUM_STEPS} | Loss: {avg_loss:.4f} | LR: {current_lr:.6f} | Elapsed: {elapsed:.0f}s | ETA: {eta:.0f}s")
            
            if global_step % CHECKPOINT_INTERVAL == 0:
                ckpt_dir = os.path.join(OUTPUT_DIR, f"checkpoint-{global_step}")
                model.save_pretrained(ckpt_dir)
                logger.info(f"Checkpoint saved: {ckpt_dir}")

# Final Save
model.save_pretrained(OUTPUT_DIR)
total_time = time.time() - start_time
logger.info("=" * 60)
logger.info(f"Training complete! Steps: {global_step} | Time: {total_time:.0f}s ({total_time/60:.1f}m)")
logger.info(f"Final loss: {sum(step_losses[-100:])/min(len(step_losses[-100:]),100):.4f}")
logger.info(f"Model saved to: {OUTPUT_DIR}")
