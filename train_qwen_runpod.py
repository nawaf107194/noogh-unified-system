#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║        NOOGH Research Agent — Qwen 2.5 7B Training           ║
║        Platform: RunPod (A100/H100/A6000)                    ║
║        Dataset:  Research Agent V1 (210 samples)             ║
║        Method:   QLoRA (4-bit) + SFT                         ║
╚══════════════════════════════════════════════════════════════╝

Usage on RunPod:
1. Start a GPU Pod (A100 80GB recommended, A6000 48GB works too)
2. Upload this script + NOOGH_RESEARCH_AGENT_V1.jsonl
3. pip install torch transformers datasets trl peft bitsandbytes accelerate
4. python train_qwen_runpod.py

Estimated time: ~15-25 min on A100 80GB
"""

import os
import json
import torch
import logging
from pathlib import Path
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG
# ============================================================================

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
OUTPUT_DIR = Path("noogh_qwen7b_research_agent")
LORA_OUTPUT = OUTPUT_DIR / "lora_adapter"

# Dataset — will search multiple locations
DATASET_CANDIDATES = [
    "NOOGH_RESEARCH_AGENT_V1.jsonl",
    "/workspace/NOOGH_RESEARCH_AGENT_V1.jsonl",
    "/root/NOOGH_RESEARCH_AGENT_V1.jsonl",
]

# Training params — conservative for small dataset
MAX_SEQ_LENGTH = 2048
BATCH_SIZE = 2              # Safe for most GPUs
GRADIENT_ACCUMULATION = 8   # Effective batch = 16
EPOCHS = 5                  # More epochs for small dataset
LEARNING_RATE = 1e-4        # Lower LR for stability
WARMUP_RATIO = 0.1          # More warmup for small data

# LoRA config — Qwen2.5 specific targets
LORA_R = 64                 # Higher rank for small dataset
LORA_ALPHA = 128
LORA_DROPOUT = 0.05
LORA_TARGETS = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

# ============================================================================
# DATA LOADING
# ============================================================================

def find_dataset():
    """Find the research agent dataset."""
    for path in DATASET_CANDIDATES:
        if Path(path).exists():
            return Path(path)
    # Also check current directory for any .jsonl files
    for f in Path(".").glob("*.jsonl"):
        if "RESEARCH" in f.name.upper() or "NOOGH" in f.name.upper():
            return f
    raise FileNotFoundError(
        "❌ Dataset not found!\n"
        "Upload NOOGH_RESEARCH_AGENT_V1.jsonl to this directory.\n"
        f"Searched: {DATASET_CANDIDATES}"
    )


def load_dataset(tokenizer):
    """Load and format dataset for Qwen 2.5 chat format."""
    from datasets import Dataset

    dataset_path = find_dataset()
    logger.info(f"📂 Loading: {dataset_path}")

    samples = []
    skipped = 0

    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            messages = data.get('messages', [])
            if len(messages) < 4:  # system + user + tool_call + answer minimum
                skipped += 1
                continue

            # Format using Qwen's chat template
            try:
                text = tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=False
                )
                samples.append({"text": text})
            except Exception as e:
                # Manual fallback — Qwen uses <|im_start|>/<|im_end|> format
                parts = []
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
                text = "\n".join(parts)
                samples.append({"text": text})

    logger.info(f"✅ Loaded {len(samples)} samples (skipped {skipped})")

    # Print category distribution
    categories = {}
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    cat = json.loads(line).get("category", "unknown")
                    categories[cat] = categories.get(cat, 0) + 1
                except:
                    pass
    logger.info("📁 Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        logger.info(f"   {cat}: {count}")

    return Dataset.from_list(samples)


# ============================================================================
# MODEL LOADING
# ============================================================================

def load_model():
    """Load Qwen 2.5 7B with QLoRA."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    logger.info(f"📦 Loading: {MODEL_NAME}")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        padding_side="right",
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 4-bit quantization
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    torch.cuda.empty_cache()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quant_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )

    # Prepare for training
    model = prepare_model_for_kbit_training(model)
    model.gradient_checkpointing_enable()

    # Apply LoRA
    logger.info(f"🔧 LoRA: r={LORA_R}, alpha={LORA_ALPHA}")
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
    logger.info(f"📊 Params: {trainable:,} trainable / {total:,} total ({100*trainable/total:.2f}%)")

    return model, tokenizer


