#!/usr/bin/env python3
"""
NOOGH Gemma 3n Training Script — Reward-Weighted SFT
====================================================
Model:   unsloth/gemma-3n-E4B-it-bnb-4bit (pre-quantized 4-bit)
Dataset: NOOGH V6 (68,889 samples)
Method:  LoRA + Reward-Weighted SFT
GPU:     RTX 5070 (12GB VRAM)
"""

import os
import re
import json
import math
import torch
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Set memory optimization BEFORE any CUDA init
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG
# ============================================================================

MODEL_NAME = "unsloth/gemma-3n-E4B-it-bnb-4bit"
DATASET_PATH = Path(__file__).parent / "training_data/NOOGH_V6_DATASET.jsonl"
OUTPUT_DIR = Path(__file__).parent / "models/noogh_gemma3n_v1"
LORA_OUTPUT = OUTPUT_DIR / "lora_adapter"

# Training hyperparams — optimized for 12GB VRAM
MAX_SEQ_LENGTH = 128       # Minimal — 12GB GPU barely fits model + training overhead
BATCH_SIZE = 1             # Micro-batch (12GB VRAM tight)
GRADIENT_ACCUMULATION = 16 # Effective batch = 16
EPOCHS = 2
LEARNING_RATE = 2e-4
WARMUP_RATIO = 0.05
MAX_SAMPLES = 15000        # Use top 15k samples by reward (out of 68k)

# LoRA config
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGETS = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

# ============================================================================
# 🏆 REWARD SYSTEM
# ============================================================================

class RewardScorer:
    """
    نظام المكافآت — يقيّم كل عينة تدريب ويعطيها درجة من 0 إلى 1.
    العينات ذات الدرجات الأعلى تحصل على وزن أكبر في التدريب.
    
    المعايير:
    1. جودة التنسيق (هل الرد منظم ومرتب؟)
    2. جودة العربية (هل فيه محتوى عربي؟)  
    3. جودة الكود (هل الكود مكتمل ومنظم؟)
    4. الطول المناسب (لا قصير جداً ولا طويل جداً)
    5. عمق الفكر (هل فيه تحليل وشرح؟)
    """
    
    # Arabic Unicode range
    ARABIC_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    # Code patterns
    CODE_PATTERNS = re.compile(r'(def |class |import |from |```|if __name__|return |print\()')
    # Structure patterns
    STRUCTURE_PATTERNS = re.compile(r'(^#{1,3}\s|^\d+\.\s|^[-*]\s|^>\s)', re.MULTILINE)
    # Thinking patterns
    THINKING_PATTERNS = re.compile(r'(لأن|بسبب|because|therefore|لذلك|أولاً|ثانياً|الخطوة|المرحلة|التحليل|الحل)', re.IGNORECASE)
    
    @staticmethod
    def score_format(text: str) -> float:
        """مكافأة التنسيق — هل الرد منظم؟"""
        score = 0.3  # Base
        
        # Markdown structure
        structures = len(RewardScorer.STRUCTURE_PATTERNS.findall(text))
        if structures >= 3:
            score += 0.3
        elif structures >= 1:
            score += 0.15
        
        # Paragraphs (not just wall of text)
        paragraphs = text.count('\n\n')
        if paragraphs >= 2:
            score += 0.2
        
        # Code blocks
        if '```' in text:
            score += 0.2
        
        return min(score, 1.0)
    
    @staticmethod
    def score_arabic(text: str) -> float:
        """مكافأة اللغة العربية"""
        arabic_chars = len(RewardScorer.ARABIC_PATTERN.findall(text))
        total_chars = max(len(text), 1)
        ratio = arabic_chars / total_chars
        
        if ratio > 0.3:
            return 1.0  # Arabic heavy
        elif ratio > 0.1:
            return 0.7  # Mixed
        elif ratio > 0.01:
            return 0.4  # Some Arabic
        return 0.2  # English only (still useful)
    
    @staticmethod
    def score_code(text: str, category: str) -> float:
        """مكافأة جودة الكود"""
        if category not in ('code', 'coding', 'code_review', 'architecture'):
            return 0.5  # Neutral for non-code
        
        score = 0.2
        
        # Has code blocks
        if '```' in text:
            score += 0.3
        
        # Has actual code patterns
        code_matches = len(RewardScorer.CODE_PATTERNS.findall(text))
        if code_matches >= 3:
            score += 0.3
        elif code_matches >= 1:
            score += 0.15
        
        # Has explanation alongside code
        if '```' in text and len(text.split('```')[0]) > 50:
            score += 0.2
        
        return min(score, 1.0)
    
    @staticmethod
    def score_length(text: str) -> float:
        """مكافأة الطول المناسب"""
        words = len(text.split())
        
        if words < 10:
            return 0.1   # Too short
        elif words < 30:
            return 0.4   # Brief
        elif words < 100:
            return 0.7   # Good
        elif words < 500:
            return 1.0   # Detailed
        elif words < 1000:
            return 0.8   # Long but ok
        else:
            return 0.5   # Too long (may be padded)
    
    @staticmethod
    def score_thinking(text: str) -> float:
        """مكافأة عمق التفكير"""
        matches = len(RewardScorer.THINKING_PATTERNS.findall(text))
        
        if matches >= 5:
            return 1.0
        elif matches >= 3:
            return 0.7
        elif matches >= 1:
            return 0.4
        return 0.2
    
    @classmethod
    def compute_reward(cls, assistant_text: str, category: str = "general") -> float:
        """
        حساب المكافأة الإجمالية — المتوسط المرجح لكل المعايير
        """
        weights = {
            'format': 0.20,
            'arabic': 0.15,
            'code': 0.25,
            'length': 0.20,
            'thinking': 0.20,
        }
        
        scores = {
            'format': cls.score_format(assistant_text),
            'arabic': cls.score_arabic(assistant_text),
            'code': cls.score_code(assistant_text, category),
            'length': cls.score_length(assistant_text),
            'thinking': cls.score_thinking(assistant_text),
        }
        
        total = sum(scores[k] * weights[k] for k in weights)
        return round(total, 4)


