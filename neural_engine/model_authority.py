"""
Single Model Authority - The ONLY allowed model loader in NOOGH system.
Enforces strict one-model-per-process policy and eliminates multi-loading.
"""

import logging
import os
import threading
from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple, Type, Union
# import torch  # Moved inside methods to prevent premature CUDA initialization

logger = logging.getLogger(__name__)


class ModelState(Enum):
    """Allowed states for the model authority."""
    UNLOADED = auto()
    LOADING = auto()
    LOADED = auto()
    FAILED = auto()
    DISABLED = auto()


class ModelAuthorityError(Exception):
    """Base exception for model authority errors."""
    pass


class ModelAlreadyLoadedError(ModelAuthorityError):
    """Raised when attempting to load a model while one is already loaded."""
    def __init__(self, loaded_model_name: str):
        self.loaded_model_name = loaded_model_name
        super().__init__(f"Model {loaded_model_name} already loaded. Must unload first.")


class ModelConflictError(ModelAuthorityError):
    """Raised when requesting a different model than the currently loaded one."""
    def __init__(self, current_model: str, requested_model: str):
        self.current_model = current_model
        self.requested_model = requested_model
        super().__init__(f"Cannot load {requested_model}. {current_model} is already loaded.")


class LoadFailedError(ModelAuthorityError):
    """Raised when model loading fails."""
    def __init__(self, model_name: str, error: str):
        self.model_name = model_name
        self.error = error
        super().__init__(f"Failed to load {model_name}: {error}")


