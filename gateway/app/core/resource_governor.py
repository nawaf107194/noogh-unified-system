import gc
import logging
from enum import Enum
from typing import Any, Dict

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger("resource_governor")


class ModelPriority(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class GPUMemoryManager:
    """
    Intelligent GPU Memory Management for NOOGH.
    Tracks VRAM usage and dynamically unloads models based on priority.
    """

    def __init__(self, total_vram_gb: float = 12.0, safety_margin_gb: float = 1.0):
        self.total_vram = total_vram_gb * 1024**3  # bytes
        self.safety_margin = safety_margin_gb * 1024**3  # bytes
        self.loaded_models: Dict[str, Dict[str, Any]] = {}  # name -> {model, priority, size_estimate}

        if TORCH_AVAILABLE and torch.cuda.is_available():
            self.device_type = "cuda"
            logger.info(f"GPUMemoryManager initialized on {torch.cuda.get_device_name(0)} ({total_vram_gb}GB)")
        else:
            self.device_type = "cpu"
            logger.warning("CUDA/Torch not available. GPUMemoryManager will track RAM instead.")

    def get_free_vram(self) -> int:
            """Get currently free VRAM on the device."""
            from logging import getLogger

            logger = getLogger(__name__)

            if not isinstance(self.device_type, str):
                raise TypeError("device_type must be a string")

            if self.device_type == "cuda" and TORCH_AVAILABLE:
                try:
                    # Clear cache to get accurate reading
                    torch.cuda.empty_cache()
                    free, total = torch.cuda.mem_get_info()
                    logger.debug(f"Free VRAM: {free}, Total VRAM: {total}")
                    return free
                except Exception as e:
                    logger.error(f"Error retrieving VRAM info: {e}")
                    return 0
            else:
                logger.warning("Device type is not 'cuda' or PyTorch is not available")
                return 0  # Fallback for CPU

    async def ensure_vram(self, required_bytes: int, priority: ModelPriority):
        """
        Ensure enough VRAM is available by unloading lower priority models.
        """
        free_now = self.get_free_vram()
        target_free = required_bytes + self.safety_margin

        if free_now >= target_free:
            return True

        logger.info(f"Insufficient VRAM. Free: {free_now/1e9:.2f}GB, Required: {required_bytes/1e9:.2f}GB")

        # Sort loaded models by priority (ascending) and then by size (descending)
        to_unload = sorted(
            self.loaded_models.items(), key=lambda x: (x[1]["priority"].value, -x[1].get("size_estimate", 0))
        )

        for name, info in to_unload:
            if info["priority"].value < priority.value:
                logger.info(f"Unloading model '{name}' (Priority: {info['priority'].name}) to free VRAM")
                await self.unload_model(name)

                free_now = self.get_free_vram()
                if free_now >= target_free:
                    return True
            else:
                break  # Cannot unload models with equal or higher priority

        return self.get_free_vram() >= target_free

    async def register_model(self, name: str, model: Any, priority: ModelPriority, size_estimate_gb: float = 2.0):
        """Register a newly loaded model."""
        size_bytes = int(size_estimate_gb * 1024**3)
        self.loaded_models[name] = {
            "model": model,
            "priority": priority,
            "size_estimate": size_bytes,
            "loaded_at": torch.cuda.utilization() if (TORCH_AVAILABLE and self.device_type == "cuda") else 0,
        }
        logger.info(f"Model '{name}' registered with priority {priority.name}")

    async def unload_model(self, name: str):
        """Unload a model and free its memory."""
        if name in self.loaded_models:
            info = self.loaded_models.pop(name)
            info["model"]

            # Delete model and clear cache
            del model
            gc.collect()
            if self.device_type == "cuda" and TORCH_AVAILABLE:
                torch.cuda.empty_cache()

            logger.info(f"Successfully unloaded model '{name}'")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get current memory statistics."""
        free = self.get_free_vram()
        return {
            "device": self.device_type,
            "total_vram_gb": self.total_vram / 1e9,
            "free_vram_gb": free / 1e9,
            "loaded_models": [
                {"name": name, "priority": info["priority"].name, "size_est_gb": info["size_estimate"] / 1e9}
                for name, info in self.loaded_models.items()
            ],
        }


# Global Instance
gpu_manager = GPUMemoryManager()
