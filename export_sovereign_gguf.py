from unsloth import FastLanguageModel
import torch
from pathlib import Path
import os

# CONFIG
LORA_PATH = Path("./models/noogh_sovereign_7b_v1")
GGUF_DIR = LORA_PATH / "gguf_final"

def main():
    print(f"🚀 Loading model and adapters from {LORA_PATH}...")
    
    # Load model and tokenizer
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = str(LORA_PATH),
        max_seq_length = 1024,
        dtype = None,
        load_in_4bit = True,
    )
    
    print("📦 Exporting to GGUF (q8_0)...")
    # This might fail if llama.cpp is not ready, but we'll try
    try:
        model.save_pretrained_gguf(
            str(GGUF_DIR),
            tokenizer,
            quantization_method = "q8_0",
        )
        print(f"✅ Export successful! Check {GGUF_DIR}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
        print("Attempting to save as 16-bit safetensors first...")
        model.save_pretrained_merged(str(GGUF_DIR / "hf_16bit"), tokenizer, save_method = "merged_16bit")

if __name__ == "__main__":
    main()
