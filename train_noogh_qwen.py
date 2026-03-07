#!/usr/bin/env python3
"""
NOOGH Qwen LoRA Training Script
Training on noogh_training_data_final_v2.jsonl (4886 samples, 24 types)
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

DATASET_PATH = Path(__file__).parent / "training_data/noogh_training_data_final_v2.jsonl"
OUTPUT_DIR = Path(__file__).parent / "models/noogh_qwen_lora_v2"
MODEL_NAME = "unsloth/Qwen2.5-Coder-1.5B-Instruct-bnb-4bit"

MAX_SEQ_LENGTH = 1024
BATCH_SIZE = 2
GRADIENT_ACCUMULATION = 8
EPOCHS = 3
LEARNING_RATE = 2e-4

# ============================================================================
# PROMPT TEMPLATE
# ============================================================================

PROMPT_TEMPLATE = """<|im_start|>system
أنت NOOGH AI Agent - مساعد ذكي متخصص في نظام NOOGH Hybrid AI. 
أنت تحلل الطلبات، تختار الأدوات المناسبة، وتتخذ قرارات آمنة.
<|im_end|>
<|im_start|>user
[{type}] {instruction}

Input: {input}
<|im_end|>
<|im_start|>assistant
{output}

Reasoning: {reasoning}
Confidence: {confidence}
<|im_end|>"""


def load_dataset():
    """Load and format dataset."""
    print(f"📂 Loading dataset from {DATASET_PATH}")
    
    samples = []
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    samples.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    
    print(f"📊 Loaded {len(samples)} samples")
    
    # Format using prompt template
    formatted = []
    for s in samples:
        text = PROMPT_TEMPLATE.format(
            type=s.get('type', s.get('task_type', 'unknown')),
            instruction=s.get('instruction', ''),
            input=s.get('input', ''),
            output=str(s.get('output', s.get('response', ''))),
            reasoning=s.get('reasoning', 'Analysis based on system architecture.'),
            confidence=s.get('confidence', 0.85)
        )
        formatted.append({"text": text})
    
    return Dataset.from_list(formatted)


def main():
    print("\n" + "="*60)
    print("🚀 NOOGH Qwen LoRA Training")
    print("="*60 + "\n")
    
    # Check GPU
    if torch.cuda.is_available():
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        print("⚠️ No GPU detected! Training will be slow.")
    
    # Load dataset
    dataset = load_dataset()
    
    # Split train/eval
    split = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = split['train']
    eval_dataset = split['test']
    
    print(f"📈 Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")
    
    # Load model with Unsloth
    print(f"\n📦 Loading model: {MODEL_NAME}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )
    
    # Apply LoRA
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        warmup_steps=50,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch",
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
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
    print("\n🏃 Starting training...")
    trainer.train()
    
    # Save
    print(f"\n💾 Saving model to {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    # Save as GGUF for deployment
    gguf_path = OUTPUT_DIR / "noogh_qwen_q4_k_m.gguf"
    print(f"📦 Converting to GGUF: {gguf_path}")
    model.save_pretrained_gguf(str(gguf_path.parent), tokenizer, quantization_method="q4_k_m")
    
    print("\n" + "="*60)
    print("✅ Training Complete!")
    print(f"   Model: {OUTPUT_DIR}")
    print(f"   GGUF: {gguf_path.parent}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
