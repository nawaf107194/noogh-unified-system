"""
Local LLM Brain Service v2.0 - Modular Dispatcher Architecture
Supports: Local HuggingFace, Neural Engine Proxy, and Fallback Logic.
"""

import logging
import os
import re
import asyncio
import httpx
from typing import Dict, Optional, List, Union

logger = logging.getLogger("local_brain")

class LocalBrainService:
    """
    A unified interface for LLM inference that dispatches requests 
    to the most appropriate backend (Local GPU, Remote Proxy, or Fallback).
    """

    def __init__(self, secrets: Dict[str, str] = None, model_name: str = None, backend: str = "auto"):
        self.secrets = secrets or {}
        self.model_name = model_name or self.secrets.get("LOCAL_MODEL_NAME", "noogh_gemma2_9b_v1")
        self.model = None
        self.tokenizer = None
        
        # Configuration for Neural Proxy
        try:
            from config.ports import PORTS
            default_proxy = f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}"
        except ImportError:
            default_proxy = "http://127.0.0.1:8002"
            
        self.proxy_url = os.getenv("NEURAL_ENGINE_URL", default_proxy)
        self.runpod_url = os.getenv("RUNPOD_GPU_URL") # Example: https://podid-8000.proxy.runpod.net
        self.proxy_token = os.getenv("NOOGH_INTERNAL_TOKEN")

        # --- Smart Backend Resolution ---
        self.backend = self._resolve_backend(backend)
        
        logger.info(f"🧠 LocalBrain v2.0 initialized. Selected Backend: [{self.backend.upper()}]")
        if self.runpod_url:
            logger.info(f"🚀 Remote GPU detected: {self.runpod_url}")

    def _resolve_backend(self, requested_backend: str) -> str:
        """Determines the active backend based on configuration and availability."""
        if requested_backend != "auto":
            logger.info(f"Using explicitly requested backend: {requested_backend}")
            return requested_backend

        # Auto-detection logic:
        # 1. Prefer Local GPU if model is available
        if self.model_name and self.model_name != "fallback":
            logger.info(f"Auto-detected Local backend for model: {self.model_name}")
            return "local"

        # 2. Prefer Proxy if configured and reachable
        logger.debug(f"Checking proxy at {self.proxy_url} (Token set: {bool(self.proxy_token)})")
        if self.proxy_token and self._check_proxy_availability():
            logger.info("Auto-detected Proxy backend.")
            return "proxy"
        
        # 3. RunPod Remote GPU (if configured)
        if self.runpod_url:
            logger.info("Auto-detected RunPod Remote GPU.")
            return "runpod"
            
        # 4. Default to fallback
        logger.warning("Falling back to Rule-based backend.")
        return "fallback"

    def _check_proxy_availability(self) -> bool:
        """Quick health check for Neural Engine Proxy."""
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(f"{self.proxy_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    async def _load_local_model(self):
        """Lazy loader for HuggingFace Transformers."""
        if self.model is not None:
            return

        logger.info(f"🔧 Lazy Loading Local Model: {self.model_name}...")
        try:
            # Heavy imports only when needed
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
            from peft import PeftModel, PeftConfig

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )

            # Check for Adapter (LoRA)
            # Normalize path for check
            model_path = self.model_name
            if not os.path.isabs(model_path):
                project_root = os.getenv("NOOGH_PROJECT_ROOT", os.getcwd())
                model_path = os.path.join(project_root, "models", self.model_name)

            if os.path.exists(os.path.join(model_path, "adapter_config.json")):
                logger.info(f"Detected LoRA adapter at {model_path}")
                config = PeftConfig.from_pretrained(model_path)
                base_model = AutoModelForCausalLM.from_pretrained(
                    config.base_model_name_or_path,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True,
                )
                self.model = PeftModel.from_pretrained(base_model, model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True,
                )
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            self._initialized = True
            logger.info("✅ Local Model Loaded Successfully.")

        except Exception as e:
            logger.error(f"❌ Failed to load local model: {e}")
            # Switch to fallback on failure
            self.backend = "fallback"

    # ---------------------------------------------------------
    # MAIN DISPATCHER
    # ---------------------------------------------------------
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Routes the generation request to the configured backend.
        """
        prompt_text = str(prompt)

        try:
            if self.backend == "runpod":
                return self._generate_via_runpod(prompt_text, **kwargs)

            if self.backend == "proxy":
                return self._generate_via_proxy(prompt_text)
            
            elif self.backend == "local":
                return self._generate_via_local_gpu(prompt_text, **kwargs)
            
            else:
                return self._generate_via_fallback(prompt_text)
                
        except Exception as e:
            logger.error(f"Generate Error ({self.backend}): {e}")
            return f"Error: Generation failed on {self.backend} backend."

    def _generate_via_runpod(self, prompt: str, **kwargs) -> str:
        """Handler for Remote RunPod GPU (OpenAI compatible)."""
        if not self.runpod_url:
            return self._generate_via_fallback(prompt)

        try:
            url = f"{self.runpod_url.rstrip('/')}/v1/chat/completions"
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    url,
                    json={
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_new_tokens", 1024)
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    answer = data["choices"][0]["message"]["content"]
                    return answer
                else:
                    logger.error(f"RunPod Error: {response.status_code} - {response.text}")
                    return self._generate_via_fallback(prompt)
        except Exception as e:
            logger.error(f"RunPod Connection Failed: {e}")
            return self._generate_via_fallback(prompt)

    # ---------------------------------------------------------
    # BACKEND HANDLERS
    # ---------------------------------------------------------
    
    def _generate_via_proxy(self, prompt: str) -> str:
        """Handler for Neural Engine HTTP Proxy."""
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.proxy_url}/api/v1/process",
                    headers={
                        "Content-Type": "application/json",
                        "X-Internal-Token": self.proxy_token
                    },
                    json={
                        "text": prompt,
                        "context": {},
                        "store_memory": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Neural Engine returns 'conclusion' in ReasoningResult
                    raw_answer = data.get("conclusion", "") or data.get("answer", "")
                    return self._format_as_react(raw_answer, prompt)
                else:
                    logger.warning(f"Proxy returned {response.status_code}. Falling back.")
                    return self._generate_via_fallback(prompt)
                    
        except Exception as e:
            logger.error(f"Proxy Connection Failed: {e}")
            return self._generate_via_fallback(prompt)

    def _generate_via_local_gpu(self, prompt: str, max_new_tokens: int = 1024, temperature: float = 0.5, **kwargs) -> str:
        """Handler for Local HuggingFace Model."""
        if not self.model:
            # Sync context bridge
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                loop.run_until_complete(self._load_local_model())
            except Exception:
                asyncio.run(self._load_local_model())

        if not self.model:
            return self._generate_via_fallback(prompt)

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.model.device.type == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            import torch
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    do_sample=temperature > 0,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Truncate prompt echo
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text

        except Exception as e:
            logger.error(f"Local Inference Error: {e}")
            return f"Error: Local inference failed - {str(e)}"

    def _generate_via_fallback(self, prompt: str) -> str:
        """Rule-based fallback for critical failures."""
        prompt_lower = prompt.lower()
        
        # Simple Math Handler (Internal Backup)
        if any(op in prompt_lower for op in ["calculate", "احسب", "+", "*", "-", "/"]):
            try:
                calc_match = re.search(r"(\d+\.?\d*)\s*([\+\-\*\/])\s*(\d+\.?\d*)", prompt)
                if calc_match:
                    a, op, b = float(calc_match.group(1)), calc_match.group(2), float(calc_match.group(3))
                    res = 0
                    if op == "+": res = a + b
                    elif op == "-": res = a - b
                    elif op == "*": res = a * b
                    elif op == "/": res = a / b if b != 0 else 0
                    return f"THINK: Local fallback math.\nACT: NONE\nANSWER: {res}"
            except Exception:
                pass
        
        return "THINK: System Offline.\nACT: NONE\nANSWER: عذراً، محرك نوق حالياً خارج الخدمة. يرجى التحقق من حالة النظام."

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------
    def _format_as_react(self, answer: str, prompt: str) -> str:
        """Formats the raw answer into ReAct style (THINK/ACT/ANSWER)."""
        # Support Sovereign Persona (v12.9.2)
        if "نوقة (تفكير):" in answer or "القرار (JSON):" in answer:
            # Already formatted with Sovereign markers, don't wrap.
            return answer
            
        if "THINK:" in answer and "ANSWER:" in answer:
            return answer
            
        return f"THINK: معالجة عبر البروكسي العصبي.\nACT: NONE\nANSWER: {answer}"

    async def hibernate(self):
        """Releases VRAM resources."""
        if self.model:
            import gc
            import torch
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            self._initialized = False
            logger.info("💤 LocalBrain hibernated.")

    async def wake_up(self):
        """Reloads resources."""
        if self.backend == "local":
            await self._load_local_model()