# ============================================================================
# DATA LOADING
# ============================================================================

def load_and_score_dataset(tokenizer) -> Dataset:
    """Load V6 dataset, score with rewards, and format for Gemma chat template."""
    
    logger.info(f"📂 Loading dataset: {DATASET_PATH}")
    
    raw_samples = []
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    raw_samples.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    logger.info(f"📊 Loaded {len(raw_samples)} raw samples")
    
    # Score and format
    scored = []
    categories = {}
    
    for sample in raw_samples:
        messages = sample.get('messages', [])
        category = sample.get('category', 'general')
        
        if not messages or len(messages) < 2:
            continue
        
        # Extract assistant response for scoring
        assistant_text = ""
        for msg in messages:
            if msg.get('role') == 'assistant':
                assistant_text = msg.get('content', '')
                break
        
        if not assistant_text or len(assistant_text) < 5:
            continue
        
        # Compute reward
        reward = RewardScorer.compute_reward(assistant_text, category)
        
        # Format using tokenizer's chat template
        try:
            formatted_text = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=False
            )
        except Exception:
            # Fallback: manual formatting
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
        
        scored.append({
            'text': formatted_text,
            'reward': reward,
            'category': category,
        })
        
        categories[category] = categories.get(category, 0) + 1
    
    logger.info(f"✅ Scored {len(scored)} valid samples")
    
    # Print category distribution
    logger.info("📁 Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:15]:
        logger.info(f"   {cat}: {count}")
    
    # Sort by reward (highest first) and take top MAX_SAMPLES
    scored.sort(key=lambda x: x['reward'], reverse=True)
    
    if len(scored) > MAX_SAMPLES:
        logger.info(f"🏆 Taking top {MAX_SAMPLES} samples by reward score")
        scored = scored[:MAX_SAMPLES]
    
    # Print reward stats
    rewards = [s['reward'] for s in scored]
    logger.info(f"📈 Reward stats: min={min(rewards):.3f}, max={max(rewards):.3f}, "
                f"mean={sum(rewards)/len(rewards):.3f}")
    
    # Create dataset (text only for SFT)
    dataset = Dataset.from_list([{'text': s['text']} for s in scored])
    return dataset


# ============================================================================
# MODEL LOADING
# ============================================================================

def load_model_for_training():
    """Load Gemma 3n with LoRA for training."""
    
    logger.info(f"📦 Loading model: {MODEL_NAME}")
    
    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        padding_side="right",
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Model — pre-quantized, no need for quantization_config
    torch.cuda.empty_cache()
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        max_memory={0: "9GiB", "cpu": "20GiB"},
    )
    
    # Enable training mode on quantized model
    # Skip prepare_model_for_kbit_training — it causes OOM converting to fp32
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    
    # LoRA
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
    
    # Print trainable params
    trainable, total = model.get_nb_trainable_parameters()
    logger.info(f"📊 Parameters: {trainable:,} trainable / {total:,} total "
                f"({100*trainable/total:.2f}%)")
    
    return model, tokenizer