# ============================================================================
# TRAINING
# ============================================================================

def train():
    """Main training loop."""
    from trl import SFTTrainer, SFTConfig

    print("\n" + "=" * 60)
    print("🚀 NOOGH Research Agent — Qwen 2.5 7B Training")
    print("=" * 60)

    if not torch.cuda.is_available():
        logger.error("❌ No GPU! RunPod GPU pod required.")
        return

    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
    logger.info(f"🎮 GPU: {gpu_name} ({gpu_mem:.1f} GB)")

    # Adjust batch size based on GPU
    global BATCH_SIZE
    if gpu_mem >= 70:      # A100 80GB / H100
        BATCH_SIZE = 4
        logger.info("⚡ A100/H100 detected — batch_size=4")
    elif gpu_mem >= 40:    # A6000 48GB
        BATCH_SIZE = 2
        logger.info("🔧 A6000 detected — batch_size=2")
    else:                  # Smaller GPU
        BATCH_SIZE = 1
        logger.info("⚠️ Small GPU — batch_size=1")

    # Load
    model, tokenizer = load_model()
    dataset = load_dataset(tokenizer)

    # Split 90/10 (small dataset needs bigger eval)
    split = dataset.train_test_split(test_size=0.1, seed=42)
    train_ds = split['train']
    eval_ds = split['test']

    logger.info(f"📈 Train: {len(train_ds)}, Eval: {len(eval_ds)}")

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
        bf16=True,
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=3,
        eval_strategy="epoch",
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_grad_norm=0.3,
        # SFT specific
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_text_field="text",
        packing=True,
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=training_args,
    )

    # Summary
    eff_batch = BATCH_SIZE * GRADIENT_ACCUMULATION
    total_steps = (len(train_ds) // eff_batch) * EPOCHS
    print(f"\n{'=' * 60}")
    print("🏃 Starting Training...")
    print(f"   Model:    {MODEL_NAME}")
    print(f"   Dataset:  {len(train_ds)} train / {len(eval_ds)} eval")
    print(f"   Epochs:   {EPOCHS}")
    print(f"   Batch:    {BATCH_SIZE} × {GRADIENT_ACCUMULATION} = {eff_batch}")
    print(f"   LR:       {LEARNING_RATE}")
    print(f"   LoRA:     r={LORA_R}, α={LORA_ALPHA}")
    print(f"   Seq Len:  {MAX_SEQ_LENGTH}")
    print(f"   Est Steps: ~{total_steps}")
    print(f"   GPU:      {gpu_name} ({gpu_mem:.0f} GB)")
    print("=" * 60 + "\n")

    # Train!
    result = trainer.train()

    # Save LoRA adapter
    logger.info(f"💾 Saving LoRA → {LORA_OUTPUT}")
    LORA_OUTPUT.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(LORA_OUTPUT))
    tokenizer.save_pretrained(str(LORA_OUTPUT))

    # Save stats
    stats = {
        "model": MODEL_NAME,
        "task": "research_agent",
        "dataset_samples": len(train_ds),
        "epochs": EPOCHS,
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "learning_rate": LEARNING_RATE,
        "max_seq_length": MAX_SEQ_LENGTH,
        "effective_batch_size": eff_batch,
        "train_loss": result.training_loss,
        "train_runtime_seconds": result.metrics.get('train_runtime', 0),
        "gpu": gpu_name,
    }
    with open(OUTPUT_DIR / "training_stats.json", 'w') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("✅ Training Complete!")
    print(f"   📁 LoRA Adapter: {LORA_OUTPUT}")
    print(f"   📊 Loss: {result.training_loss:.4f}")
    print(f"   ⏱️  Time: {result.metrics.get('train_runtime', 0)/60:.1f} min")
    print("=" * 60)
    print("\n📥 To download adapter to your local machine:")
    print(f"   runpodctl receive {LORA_OUTPUT}")
    print("   OR")
    print(f"   scp -r root@<POD_IP>:/workspace/{LORA_OUTPUT}/ ./")
    print()

    return result


if __name__ == "__main__":
    train()
