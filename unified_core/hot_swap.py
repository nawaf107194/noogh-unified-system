"""
NOOGH Student Hot-Swap
========================
Reload the Student model after training without restarting the service.

Flow:
1. Signal the Neural Engine to unload the current model
2. Wait for VRAM to clear
3. Load the new model (or updated GGUF)
4. Verify with a test prompt
5. Resume normal operation

Can be triggered:
- After distillation training completes
- After GGUF conversion
- Manually via API or CLI
"""

import asyncio
import logging
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("unified_core.hot_swap")


async def hot_swap_model(
    new_model_path: str = None,
    backend: str = None,
    test_prompt: str = "Explain what a Python decorator is in one sentence.",
) -> Dict[str, Any]:
    """
    Hot-swap the Student model without restarting the service.
    
    Args:
        new_model_path: Path to the new model (GGUF or HF format)
        backend: Backend to use ("gguf", "local-gpu", "auto")
        test_prompt: Prompt to verify the model works
    
    Returns:
        Dict with success status, timing, and test result
    """
    start = time.time()
    
    logger.info(f"🔄 Hot-swap starting: {new_model_path or 'default'}")
    
    try:
        from neural_engine.model_authority import get_model_authority, ModelState
        authority = get_model_authority()
    except ImportError:
        return {"success": False, "error": "ModelAuthority not available"}
    
    # Step 1: Unload current model
    logger.info("📤 Unloading current model...")
    try:
        authority.unload_model()
        await asyncio.sleep(2)  # Give CUDA time to reclaim memory
    except Exception as e:
        logger.warning(f"Unload warning (non-fatal): {e}")
    
    # Step 2: Determine new model
    if new_model_path is None:
        # Auto-detect: check for latest GGUF
        gguf_dir = Path(__file__).parent / "data" / "models" / "gguf"
        gguf_files = sorted(gguf_dir.glob("*.gguf")) if gguf_dir.exists() else []
        if gguf_files:
            new_model_path = str(gguf_files[-1])
            backend = backend or "gguf"
            logger.info(f"🔍 Auto-detected GGUF: {new_model_path}")
        else:
            new_model_path = os.getenv("NOOGH_MODEL", "")
            backend = backend or os.getenv("NOOGH_BACKEND", "auto")
            logger.info(f"🔍 Using default model: {new_model_path}")
    
    if backend is None:
        backend = "gguf" if new_model_path.endswith(".gguf") else "auto"
    
    # Step 3: Load new model
    logger.info(f"📥 Loading new model: {new_model_path} [backend={backend}]")
    try:
        model, tokenizer = authority.load_model(
            backend=backend,
            model_name=new_model_path,
        )
        load_time = round(time.time() - start, 1)
        logger.info(f"✅ Model loaded in {load_time}s")
    except Exception as e:
        logger.error(f"❌ Model load failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "elapsed_seconds": round(time.time() - start, 1),
        }
    
    # Step 4: Verify with test prompt
    test_result = None
    if test_prompt:
        logger.info("🧪 Running verification prompt...")
        try:
            from unified_core.neural_bridge import NeuralEngineClient
            client = NeuralEngineClient()
            
            messages = [
                {"role": "user", "content": test_prompt},
            ]
            result = await client.complete(messages, max_tokens=100)
            
            if result.get("success") and result.get("content"):
                test_result = result["content"][:200]
                logger.info(f"✅ Verification passed: {test_result[:80]}...")
            else:
                test_result = f"Warning: {result.get('error', 'no response')}"
                logger.warning(f"⚠️ Verification uncertain: {test_result}")
                
            await client.close()
        except Exception as e:
            test_result = f"Verification skipped: {e}"
            logger.warning(test_result)
    
    elapsed = round(time.time() - start, 1)
    
    result = {
        "success": True,
        "model_path": new_model_path,
        "backend": backend,
        "load_time_seconds": load_time,
        "total_elapsed_seconds": elapsed,
        "test_result": test_result,
        "authority_state": authority.state.value if hasattr(authority.state, 'value') else str(authority.state),
    }
    
    # Record in cognitive journal
    try:
        from unified_core.cognitive_journal import get_cognitive_journal
        journal = get_cognitive_journal()
        journal.record(
            entry_type="decision",
            content=f"Hot-swapped model to {Path(new_model_path).name}",
            context={"backend": backend, "load_time": load_time},
            confidence=0.9,
            tags=["hot_swap", "model_loading"],
        )
    except Exception:
        pass
    
    logger.info(f"🔄 Hot-swap complete: {elapsed}s total")
    return result


async def schedule_hot_swap_after_training(
    training_output_dir: str,
    auto_gguf: bool = True,
) -> Dict[str, Any]:
    """
    Called after training completes to automatically deploy the new model.
    
    1. Optionally converts to GGUF first
    2. Then hot-swaps
    """
    logger.info(f"🎓 Post-training hot-swap for: {training_output_dir}")
    
    model_path = training_output_dir
    backend = "auto"
    
    # Auto-GGUF if requested
    if auto_gguf:
        try:
            from auto_gguf import full_pipeline
            base_model = os.getenv("NOOGH_BASE_MODEL", "")
            if base_model:
                gguf_result = full_pipeline(base_model, training_output_dir)
                if gguf_result.get("success"):
                    model_path = gguf_result["gguf_file"]
                    backend = "gguf"
                    logger.info(f"📦 GGUF ready: {model_path}")
                else:
                    logger.warning(f"GGUF failed, using raw model: {gguf_result.get('error')}")
        except Exception as e:
            logger.warning(f"Auto-GGUF skipped: {e}")
    
    return await hot_swap_model(model_path, backend)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NOOGH Student Model Hot-Swap")
    parser.add_argument("--model", type=str, default=None, help="Path to new model")
    parser.add_argument("--backend", type=str, default=None, help="Backend (gguf/local-gpu/auto)")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    result = asyncio.run(hot_swap_model(args.model, args.backend))
    import json
    print(json.dumps(result, indent=2))
