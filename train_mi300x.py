#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     NOOGH Cloud Training — AMD MI300X 192GB Optimized        ║
║     Model:   Gemma 3n E4B (7.9B params) — FULL PRECISION     ║
║     Dataset: NOOGH V7 (236K samples)                         ║
║     Method:  LoRA SFT (no quantization needed!)              ║
╚══════════════════════════════════════════════════════════════╝

MI300X has 192GB HBM3 — no need for 4-bit quantization!
Full bf16 model (~16GB) + LoRA + long sequences + large batches.

Usage:
1. Upload this script + NOOGH_V7_EXPANDED.jsonl  
2. pip install torch transformers datasets trl peft accelerate timm
3. huggingface-cli login
4. python train_mi300x.py

Estimated time: ~15-25 min on MI300X
"""

import os
import re
import json
import torch
import logging
from pathlib import Path

from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG — MI300X 192GB optimized (NO quantization needed!)
# ============================================================================

MODEL_NAME = "google/gemma-3n-E4B-it"
DATASET_PATH = Path("NOOGH_V7_EXPANDED.jsonl")
OUTPUT_DIR = Path("noogh_gemma3n_v1")
LORA_OUTPUT = OUTPUT_DIR / "lora_adapter"

# Training — MI300X can handle massive batches
MAX_SEQ_LENGTH = 4096      # Full long context!
BATCH_SIZE = 8             # MI300X handles 8 easily
GRADIENT_ACCUMULATION = 2  # Effective batch = 16
EPOCHS = 3
LEARNING_RATE = 2e-4
WARMUP_RATIO = 0.05
MAX_SAMPLES = 0            # 0 = use ALL 236K samples

# LoRA — larger rank for better quality (192GB = no limits)
LORA_R = 64
LORA_ALPHA = 128
LORA_DROPOUT = 0.05
LORA_TARGETS = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


# ============================================================================
# 🏆 REWARD SYSTEM
# ============================================================================

class RewardScorer:
    ARABIC_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    CODE_PATTERNS = re.compile(r'(def |class |import |from |```|if __name__|return |print\()')
    STRUCTURE_PATTERNS = re.compile(r'(^#{1,3}\s|^\d+\.\s|^[-*]\s|^>\s)', re.MULTILINE)
    THINKING_PATTERNS = re.compile(
        r'(لأن|بسبب|because|therefore|لذلك|أولاً|ثانياً|الخطوة|المرحلة|التحليل|الحل)',
        re.IGNORECASE
    )
    
    @staticmethod
    def score_format(text):
        score = 0.3
        structures = len(RewardScorer.STRUCTURE_PATTERNS.findall(text))
        if structures >= 3: score += 0.3
        elif structures >= 1: score += 0.15
        if text.count('\n\n') >= 2: score += 0.2
        if '```' in text: score += 0.2
        return min(score, 1.0)
    
    @staticmethod
    def score_arabic(text):
        ratio = len(RewardScorer.ARABIC_PATTERN.findall(text)) / max(len(text), 1)
        if ratio > 0.3: return 1.0
        elif ratio > 0.1: return 0.7
        elif ratio > 0.01: return 0.4
        return 0.2
    
    @staticmethod
    def score_code(text, category):
        if category not in ('code', 'coding', 'code_review', 'architecture', 'Coding'):
            return 0.5
        score = 0.2
        if '```' in text: score += 0.3
        code_matches = len(RewardScorer.CODE_PATTERNS.findall(text))
        if code_matches >= 3: score += 0.3
        elif code_matches >= 1: score += 0.15
        if '```' in text and len(text.split('```')[0]) > 50: score += 0.2
        return min(score, 1.0)
    
    @staticmethod
    def score_length(text):
        words = len(text.split())
        if words < 10: return 0.1
        elif words < 30: return 0.4
        elif words < 100: return 0.7
        elif words < 500: return 1.0
        elif words < 1000: return 0.8
        return 0.5
    
    @staticmethod
    def score_thinking(text):
        matches = len(RewardScorer.THINKING_PATTERNS.findall(text))
        if matches >= 5: return 1.0
        elif matches >= 3: return 0.7
        elif matches >= 1: return 0.4
        return 0.2
    
    @classmethod
    def compute_reward(cls, text, category="general"):
        w = {'format': 0.20, 'arabic': 0.15, 'code': 0.25, 'length': 0.20, 'thinking': 0.20}
        s = {
            'format': cls.score_format(text), 'arabic': cls.score_arabic(text),
            'code': cls.score_code(text, category), 'length': cls.score_length(text),
            'thinking': cls.score_thinking(text),
        }
        return round(sum(s[k] * w[k] for k in w), 4)


# ============================================================================
# DATA LOADING
# ============================================================================

def find_dataset():
    for p in [DATASET_PATH, Path("training_data/NOOGH_V7_EXPANDED.jsonl"),
              Path("/workspace/NOOGH_V7_EXPANDED.jsonl"), Path("/root/NOOGH_V7_EXPANDED.jsonl")]:
        if p.exists():
            return p
    raise FileNotFoundError("Dataset not found! Upload NOOGH_V7_EXPANDED.jsonl")


def load_and_score_dataset(tokenizer):
    dataset_path = find_dataset()
    logger.info(f"📂 Loading: {dataset_path}")
    
    raw = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try: raw.append(json.loads(line))
                except: continue
    
    logger.info(f"📊 {len(raw):,} raw samples")
    
    scored = []
    cats = {}
    for sample in raw:
        msgs = sample.get('messages', [])
        cat = sample.get('category', 'general')
        if len(msgs) < 2: continue
        
        asst = next((m['content'] for m in msgs if m.get('role')=='assistant'), "")
        if len(asst) < 5: continue
        
        reward = RewardScorer.compute_reward(asst, cat)
        
        try:
            text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
        except:
            parts = []
            for m in msgs:
                r, c = m.get('role','user'), m.get('content','')
                if r == 'system': parts.append(f"<start_of_turn>user\n[System: {c}]")
                elif r == 'user': parts.append(f"<start_of_turn>user\n{c}<end_of_turn>")
                elif r == 'assistant': parts.append(f"<start_of_turn>model\n{c}<end_of_turn>")
            text = "\n".join(parts)
        
        scored.append({'text': text, 'reward': reward})
        cats[cat] = cats.get(cat, 0) + 1
    
    logger.info(f"✅ {len(scored):,} valid samples")
    for cat, n in sorted(cats.items(), key=lambda x:-x[1])[:10]:
        logger.info(f"   {cat}: {n:,}")
    
    scored.sort(key=lambda x: x['reward'], reverse=True)
    if MAX_SAMPLES > 0 and len(scored) > MAX_SAMPLES:
        scored = scored[:MAX_SAMPLES]
    
    rewards = [s['reward'] for s in scored]
    logger.info(f"📈 Rewards: min={min(rewards):.3f} max={max(rewards):.3f} mean={sum(rewards)/len(rewards):.3f}")
    
    return Dataset.from_list([{'text': s['text']} for s in scored])


# ============================================================================
# MODEL — NO QUANTIZATION (MI300X has 192GB!)
# ============================================================================

def load_model():
    logger.info(f"📦 Loading {MODEL_NAME} in bf16 (NO quantization — MI300X 192GB)")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, padding_side="right")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Full bf16 — no quantization needed with 192GB!
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        low_cpu_mem_usage=True,
    )
    
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    
    # LoRA r=64 for maximum quality
    logger.info(f"🔧 LoRA r={LORA_R}, α={LORA_ALPHA}")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGETS,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    
    t, total = model.get_nb_trainable_parameters()
    logger.info(f"📊 {t:,} trainable / {total:,} total ({100*t/total:.2f}%)")
    
    return model, tokenizer


# ============================================================================
# TRAINING
# ============================================================================

def train():
    print("\n" + "=" * 60)
    print("🚀 NOOGH Training — MI300X 192GB — FULL POWER")
    print("=" * 60)
    
    if not torch.cuda.is_available():
        logger.error("❌ No GPU!")
        return
    
    gpu = torch.cuda.get_device_name(0)
    mem = torch.cuda.get_device_properties(0).total_memory / 1e9
    logger.info(f"🎮 {gpu} ({mem:.0f} GB)")
    
    model, tokenizer = load_model()
    dataset = load_and_score_dataset(tokenizer)
    
    split = dataset.train_test_split(test_size=0.03, seed=42)
    train_ds, eval_ds = split['train'], split['test']
    logger.info(f"📈 Train: {len(train_ds):,}, Eval: {len(eval_ds):,}")
    
    used = torch.cuda.memory_allocated() / 1e9
    logger.info(f"💾 VRAM used: {used:.1f} GB / {mem:.0f} GB")
    
    args = SFTConfig(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        warmup_ratio=WARMUP_RATIO,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        bf16=True,
        logging_steps=50,
        save_strategy="steps",
        save_steps=1000,
        save_total_limit=3,
        eval_strategy="steps",
        eval_steps=1000,
        optim="adamw_torch",         # Full AdamW (no need for 8-bit on MI300X)
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_grad_norm=0.3,
        dataloader_num_workers=4,     # MI300X can handle parallel loading
        dataloader_pin_memory=True,
        max_length=MAX_SEQ_LENGTH,
        dataset_text_field="text",
        packing=True,
    )
    
    trainer = SFTTrainer(
        model=model, processing_class=tokenizer,
        train_dataset=train_ds, eval_dataset=eval_ds,
        args=args,
    )
    
    est_steps = (len(train_ds) // (BATCH_SIZE * GRADIENT_ACCUMULATION)) * EPOCHS
    print(f"\n{'='*60}")
    print(f"🏃 Training Config:")
    print(f"   GPU:      {gpu} ({mem:.0f} GB)")
    print(f"   Model:    {MODEL_NAME} (bf16, NO quantization)")
    print(f"   Dataset:  {len(train_ds):,} samples")
    print(f"   Epochs:   {EPOCHS}")
    print(f"   Batch:    {BATCH_SIZE} × {GRADIENT_ACCUMULATION} = {BATCH_SIZE*GRADIENT_ACCUMULATION}")
    print(f"   Seq Len:  {MAX_SEQ_LENGTH}")
    print(f"   LoRA:     r={LORA_R}, α={LORA_ALPHA}")
    print(f"   Packing:  True")
    print(f"   Steps:    ~{est_steps:,}")
    print(f"{'='*60}\n")
    
    stats = trainer.train()
    
    # Save
    LORA_OUTPUT.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(LORA_OUTPUT))
    tokenizer.save_pretrained(str(LORA_OUTPUT))
    
    info = {
        "model": MODEL_NAME, "gpu": gpu, "vram_gb": mem,
        "dataset_samples": len(train_ds), "epochs": EPOCHS,
        "lora_r": LORA_R, "lora_alpha": LORA_ALPHA,
        "max_seq_length": MAX_SEQ_LENGTH,
        "batch_size": BATCH_SIZE * GRADIENT_ACCUMULATION,
        "quantization": "NONE (full bf16)",
        "train_loss": stats.training_loss,
        "runtime_min": stats.metrics.get('train_runtime', 0) / 60,
    }
    with open(OUTPUT_DIR / "training_stats.json", 'w') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ Done!")
    print(f"   📁 Adapter: {LORA_OUTPUT}")
    print(f"   📊 Loss: {stats.training_loss:.4f}")
    print(f"   ⏱️  Time: {info['runtime_min']:.1f} min")
    print(f"{'='*60}")


if __name__ == "__main__":
    train()
