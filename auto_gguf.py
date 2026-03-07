#!/usr/bin/env python3
"""
NOOGH Auto-GGUF Pipeline
===========================
Automatically converts a trained LoRA adapter into a deployable GGUF model.

Pipeline:
1. Merge LoRA adapter with base model
2. Convert merged model to GGUF format
3. Quantize to Q4_K_M for optimal size/quality
4. Move to deployment directory

Requirements:
- llama.cpp (for conversion)
- Base model weights
- Trained LoRA adapter
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("auto_gguf")

# Paths
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
GGUF_OUTPUT_DIR = MODELS_DIR / "gguf"


def merge_lora(
    base_model: str,
    lora_adapter: str,
    output_dir: str = None,
) -> Dict[str, Any]:
    """
    Step 1: Merge LoRA adapter with base model.
    
    Uses PEFT's merge_and_unload.
    """
    if output_dir is None:
        output_dir = str(MODELS_DIR / "merged")
    
    logger.info(f"🔗 Merging LoRA: {lora_adapter} → {base_model}")
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        
        # Load base model
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype="auto",
            device_map="cpu",  # Merge on CPU to save VRAM
        )
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        
        # Load and merge LoRA
        model = PeftModel.from_pretrained(model, lora_adapter)
        model = model.merge_and_unload()
        
        # Save merged model
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        logger.info(f"✅ Merged model saved: {output_dir}")
        return {"success": True, "merged_dir": output_dir}
        
    except ImportError:
        # Fallback: use CLI
        logger.info("Using CLI merge (transformers not available)")
        cmd = [
            sys.executable, "-m", "peft.merge_and_unload",
            "--model_name_or_path", base_model,
            "--peft_model_path", lora_adapter,
            "--output_dir", output_dir,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            return {"success": True, "merged_dir": output_dir}
        return {"success": False, "error": result.stderr}
        
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        return {"success": False, "error": str(e)}


def convert_to_gguf(
    model_dir: str,
    output_file: str = None,
    quantize: str = "q4_k_m",
    llama_cpp_dir: str = None,
) -> Dict[str, Any]:
    """
    Step 2+3: Convert merged model to quantized GGUF.
    
    Uses llama.cpp's convert script.
    """
    if output_file is None:
        GGUF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = str(GGUF_OUTPUT_DIR / f"noogh-student-{quantize}.gguf")
    
    # Find llama.cpp
    if llama_cpp_dir is None:
        candidates = [
            Path.home() / "llama.cpp",
            Path("/opt/llama.cpp"),
            Path.home() / "projects" / "llama.cpp",
        ]
        for c in candidates:
            if (c / "convert_hf_to_gguf.py").exists():
                llama_cpp_dir = str(c)
                break
    
    if not llama_cpp_dir:
        return {"success": False, "error": "llama.cpp not found. Install it first."}
    
    convert_script = Path(llama_cpp_dir) / "convert_hf_to_gguf.py"
    quantize_bin = Path(llama_cpp_dir) / "build" / "bin" / "llama-quantize"
    
    if not convert_script.exists():
        return {"success": False, "error": f"Convert script not found: {convert_script}"}
    
    logger.info(f"📦 Converting to GGUF: {model_dir}")
    
    try:
        # Step 2: Convert to F16 GGUF
        f16_file = output_file.replace(f"-{quantize}", "-f16")
        cmd = [
            sys.executable, str(convert_script),
            model_dir,
            "--outfile", f16_file,
            "--outtype", "f16",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        if result.returncode != 0:
            return {"success": False, "error": f"Convert failed: {result.stderr[:200]}"}
        
        logger.info(f"✅ F16 GGUF: {f16_file}")
        
        # Step 3: Quantize
        if quantize_bin.exists():
            cmd = [str(quantize_bin), f16_file, output_file, quantize.upper()]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
            if result.returncode != 0:
                return {"success": False, "error": f"Quantize failed: {result.stderr[:200]}"}
            
            # Clean up F16 
            try:
                os.remove(f16_file)
            except Exception:
                pass
            
            logger.info(f"✅ Quantized GGUF: {output_file}")
        else:
            output_file = f16_file  # No quantization available
            logger.warning("Quantize binary not found — using F16")
        
        # Get file size
        size_mb = round(os.path.getsize(output_file) / (1024 * 1024), 1)
        
        return {
            "success": True,
            "gguf_file": output_file,
            "size_mb": size_mb,
            "quantization": quantize,
        }
        
    except Exception as e:
        logger.error(f"GGUF conversion failed: {e}")
        return {"success": False, "error": str(e)}


def full_pipeline(
    base_model: str,
    lora_adapter: str,
    quantize: str = "q4_k_m",
    llama_cpp_dir: str = None,
) -> Dict[str, Any]:
    """
    Run the complete LoRA → Merge → GGUF pipeline.
    """
    start = time.time()
    logger.info("🚀 Starting Auto-GGUF Pipeline")
    
    # Step 1: Merge
    merge_result = merge_lora(base_model, lora_adapter)
    if not merge_result.get("success"):
        return {"success": False, "stage": "merge", "error": merge_result.get("error")}
    
    # Step 2+3: Convert + Quantize
    gguf_result = convert_to_gguf(
        merge_result["merged_dir"],
        quantize=quantize,
        llama_cpp_dir=llama_cpp_dir,
    )
    if not gguf_result.get("success"):
        return {"success": False, "stage": "convert", "error": gguf_result.get("error")}
    
    elapsed = round(time.time() - start, 1)
    
    result = {
        "success": True,
        "gguf_file": gguf_result["gguf_file"],
        "size_mb": gguf_result["size_mb"],
        "quantization": quantize,
        "elapsed_seconds": elapsed,
    }
    
    # Save pipeline result
    result_file = GGUF_OUTPUT_DIR / "pipeline_result.json"
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"✅ Pipeline complete: {gguf_result['gguf_file']} ({gguf_result['size_mb']}MB) in {elapsed}s")
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NOOGH Auto-GGUF Pipeline")
    parser.add_argument("--base", required=True, help="Base model path")
    parser.add_argument("--lora", required=True, help="LoRA adapter path")
    parser.add_argument("--quantize", default="q4_k_m", help="Quantization type")
    parser.add_argument("--llama-cpp", default=None, help="llama.cpp directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    result = full_pipeline(args.base, args.lora, args.quantize, args.llama_cpp)
    print(json.dumps(result, indent=2))
