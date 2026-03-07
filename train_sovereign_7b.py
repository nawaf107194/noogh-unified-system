#!/usr/bin/env python3
"""
NOOGH Sovereign Training Script
Training Qwen 2.5 7B on Sovereign Dataset (4,032 samples)
"""

import os
import json
import torch
from pathlib import Path
from datasets import Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

# ============================================================================
# CONFIG
# ============================================================================

# Use Sovereign Dataset (FINAL VERSION v5)
DATASET_PATH = Path(__file__).parent / "training_data/SOVEREIGN_MASTER_V5_ULTIMA_FINAL.jsonl"

# Output
OUTPUT_DIR = Path(__file__).parent / "models/noogh_sovereign_7b_v1"

# Model - Use Unsloth's 4-bit Qwen 7B with CPU offload
MODEL_NAME = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit"
USE_CPU_OFFLOAD = True

# Training params (optimized for 7B on single GPU)
MAX_SEQ_LENGTH = 1024  # Reduced from 2048 to fit in 12GB VRAM alongside other services
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 16
EPOCHS = 2
LEARNING_RATE = 1e-4

# ============================================================================
# PROMPT TEMPLATE
# ============================================================================

PROMPT_TEMPLATE = """<|im_start|>system
أنت NOOGH AI - نظام ذكاء اصطناعي هجين متقدم.
تتميز بالتفكير الإبداعي، التحليل العميق، وحل المشكلات المعقدة.
<|im_end|>
<|im_start|>user
[{task_type}] {instruction}
<|im_end|>
<|im_start|>assistant
{output}
<|im_end|>"""


def load_dataset():
    """Load and format Sovereign Dataset."""
    print(f"📂 Loading: {DATASET_PATH}")
    
    samples = []
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    samples.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    
    print(f"📊 Loaded {len(samples)} samples")
    
    # Count by type
    types = {}
    for s in samples:
        t = s.get('task_type', s.get('category', 'unknown'))
        types[t] = types.get(t, 0) + 1
    
    print("\n📁 Distribution:")
    for t, c in sorted(types.items(), key=lambda x: -x[1])[:10]:
        print(f"   {t}: {c}")
    
    # Format
    formatted = []
    for s in samples:
        # Get output
        output = s.get('output', '')
        if not output and s.get('expected'):
            expected = s['expected']
            if isinstance(expected, dict):
                parts = []
                if expected.get('approach'):
                    parts.append("الخطوات:\n" + "\n".join(f"- {x}" for x in expected['approach']))
                if expected.get('acceptance_checks'):
                    parts.append("\nمعايير القبول:\n" + "\n".join(f"✓ {x}" for x in expected['acceptance_checks']))
                output = "\n".join(parts)
            else:
                output = str(expected)
        
        if not output:
            output = "سأقوم بتحليل المشكلة وتقديم حل مناسب."
        
        text = PROMPT_TEMPLATE.format(
            task_type=s.get('task_type', s.get('category', 'general')),
            instruction=s.get('instruction', s.get('instruction_ar', '')),
            output=output[:1500]  # Limit output length
        )
        formatted.append({"text": text})
    
    return Dataset.from_list(formatted)


def main():
    print("\n" + "="*60)
    print("🚀 NOOGH Sovereign Training - Qwen 2.5 7B")
    print("="*60 + "\n")
    
    # GPU check
    if torch.cuda.is_available():
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"   Memory: {mem:.1f} GB")
        if mem < 20:
            print("⚠️ Low VRAM - using aggressive memory optimization")
    else:
        print("❌ No GPU! Training will be very slow.")
        return
    
    # Load dataset
    dataset = load_dataset()
    
    # Split
    split = dataset.train_test_split(test_size=0.05, seed=42)
    train_dataset = split['train']
    eval_dataset = split['test']
    
    print(f"\n📈 Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")
    
    # Load model
    print(f"\n📦 Loading: {MODEL_NAME}")
    print("   🎮 GPU ONLY mode")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )
    
    # LoRA
    print("🔧 Applying LoRA...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=32,  # Higher rank for 7B
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )
    
    # Training args
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        warmup_steps=100,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        save_strategy="steps",
        save_steps=200,
        eval_strategy="steps",
        eval_steps=200,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
        gradient_checkpointing=True,
    )
    
    # Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        args=training_args,
    )
    
    # Train
    print("\n" + "="*60)
    print("🏃 Starting Training...")
    print("="*60)
    trainer.train()
    
    # Save
    print(f"\n💾 Saving to {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    # GGUF
    print("📦 Converting to GGUF...")
    try:
        model.save_pretrained_gguf(
            str(OUTPUT_DIR / "gguf"), 
            tokenizer, 
            quantization_method="q4_k_m"
        )
        print(f"✅ GGUF saved to {OUTPUT_DIR}/gguf/")
    except Exception as e:
        print(f"⚠️ GGUF conversion failed: {e}")
    
    print("\n" + "="*60)
    print("✅ Training Complete!")
    print(f"   Model: {OUTPUT_DIR}")
    print(f"   Samples: {len(train_dataset)}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