class ModelAuthority:
    """
    Singleton authority that is the ONLY allowed model loader in the system.
    Enforces strict one-model policy and prevents multi-loading.
    """
    
    _instance: Optional['ModelAuthority'] = None
    _lock = threading.RLock()
    
    # Qwen 2.5 requires trust_remote_code for chat template support
    # Previously False for security (CVE-NE-07/17), enabled for verified Qwen model
    TRUST_REMOTE_CODE = True
    
    def __new__(cls) -> 'ModelAuthority':
        """Singleton pattern with thread safety."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the model authority."""
        if getattr(self, '_initialized', False):
            return
            
        self.state = ModelState.UNLOADED
        self.loaded_model: Optional[Any] = None
        self.loaded_tokenizer: Optional[Any] = None
        self.model_name: Optional[str] = None
        self.backend: Optional[str] = None
        self.error_info: Optional[str] = None
        
        # Configuration
        self.max_memory_gb = int(os.getenv("MAX_MODEL_MEMORY_GB", "10"))
        self.allow_reload = os.getenv("ALLOW_MODEL_RELOAD", "false").lower() == "true"
        
        # LoRA adapter configuration - Qwen 2.5 7B Research Agent (trained 2026-02-13)
        self.lora_adapter_path = os.getenv("NOOGH_LORA_ADAPTER", "/home/noogh/projects/noogh_unified_system/src/noogh_qwen7b_lora")
        self.use_lora = os.path.exists(self.lora_adapter_path) if self.lora_adapter_path else False
        
        self._initialized = True
        logger.info(f"✅ Model Authority initialized. Max memory: {self.max_memory_gb}GB")
    
    def get_state(self) -> ModelState:
        """Get current state of the model authority."""
        return self.state
    
    def get_loaded_model_info(self) -> Dict[str, Any]:
            """Get information about the currently loaded model."""
            if not hasattr(self, 'state') or not hasattr(self.state, 'name'):
                raise AttributeError("The 'state' attribute or its 'name' property is missing.")
            if not hasattr(self, 'model_name'):
                raise AttributeError("The 'model_name' attribute is missing.")
            if not hasattr(self, 'backend'):
                raise AttributeError("The 'backend' attribute is missing.")
            if not hasattr(self, '_get_memory_usage'):
                raise AttributeError("The '_get_memory_usage' method is missing.")
            if not callable(self._get_memory_usage):
                raise TypeError("'_get_memory_usage' is not a callable method.")
            if not hasattr(self, 'error_info'):
                raise AttributeError("The 'error_info' attribute is missing.")

            try:
                memory_usage = self._get_memory_usage()
            except Exception as e:
                logging.error(f"Failed to get memory usage: {e}")
                memory_usage = None

            return {
                "state": self.state.name,
                "model_name": self.model_name,
                "backend": self.backend,
                "memory_usage_gb": memory_usage,
                "error_info": self.error_info
            }
    
    def load_model(self, backend: str = "auto", model_name: str = None) -> Tuple[Any, Any]:
        """
        Load a model through the authority. This is the ONLY allowed load path.
        
        Args:
            backend: Backend type ("local-gpu", "ollama", "openai", "mock")
            model_name: Specific model name/identifier
            
        Returns:
            Tuple of (model, tokenizer) or raises ModelAuthorityError
            
        Raises:
            ModelAlreadyLoadedError: If a model is already loaded
            ModelConflictError: If requesting different model than loaded
            LoadFailedError: If loading fails
        """
        with self._lock:
            # Check if disabled
            if self.state == ModelState.DISABLED:
                raise ModelAuthorityError("Model loading is disabled by configuration")
            
            # Check if already loaded
            if self.state == ModelState.LOADED:
                if model_name and model_name != self.model_name:
                    raise ModelConflictError(self.model_name, model_name)
                if backend and backend != self.backend:
                    raise ModelConflictError(self.backend, backend)
                raise ModelAlreadyLoadedError(self.model_name or "unknown")
            
            # Check if loading in progress
            if self.state == ModelState.LOADING:
                raise ModelAuthorityError("Model loading already in progress")
            
            # Check if previous failure
            if self.state == ModelState.FAILED and not self.allow_reload:
                raise ModelAuthorityError(f"Previous load failed: {self.error_info}. Reset required.")
            
            # CRITICAL FIX: Pre-load VRAM check for local-gpu backend
            if backend == "local-gpu":
                available_vram = self._get_available_vram()
                logger.info(f"Pre-load VRAM check: {available_vram:.1f}GB available")
                
                if available_vram < 2.0:  # Need at least 2GB free for 4-bit quantized model
                    raise ModelAuthorityError(
                        f"Insufficient VRAM: {available_vram:.1f}GB available, need 2GB minimum for model loading"
                    )
                
                if available_vram < self.max_memory_gb:
                    logger.warning(
                        f"VRAM tight: {available_vram:.1f}GB available, "
                        f"max configured: {self.max_memory_gb}GB. Loading may fail."
                    )
            
            # Start loading
            self.state = ModelState.LOADING
            self.backend = backend # Update backend if it was changed by auto-fallback
            self.model_name = model_name
            self.error_info = None
            
            model, tokenizer = None, None
            load_attempts = []
            
            # Determine loading strategy based on backend
            if backend == "auto":
                backends_to_try = []
                if torch.cuda.is_available():
                    backends_to_try.append("local-gpu")
                backends_to_try.append("local-cpu")
                
                for current_backend in backends_to_try:
                    try:
                        logger.info(f"🧠 Model Authority: Attempting to load {current_backend} model '{model_name}' (auto-fallback)")
                        if current_backend == "local-gpu":
                            model, tokenizer = self._load_local_gpu_model(model_name)
                        elif current_backend == "gguf":
                            model, tokenizer = self._load_gguf_model(model_name)
                        elif current_backend == "local-cpu":
                            model, tokenizer = self._load_local_cpu_model(model_name)
                        self.backend = current_backend # Update the actual backend used
                        break # Success, exit loop
                    except Exception as e:
                        load_attempts.append(f"{current_backend} failed: {e}")
                        logger.warning(f"❌ Model Authority: {current_backend} load failed: {e}")
                
                if model is None: # All auto-fallback attempts failed
                    self.state = ModelState.FAILED
                    self.error_info = "; ".join(load_attempts)
                    logger.error(f"❌ Model Authority: All auto-fallback attempts failed for model '{model_name}': {self.error_info}")
                    raise LoadFailedError(model_name or "unknown", self.error_info)
            else: # Specific backend requested
                try:
                    logger.info(f"🧠 Model Authority: Loading {backend} model '{model_name}'")
                    
                    if backend == "local-gpu":
                        model, tokenizer = self._load_local_gpu_model(model_name)
                    elif backend == "gguf":
                        model, tokenizer = self._load_gguf_model(model_name)
                    elif backend == "local-cpu":
                        model, tokenizer = self._load_local_cpu_model(model_name)
                    elif backend == "ollama":
                        model, tokenizer = self._load_ollama_model()
                    elif backend == "openai":
                        model, tokenizer = self._load_openai_model()
                    else:
                        raise LoadFailedError(model_name or "unknown", f"Unsupported backend: {backend}")
                        
                except Exception as e:
                    # Failure
                    self.state = ModelState.FAILED
                    self.error_info = str(e)
                    logger.error(f"❌ Model Authority: Failed to load model: {e}")
                    raise LoadFailedError(model_name or "unknown", str(e))
            
            # If we reached here, a model was successfully loaded or an error was raised
            # Success
            self.loaded_model = model
            self.loaded_tokenizer = tokenizer
            self.state = ModelState.LOADED
            
            logger.info(f"✅ Model Authority: Successfully loaded {self.backend} model '{model_name}'")
            logger.info(f"🔧 Memory usage: {self._get_memory_usage():.1f}GB")
            
            return model, tokenizer
    
    async def load_model_async(self, backend: str = "auto", model_name: str = None) -> Tuple[Any, Any]:
        """Async wrapper for model loading to prevent blocking the event loop."""
        import asyncio
        return await asyncio.to_thread(self.load_model, backend, model_name)

    def unload_model(self) -> None:
        """Unload the current model and free memory."""
        with self._lock:
            if self.state != ModelState.LOADED:
                logger.warning("No model loaded to unload")
                return
            
            try:
                # Clear model references to free memory
                if hasattr(self.loaded_model, 'cpu'):
                    self.loaded_model.cpu()
                if hasattr(self.loaded_model, 'to'):
                    self.loaded_model.to('cpu')
                
                # Clear CUDA cache
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # Delete references
                del self.loaded_model
                del self.loaded_tokenizer
                self.loaded_model = None
                self.loaded_tokenizer = None
                self.model_name = None
                self.backend = None
                self.state = ModelState.UNLOADED
                
                logger.info("✅ Model Authority: Model unloaded and memory freed")
                
            except Exception as e:
                logger.error(f"❌ Model Authority: Failed to unload model: {e}")
                self.state = ModelState.FAILED
                self.error_info = f"Unload failed: {e}"
    
    def reset(self) -> None:
        """Reset the authority to UNLOADED state, clearing any failure state."""
        with self._lock:
            if self.state == ModelState.LOADED:
                self.unload_model()
            else:
                self.state = ModelState.UNLOADED
                self.error_info = None
                logger.info("✅ Model Authority: Reset to UNLOADED state")
    
    def disable(self) -> None:
        """Disable model loading entirely."""
        with self._lock:
            if self.state == ModelState.LOADED:
                self.unload_model()
            self.state = ModelState.DISABLED
            logger.warning("⚠️ Model Authority: Model loading disabled")
    
    def enable(self) -> None:
            """Re-enable model loading."""
            if not isinstance(self.state, ModelState):
                raise TypeError("State must be an instance of ModelState enum.")
        
            with self._lock:
                if self.state == ModelState.DISABLED:
                    self.state = ModelState.UNLOADED
                    logger.info("✅ Model Authority: Model loading enabled")
                else:
                    logger.warning("⚠️ Attempted to enable model loading, but state is not DISABLED.")
    
    def _patch_bitsandbytes(self):
        """
        CRITICAL MONKEY-PATCH: Bypasses the failing bitsandbytes Gaudi SW check.
        
        The bitsandbytes library attempts to run 'pip list | grep habana-torch-plugin'
        at the module level when imported. This fails in restricted environments.
        We monkey-patch subprocess.run to return a safe dummy result for this call.
        """
        import subprocess
        from unittest.mock import MagicMock
        
        original_run = subprocess.run
        
        def patched_run(*args, **kwargs):
            command = args[0] if args else kwargs.get("args", "")
            if isinstance(command, str) and "habana-torch-plugin" in command:
                logger.info("🛡️ Model Authority: Intercepted bitsandbytes Gaudi check. Bypassing...")
                return MagicMock(stdout="", returncode=1)
            return original_run(*args, **kwargs)
        
        subprocess.run = patched_run
        logger.info("✅ Model Authority: subprocess.run patched for bitsandbytes stability")

    def _load_local_gpu_model(self, model_name: str) -> Tuple[Any, Any]:
        """Load a local GPU model with strict memory controls + optional LoRA adapter."""
        import torch
        try:
            # Apply patch before any transformer/bitsandbytes imports
            self._patch_bitsandbytes()
            
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            from peft import PeftModel, PeftConfig
            
            logger.info(f"📦 Loading local GPU model: {model_name}")
            
            import os
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
            torch.cuda.empty_cache()
            
            # --- Detect LoRA Adapter ---
            # Check if model_name points to a local adapter directory
            adapter_path = None
            if os.path.isabs(model_name) and os.path.exists(os.path.join(model_name, "adapter_config.json")):
                adapter_path = model_name
            else:
                # Check relative to project models dir
                project_root = os.getenv("NOOGH_PROJECT_ROOT", os.getcwd())
                candidate = os.path.join(project_root, "models", model_name)
                if os.path.exists(os.path.join(candidate, "adapter_config.json")):
                    adapter_path = candidate
            
            # Also check the explicit NOOGH_LORA_ADAPTER env var
            if not adapter_path and self.use_lora:
                adapter_path = self.lora_adapter_path
            
            if adapter_path:
                # --- LoRA Adapter Mode: Load base model + adapter ---
                logger.info(f"🔧 Detected LoRA adapter at: {adapter_path}")
                peft_config = PeftConfig.from_pretrained(adapter_path)
                base_model_name = peft_config.base_model_name_or_path
                logger.info(f"📦 Base model from adapter config: {base_model_name}")
                
                # 4-bit quantization for efficient VRAM usage
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    llm_int8_enable_fp32_cpu_offload=True,  # Enable CPU offloading for layers that don't fit
                )
                
                import psutil
                cpu_ram_gb = int(psutil.virtual_memory().available / 1e9)
                # Hybrid: 4GiB GPU + rest on CPU for layer offloading (coexists with ollama)
                max_mem = {0: "4GiB", "cpu": f"{min(cpu_ram_gb, 20)}GiB"}
                logger.info(f"🧠 Memory map: GPU=4GiB, CPU={min(cpu_ram_gb, 20)}GiB (Hybrid: critical layers GPU, rest CPU)")
                
                # Load base model with quantization
                base_model = AutoModelForCausalLM.from_pretrained(
                    base_model_name,
                    quantization_config=bnb_config,
                    torch_dtype=torch.bfloat16,
                    attn_implementation="eager",
                    device_map="auto",
                    trust_remote_code=ModelAuthority.TRUST_REMOTE_CODE,
                    low_cpu_mem_usage=True,
                    max_memory=max_mem,
                )
                
                # CRITICAL FIX: ALWAYS use base model tokenizer to avoid vocab mismatch
                # The adapter tokenizer may have different vocab size → CUDA assert error
                tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=ModelAuthority.TRUST_REMOTE_CODE)
                
                # Ensure pad_token is set (Gemma doesn't have one by default)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                    tokenizer.pad_token_id = tokenizer.eos_token_id
                    logger.info("📝 Set pad_token = eos_token")
                
                # Apply LoRA adapter
                model = PeftModel.from_pretrained(base_model, adapter_path)
                model.eval()
                
                # Validate vocab size match
                model_vocab = base_model.config.vocab_size
                tok_vocab = len(tokenizer)
                if model_vocab != tok_vocab:
                    logger.warning(f"⚠️ Vocab mismatch: model={model_vocab}, tokenizer={tok_vocab}. Resizing embeddings...")
                    base_model.resize_token_embeddings(tok_vocab)
                else:
                    logger.info(f"✅ Vocab sizes match: {model_vocab}")
                
                logger.info(f"✅ LoRA adapter loaded successfully from {adapter_path}")
                
                return model, tokenizer
            else:
                # --- Standard Model Mode ---
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name, 
                    use_fast=False, 
                    trust_remote_code=ModelAuthority.TRUST_REMOTE_CODE
                )
                
                # MoE models: load in bfloat16 (naturally efficient, no quantization issues)
                logger.info(f"🧠 Loading MoE model in bfloat16 with auto device mapping")

                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.bfloat16,  # Use bfloat16 instead of quantization
                    device_map="auto",  # Auto distribution across GPU/CPU
                    trust_remote_code=ModelAuthority.TRUST_REMOTE_CODE,
                    low_cpu_mem_usage=True,
                )
                
                return model, tokenizer
            
        except Exception as e:
            raise LoadFailedError(model_name, f"Local GPU load failed: {e}")

    def _load_gguf_model(self, model_path: str) -> Tuple[Any, Any]:
        """Load a GGUF model using llama-cpp-python."""
        try:
            from llama_cpp import Llama
            
            logger.info(f"📦 Loading GGUF model: {model_path}")
            
            # Simplified loading for GGUF
            model = Llama(
                model_path=model_path,
                n_gpu_layers=int(os.environ.get("NOOGH_GGUF_LAYERS", "0")), # Configurable layers
                n_ctx=2048,      # Reduced context for VRAM safety
                verbose=False
            )
            
            # For GGUF, we treat the model instance as both model and tokenizer-like interface
            # as llama-cpp-python handles both.
            return model, model
            
        except Exception as e:
            raise LoadFailedError(model_path, f"GGUF load failed: {e}")

    def _load_local_cpu_model(self, model_name: str) -> Tuple[Any, Any]:
        """Load a local model onto CPU using 4-bit quantization (if possible)."""
        try:
            self._patch_bitsandbytes()
            
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            from peft import PeftModel
            
            logger.info(f"📦 Loading local CPU model: {model_name}")
            
            # FATAL-01 FIX: torch must be imported here (was missing)
            import torch
            
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                llm_int8_enable_fp32_cpu_offload=True,  # Enable CPU offloading for layers that don't fit
            )
            
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                use_fast=False,
                trust_remote_code=ModelAuthority.TRUST_REMOTE_CODE,
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="cpu",
                trust_remote_code=False,
                low_cpu_mem_usage=True,
                max_memory={"cpu": f"{self.max_memory_gb}GB"},
            )
            
            if self.use_lora:
                logger.info(f"🔧 Loading LoRA adapter from: {self.lora_adapter_path}")
                model = PeftModel.from_pretrained(model, self.lora_adapter_path)
                model.eval()
                logger.info("✅ LoRA adapter loaded successfully")
            
            return model, tokenizer
        except Exception as e:
            raise LoadFailedError(model_name, f"Local CPU load failed: {e}")
    
    def _load_ollama_model(self) -> Tuple[Any, Any]:
        """Load Ollama model."""
        try:
            from langchain_community.llms import Ollama
            model = Ollama(model="llama2")
            return model, None  # Ollama doesn't use separate tokenizer
        except Exception as e:
            raise LoadFailedError("ollama", f"Ollama load failed: {e}")
    
    def _load_openai_model(self) -> Tuple[Any, Any]:
        """Load OpenAI model."""
        try:
            from langchain_openai import ChatOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise LoadFailedError("openai", "OPENAI_API_KEY not set")
            model = ChatOpenAI(model="gpt-3.5-turbo", api_key=api_key, temperature=0.7)
            return model, None  # OpenAI doesn't use separate tokenizer
        except Exception as e:
            raise LoadFailedError("openai", f"OpenAI load failed: {e}")
    
    def _get_memory_usage(self) -> float:
        """Get current GPU memory usage in GB."""
        import torch
        if not torch.cuda.is_available():
            return 0.0
        
        try:
            memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            return round(memory_allocated, 1)
        except Exception:
            return 0.0
    
    def _get_available_vram(self) -> float:
        """
        Get available GPU memory in GB.
        
        CRITICAL FIX: Added to enable pre-load VRAM checks that prevent
        OOM crashes by refusing to load when insufficient memory is available.
        """
        import torch
        if not torch.cuda.is_available():
            return 0.0
        
        try:
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            
            # Available = total - max(allocated, reserved)
            # Use reserved as it's more conservative
            available = total - reserved
            
            return round(available, 1)
        except Exception as e:
            logger.warning(f"Could not determine available VRAM: {e}")
            return 0.0


# Global singleton access
def get_model_authority() -> ModelAuthority:
    """Get the global ModelAuthority instance."""
    return ModelAuthority()