# ============================================================================
# TRAINING
# ============================================================================

def train():
    """Main training loop."""
    
    print("\n" + "=" * 60)
    print("🚀 NOOGH Gemma 3n Training — Reward-Weighted SFT")
    print("=" * 60)
    
    # GPU check
    if not torch.cuda.is_available():
        logger.error("❌ No GPU available!")
        return
    
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
    logger.info(f"🎮 GPU: {gpu_name} ({gpu_mem:.1f} GB)")
    
    # Load model
    model, tokenizer = load_model_for_training()
    
    # Load and score dataset
    dataset = load_and_score_dataset(tokenizer)
    
    # Split — no eval to save memory
    logger.info(f"📈 Train: {len(dataset)} samples")
    
    # VRAM check
    torch.cuda.empty_cache()
    used = torch.cuda.memory_allocated() / 1e9
    logger.info(f"💾 VRAM after model load: {used:.2f} GB")
    
    # Training args
    training_args = SFTConfig(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        warmup_ratio=WARMUP_RATIO,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=True,
        logging_steps=25,
        save_strategy="steps",
        save_steps=500,
        save_total_limit=2,
        eval_strategy="no",
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_grad_norm=0.3,
        dataloader_pin_memory=False,
        remove_unused_columns=True,
        # SFT specific
        max_length=MAX_SEQ_LENGTH,
        dataset_text_field="text",
    )
    
    # SFT Trainer
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=training_args,
    )
    
    # Train
    print("\n" + "=" * 60)
    print("🏃 Starting Training...")
    print(f"   Model:    {MODEL_NAME}")
    print(f"   Dataset:  {len(dataset)} samples (reward-filtered)")
    print(f"   Epochs:   {EPOCHS}")
    print(f"   Batch:    {BATCH_SIZE} × {GRADIENT_ACCUMULATION} = {BATCH_SIZE * GRADIENT_ACCUMULATION}")
    print(f"   LR:       {LEARNING_RATE}")
    print(f"   LoRA:     r={LORA_R}, α={LORA_ALPHA}")
    print(f"   Seq Len:  {MAX_SEQ_LENGTH}")
    print("=" * 60 + "\n")
    
    trainer_stats = trainer.train()
    
    # Save
    logger.info(f"💾 Saving LoRA adapter to {LORA_OUTPUT}")
    LORA_OUTPUT.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(LORA_OUTPUT))
    tokenizer.save_pretrained(str(LORA_OUTPUT))
    
    # Save training stats
    stats = {
        "model": MODEL_NAME,
        "dataset": str(DATASET_PATH),
        "samples_trained": len(train_ds),
        "epochs": EPOCHS,
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "learning_rate": LEARNING_RATE,
        "max_seq_length": MAX_SEQ_LENGTH,
        "train_loss": trainer_stats.training_loss,
        "train_runtime_seconds": trainer_stats.metrics.get('train_runtime', 0),
        "reward_system": "format(0.20) + arabic(0.15) + code(0.25) + length(0.20) + thinking(0.20)",
    }
    
    with open(OUTPUT_DIR / "training_stats.json", 'w') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("✅ Training Complete!")
    print(f"   📁 LoRA Adapter: {LORA_OUTPUT}")
    print(f"   📊 Loss: {trainer_stats.training_loss:.4f}")
    print(f"   ⏱️  Time: {trainer_stats.metrics.get('train_runtime', 0)/60:.1f} min")
    print("=" * 60 + "\n")
    
    return trainer_stats


if __name__ == "__main__":
    train()
