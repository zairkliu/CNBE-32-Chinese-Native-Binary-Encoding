#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNBE-32 Qwen3.5-0.8B Model Server
Loads the merged LoRA model and provides Chat + Gradio interface.

Usage:
    python scripts/serve_cnbe_model.py
    
    Gradio: http://localhost:7860
    API:    http://localhost:8000/v1/chat/completions
"""

import os
import sys
import gc
import json
import time
import logging
import argparse
from typing import Optional, List, Dict, Any
from threading import Lock
from contextlib import asynccontextmanager

import torch
import uvicorn
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGE_DIR = os.path.join(PROJECT_DIR, "outputs", "cnbe-merged")
DEFAULT_MODEL_PATH = MERGE_DIR

# Global state
model = None
tokenizer = None
model_lock = Lock()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Generation params
GENERATION_KWARGS = {
    "do_sample": True,
    "temperature": 0.7,
    "top_p": 0.85,
    "top_k": 50,
    "repetition_penalty": 1.1,
    "max_new_tokens": 1024,
    "pad_token_id": None,
}

CNBE_SYSTEM_PROMPT = """You are a CNBE-32 (Chinese Native Binary Encoding) specialist.
CNBE-32 encodes character radicals, stroke counts, and structure types into 32-bit binary.

CNBE-32 Format (32-bit):
| Field     | Width | Description    |
|-----------|:-----:|----------------|
| [31:28]   | 4     | Reserved       |
| [27:24]   | 4     | Sub-type       |
| [23:14]   | 10    | Radical ID     |
| [13:8]    | 6     | Stroke count   |
| [7:4]     | 4     | Structure type |
| [3:0]     | 4     | Extra strokes  |

You have mastered the complete CNBE-32 encoding knowledge."""


# FastAPI app
@asynccontextmanager
async def lifespan(app):
    load_model(DEFAULT_MODEL_PATH)
    logger.info(f"Model loaded on {DEVICE.upper()}")
    yield
    global model, tokenizer
    model = None
    tokenizer = None
    gc.collect()
    torch.cuda.empty_cache()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CNBE-32 Qwen API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Model loading
def load_model(model_path: str):
    global model, tokenizer
    with model_lock:
        if model is not None:
            return
        
        logger.info(f"Loading model from: {model_path}")
        logger.info(f"Device: {DEVICE}")
        
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            padding_side="right",
        )
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch.bfloat16,
            device_map="auto" if DEVICE == "cuda" else None,
            trust_remote_code=True,
        )
        model.eval()
        
        if DEVICE == "cpu":
            model = model.to(DEVICE)
        
        logger.info(f"Model loaded. Params: {sum(p.numel() for p in model.parameters())/1e6:.0f}M")
        if torch.cuda.is_available():
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}, Mem: {torch.cuda.memory_allocated()/1e9:.2f}GB")


# Schema
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "cnbe-32-qwen"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


# Core generation
@torch.no_grad()
def generate_response(messages: List[ChatMessage], temperature: float = 0.7, max_tokens: int = 1024) -> str:
    global model, tokenizer
    
    formatted = [{"role": "system", "content": CNBE_SYSTEM_PROMPT}]
    for m in messages:
        formatted.append({"role": m.role, "content": m.content})
    
    if tokenizer.chat_template:
        prompt = tokenizer.apply_chat_template(
            formatted,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        prompt = ""
        for m in formatted:
            prompt += "<|" + m["role"] + "|>\n" + m["content"] + "\n"
        prompt += "<|assistant|>\n"
    
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    gen_kwargs = GENERATION_KWARGS.copy()
    gen_kwargs["temperature"] = temperature
    gen_kwargs["max_new_tokens"] = min(max_tokens, 2048)
    gen_kwargs["pad_token_id"] = tokenizer.pad_token_id or tokenizer.eos_token_id
    
    outputs = model.generate(**inputs, **gen_kwargs)
    
    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return response.strip()


# API routes
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    start = time.time()
    
    response_text = generate_response(
        request.messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens or 1024,
    )
    
    elapsed = time.time() - start
    logger.info(f"Generated {elapsed:.2f}s ({len(response_text)} chars)")
    
    return ChatResponse(
        model=request.model,
        choices=[{
            "index": 0,
            "message": {"role": "assistant", "content": response_text},
            "finish_reason": "stop",
        }],
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    )

@app.get("/v1/models")
async def list_models():
    return {"object": "list", "data": [{"id": "cnbe-32-qwen", "object": "model"}]}

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}


# Gradio interface
def create_gradio_interface():
    import gradio as gr
    
    def chat_fn(message, history):
        history_openai = []
        for h in history:
            history_openai.append(ChatMessage(role=h["role"], content=h["content"]))
        history_openai.append(ChatMessage(role="user", content=message))
        
        response = generate_response(history_openai)
        return response
    
    with gr.Blocks(title="CNBE-32 Qwen Chat") as demo:
        gr.Markdown(
            "# CNBE-32 Qwen3.5-0.8B Chat Demo\n\n"
            "This is a Qwen3.5-0.8B model fine-tuned with **CNBE-32 encoding knowledge** via LoRA.\n\n"
            "**Example questions**:\n"
            "- What is CNBE-32 encoding?\n"
            "- Explain the CNBE-32 bit layout\n"
            "- How does CNBE differ from Unicode?\n"
            "- What radical and stroke count does character X have?"
        )
        
        chatbot = gr.Chatbot(label="CNBE-32 Qwen Chat", height=500)
        msg = gr.Textbox(label="Question", placeholder="e.g. What is CNBE-32?", lines=2)
        clear = gr.Button("Clear")
        
        def respond(message, chat_history):
            if not message.strip():
                return "", chat_history
            
            history_openai = []
            for h in chat_history:
                history_openai.append(ChatMessage(role=h["role"], content=h["content"]))
            history_openai.append(ChatMessage(role="user", content=message))
            
            response = generate_response(history_openai)
            
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": response})
            return "", chat_history
        
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        clear.click(lambda: None, None, chatbot, queue=False)
    
    return demo


# Main
def main():
    parser = argparse.ArgumentParser(description="CNBE-32 Qwen Model Server")
    parser.add_argument("--port", type=int, default=7860, help="Gradio port")
    parser.add_argument("--api-port", type=int, default=8000, help="API port")
    parser.add_argument("--model-path", type=str, default=DEFAULT_MODEL_PATH, help="Model path")
    parser.add_argument("--api-only", action="store_true")
    parser.add_argument("--gradio-only", action="store_true")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("CNBE-32 Qwen3.5-0.8B Model Server")
    logger.info("=" * 60)
    
    load_model(args.model_path)
    
    if args.api_only:
        uvicorn.run(app, host="0.0.0.0", port=args.api_port)
    elif args.gradio_only:
        demo = create_gradio_interface()
        demo.launch(server_name="0.0.0.0", server_port=args.port, show_error=True)
    else:
        import threading
        api_thread = threading.Thread(
            target=uvicorn.run, args=(app,),
            kwargs={"host": "0.0.0.0", "port": args.api_port},
            daemon=True
        )
        api_thread.start()
        
        logger.info(f"API: http://localhost:{args.api_port}")
        logger.info(f"Gradio: http://localhost:{args.port}")
        demo = create_gradio_interface()
        demo.launch(server_name="0.0.0.0", server_port=args.port, show_error=True)


if __name__ == "__main__":
    main()


