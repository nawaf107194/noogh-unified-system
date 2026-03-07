#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║        NOOGH Cloud Training — A100 80GB Optimized            ║
║        Model:   Gemma 3n E4B (7.9B params)                   ║
║        Dataset: NOOGH V7 (236K samples)                      ║
║        Method:  LoRA + Reward-Weighted SFT                   ║
╚══════════════════════════════════════════════════════════════╝

Usage on RunPod / Vast.ai / Lambda:
1. Upload this script + NOOGH_V7_EXPANDED.jsonl
2. pip install transformers datasets trl peft bitsandbytes accelerate timm
3. huggingface-cli login
4. python train_cloud.py

Estimated time: ~30-45 min on A100 80GB
"""

import os
import re
import json
import torch
import logging
from pathlib import Path
from dataclasses import dataclass

from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG — A100 80GB optimized
# ============================================================================

MODEL_NAME = "google/gemma-3n-E4B-it"        # Full precision base
DATASET_PATH = Path("NOOGH_V7_EXPANDED.jsonl") # Will search common locations
OUTPUT_DIR = Path("noogh_gemma3n_v1")
LORA_OUTPUT = OUTPUT_DIR / "lora_adapter"

# Training — A100 can handle much more
MAX_SEQ_LENGTH = 2048      # Full context
BATCH_SIZE = 4             # A100 handles 4 easily
GRADIENT_ACCUMULATION = 4  # Effective batch = 16
EPOCHS = 3
LEARNING_RATE = 2e-4
WARMUP_RATIO = 0.05
MAX_SAMPLES = 0            # 0 = use ALL samples

# LoRA — can afford larger rank on A100
LORA_R = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.05
LORA_TARGETS = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

# Quantization — 4-bit for efficient training
QUANT_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    llm_int8_enable_fp32_cpu_offload=True,
)

# ============================================================================
# 🏆 REWARD SYSTEM
# ============================================================================

class RewardScorer:
    """
    نظام المكافآت — يقيّم كل عينة تدريب ويعطيها درجة من 0 إلى 1.
    """
    
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
        arabic_chars = len(RewardScorer.ARABIC_PATTERN.findall(text))
        ratio = arabic_chars / max(len(text), 1)
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
    def compute_reward(cls, assistant_text, category="general"):
        weights = {'format': 0.20, 'arabic': 0.15, 'code': 0.25, 'length': 0.20, 'thinking': 0.20}
        scores = {
            'format': cls.score_format(assistant_text),
            'arabic': cls.score_arabic(assistant_text),
            'code': cls.score_code(assistant_text, category),
            'length': cls.score_length(assistant_text),
            'thinking': cls.score_thinking(assistant_text),
        }
        return round(sum(scores[k] * weights[k] for k in weights), 4)


# ============================================================================
# DATA LOADING
# ============================================================================

def find_dataset():
    """Search common locations for the dataset."""
    candidates = [
        DATASET_PATH,
        Path("training_data/NOOGH_V7_EXPANDED.jsonl"),
        Path("/workspace/NOOGH_V7_EXPANDED.jsonl"),
        Path("/root/NOOGH_V7_EXPANDED.jsonl"),
        Path.home() / "NOOGH_V7_EXPANDED.jsonl",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"Dataset not found! Searched: {[str(p) for p in candidates]}")


def load_and_score_dataset(tokenizer):
    """Load V7 dataset, score with rewards, format for Gemma."""
    
    dataset_path = find_dataset()
    logger.info(f"📂 Loading dataset: {dataset_path}")
    
    raw_samples = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    raw_samples.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    logger.info(f"📊 Loaded {len(raw_samples):,} raw samples")
    
    scored = []
    categories = {}
    
    for sample in raw_samples:
        messages = sample.get('messages', [])
        category = sample.get('category', 'general')
        
        if not messages or len(messages) < 2:
            continue
        
        # Extract assistant response
        assistant_text = ""
        for msg in messages:
            if msg.get('role') == 'assistant':
                assistant_text = msg.get('content', '')
                break
        
        if not assistant_text or len(assistant_text) < 5:
            continue
        
        reward = RewardScorer.compute_reward(assistant_text, category)
        
        try:
            formatted_text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )
        except Exception:
            parts = []
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'system':
                    parts.append(f"<start_of_turn>user\n[System: {content}]")
                elif role == 'user':
                    parts.append(f"<start_of_turn>user\n{content}<end_of_turn>")
                elif role == 'assistant':
                    parts.append(f"<start_of_turn>model\n{content}<end_of_turn>")
            formatted_text = "\n".join(parts)
        
        scored.append({'text': formatted_text, 'reward': reward, 'category': category})
        categories[category] = categories.get(category, 0) + 1
    
    logger.info(f"✅ Scored {len(scored):,} valid samples")
    
    # Print categories
    logger.info("📁 Top categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:15]:
        logger.info(f"   {cat}: {count:,}")
    
    # Sort by reward and optionally limit
    scored.sort(key=lambda x: x['reward'], reverse=True)
    
    if MAX_SAMPLES > 0 and len(scored) > MAX_SAMPLES:
        logger.info(f"🏆 Taking top {MAX_SAMPLES:,} samples by reward")
        scored = scored[:MAX_SAMPLES]
    
    rewards = [s['reward'] for s in scored]
    logger.info(f"📈 Reward stats: min={min(rewards):.3f}, max={max(rewards):.3f}, "
                f"mean={sum(rewards)/len(rewards):.3f}")
    
    dataset = Dataset.from_list([{'text': s['text']} for s in scored])
    return dataset


# ============================================================================
# MODEL LOADING
# ============================================================================

def load_model_for_training():
    """Load Gemma 3n with QLoRA for A100 training."""
    
    logger.info(f"📦 Loading model: {MODEL_NAME}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, padding_side="right")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    torch.cuda.empty_cache()
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=QUANT_CONFIG,
        device_map="auto",
        low_cpu_mem_usage=True,
        torch_dtype=torch.bfloat16,
    )
    
    # Prepare for QLoRA training
    model = prepare_model_for_kbit_training(model)
    model.gradient_checkpointing_enable()
    
    # Apply LoRA
    logger.info(f"🔧 Applying LoRA (r={LORA_R}, alpha={LORA_ALPHA})")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGETS,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, lora_config)
    
    trainable, total = model.get_nb_trainable_parameters()
    logger.info(f"📊 Parameters: {trainable:,} trainable / {total:,} total "
                f"({100*trainable/total:.2f}%)")
    
    return model, tokenizer


# ============================================================================
# TRAINING
# ============================================================================

def train():
    """Main training loop — A100 optimized."""
    
    print("\n" + "=" * 60)
    print("🚀 NOOGH Cloud Training — A100 80GB")
    print("=" * 60)
    
    if not torch.cuda.is_available():
        logger.error("❌ No GPU available!")
        return
    
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
    logger.info(f"🎮 GPU: {gpu_name} ({gpu_mem:.1f} GB)")
    
    # Load model
    model, tokenizer = load_model_for_training()
    
    # Load dataset
    dataset = load_and_score_dataset(tokenizer)
    
    # Split 95/5
    split = dataset.train_test_split(test_size=0.05, seed=42)
    train_ds = split['train']
    eval_ds = split['test']
    
    logger.info(f"📈 Train: {len(train_ds):,}, Eval: {len(eval_ds):,}")
    
    # VRAM check
    torch.cuda.empty_cache()
    used = torch.cuda.memory_allocated() / 1e9
    logger.info(f"💾 VRAM after model load: {used:.2f} GB")
    
    # Training config
    training_args = SFTConfig(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        warmup_ratio=WARMUP_RATIO,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        bf16=True,                 # A100 supports bf16 natively
        logging_steps=50,
        save_strategy="steps",
        save_steps=1000,
        save_total_limit=3,
        eval_strategy="steps",
        eval_steps=1000,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_grad_norm=0.3,
        dataloader_pin_memory=True,
        # SFT specific
        max_length=MAX_SEQ_LENGTH,
        dataset_text_field="text",
        packing=True,              # A100 can handle packing
    )
    
    # Trainer
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=training_args,
    )
    
    # Print summary
    total_steps = (len(train_ds) // (BATCH_SIZE * GRADIENT_ACCUMULATION)) * EPOCHS
    print(f"\n{'=' * 60}")
    print("🏃 Starting Training...")
    print(f"   Model:    {MODEL_NAME}")
    print(f"   Dataset:  {len(train_ds):,} train / {len(eval_ds):,} eval")
    print(f"   Epochs:   {EPOCHS}")
    print(f"   Batch:    {BATCH_SIZE} × {GRADIENT_ACCUMULATION} = {BATCH_SIZE * GRADIENT_ACCUMULATION}")
    print(f"   LR:       {LEARNING_RATE}")
    print(f"   LoRA:     r={LORA_R}, α={LORA_ALPHA}")
    print(f"   Seq Len:  {MAX_SEQ_LENGTH}")
    print(f"   Packing:  True")
    print(f"   Est Steps: ~{total_steps:,}")
    print(f"   GPU:      {gpu_name}")
    print("=" * 60 + "\n")
    
    # Train!
    trainer_stats = trainer.train()
    
    # Save
    logger.info(f"💾 Saving LoRA adapter to {LORA_OUTPUT}")
    LORA_OUTPUT.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(LORA_OUTPUT))
    tokenizer.save_pretrained(str(LORA_OUTPUT))
    
    # Save stats
    stats = {
        "model": MODEL_NAME,
        "dataset_samples": len(train_ds),
        "epochs": EPOCHS,
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "learning_rate": LEARNING_RATE,
        "max_seq_length": MAX_SEQ_LENGTH,
        "batch_size": BATCH_SIZE * GRADIENT_ACCUMULATION,
        "train_loss": trainer_stats.training_loss,
        "train_runtime_seconds": trainer_stats.metrics.get('train_runtime', 0),
        "gpu": gpu_name,
        "reward_system": "format(0.20) + arabic(0.15) + code(0.25) + length(0.20) + thinking(0.20)",
    }
    
    with open(OUTPUT_DIR / "training_stats.json", 'w') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print("✅ Training Complete!")
    print(f"   📁 LoRA Adapter: {LORA_OUTPUT}")
    print(f"   📊 Loss: {trainer_stats.training_loss:.4f}")
    print(f"   ⏱️  Time: {trainer_stats.metrics.get('train_runtime', 0)/60:.1f} min")
    print("=" * 60)
    print("\n📥 Download your adapter:")
    print(f"   scp -r user@cloud:{LORA_OUTPUT}/ ./noogh_lora_adapter/")
    print()
    
    return trainer_stats


if __name__ == "__main__":
    train()
