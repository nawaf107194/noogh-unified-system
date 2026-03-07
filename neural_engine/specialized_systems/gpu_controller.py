"""
GPU Resource Controller
Manages GPU memory allocation between different AI models:
- LLM (Mistral-7B) for chat
- Stable Diffusion for images  
- Stable Video Diffusion for video
- Bark for audio

Enables seamless switching between modes by unloading/reloading models.
"""
import logging
import asyncio
from typing import Optional, Dict, Any, Literal
from enum import Enum
from datetime import datetime

logger = logging.getLogger("gpu_controller")


class GPUMode(Enum):
    """Current GPU allocation mode."""
    IDLE = "idle"           # No models loaded
    LLM = "llm"             # Mistral-7B for chat
    IMAGE = "image"         # Stable Diffusion
    VIDEO = "video"         # Stable Video Diffusion  
    AUDIO = "audio"         # Bark TTS (runs on CPU)
    MIXED = "mixed"         # LLM + lightweight models


class GPUController:
    """
    GPU Resource Controller for managing model switching.
    
    RTX 5070 has 12GB VRAM:
    - Mistral-7B (4-bit): ~4-8GB
    - Stable Diffusion: ~4GB
    - Stable Video Diffusion: ~8GB
    - Bark TTS: CPU (no GPU needed)
    
    Cannot run LLM + SVD simultaneously.
    """
    
    def __init__(self):
        self.current_mode = GPUMode.IDLE
        self._llm_loaded = False
        self._image_loaded = False
        self._video_loaded = False
        self._mode_lock = asyncio.Lock()
        self._switch_in_progress = False
        self._last_switch = None
        logger.info("GPUController initialized")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current GPU status."""
        try:
            import torch
            
            if torch.cuda.is_available():
                total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                allocated = torch.cuda.memory_allocated(0) / (1024**3)
                reserved = torch.cuda.memory_reserved(0) / (1024**3)
                free = total - reserved
            else:
                total = allocated = reserved = free = 0
            
            return {
                "mode": self.current_mode.value,
                "gpu": {
                    "total_gb": round(total, 2),
                    "allocated_gb": round(allocated, 2),
                    "reserved_gb": round(reserved, 2),
                    "free_gb": round(free, 2)
                },
                "models": {
                    "llm_loaded": self._llm_loaded,
                    "image_loaded": self._image_loaded,
                    "video_loaded": self._video_loaded
                },
                "switch_in_progress": self._switch_in_progress,
                "last_switch": self._last_switch.isoformat() if self._last_switch else None
            }
        except Exception as e:
            logger.error(f"Failed to get GPU status: {e}")
            return {"error": str(e)}
    
    async def switch_to_mode(self, target_mode: GPUMode) -> Dict[str, Any]:
        """
        Switch GPU to target mode.
        
        This will:
        1. Unload conflicting models
        2. Free GPU memory
        3. Load required models
        
        Returns status dict with success/error info.
        """
        async with self._mode_lock:
            if self._switch_in_progress:
                return {"status": "busy", "message": "Mode switch already in progress"}
            
            self._switch_in_progress = True
            
        try:
            logger.info(f"Switching GPU mode: {self.current_mode.value} -> {target_mode.value}")
            
            # Unload conflicting models based on target
            if target_mode == GPUMode.VIDEO:
                # Video needs most memory - unload everything
                await self._unload_llm()
                await self._unload_image()
                await self._free_gpu_memory()
                await self._load_video()
                
            elif target_mode == GPUMode.LLM:
                # LLM mode - unload heavy models
                await self._unload_video()
                await self._free_gpu_memory()
                await self._load_llm()
                
            elif target_mode == GPUMode.IMAGE:
                # Image mode - can coexist with LLM on 12GB
                await self._unload_video()
                await self._free_gpu_memory()
                # Don't unload LLM - SD can work with remaining memory
                
            elif target_mode == GPUMode.IDLE:
                # Unload everything
                await self._unload_llm()
                await self._unload_image()
                await self._unload_video()
                await self._free_gpu_memory()
            
            self.current_mode = target_mode
            self._last_switch = datetime.now()
            
            status = await self.get_status()
            status["status"] = "success"
            status["message"] = f"Switched to {target_mode.value} mode"
            
            logger.info(f"GPU mode switch complete: {target_mode.value}")
            return status
            
        except Exception as e:
            logger.error(f"Mode switch failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            self._switch_in_progress = False
    
    async def _unload_llm(self):
        """Unload the LLM model."""
        if not self._llm_loaded:
            return
            
        try:
            # Import and unload ReasoningEngine
            from neural_engine.api.routes import _components
            if _components and hasattr(_components.get('reasoning'), 'unload'):
                _components['reasoning'].unload()
            
            self._llm_loaded = False
            logger.info("LLM unloaded")
        except Exception as e:
            logger.warning(f"Failed to unload LLM: {e}")
    
    async def _load_llm(self):
        """Load the LLM model."""
        if self._llm_loaded:
            return
            
        try:
            # Trigger LLM reload by reinitializing ReasoningEngine
            from neural_engine.reasoning_engine import ReasoningEngine
            # This will be lazy-loaded on next request
            self._llm_loaded = True
            logger.info("LLM marked for reload on next request")
        except Exception as e:
            logger.warning(f"Failed to prepare LLM reload: {e}")
    
    async def _unload_image(self):
        """Unload image generation model."""
        if not self._image_loaded:
            return
            
        try:
            from neural_engine.specialized_systems.image_generator import get_image_generator
            get_image_generator().unload()
            self._image_loaded = False
            logger.info("Image generator unloaded")
        except Exception as e:
            logger.warning(f"Failed to unload image generator: {e}")
    
    async def _unload_video(self):
        """Unload video generation model."""
        if not self._video_loaded:
            return
            
        try:
            from neural_engine.specialized_systems.video_generator import get_video_generator
            get_video_generator().unload()
            self._video_loaded = False
            logger.info("Video generator unloaded")
        except Exception as e:
            logger.warning(f"Failed to unload video generator: {e}")
    
    async def _load_video(self):
        """Prepare video generator for loading."""
        self._video_loaded = True
        logger.info("Video generator marked for loading")
    
    async def _free_gpu_memory(self):
        """Free all GPU memory caches."""
        try:
            import torch
            import gc
            
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            logger.info("GPU memory cache cleared")
        except Exception as e:
            logger.warning(f"Failed to free GPU memory: {e}")
    
    async def request_video_generation(
        self,
        input_image_path: str,
        num_frames: int = 14,
        fps: int = 7,
        motion_bucket_id: int = 127,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        High-level API for video generation with automatic mode switching.
        
        1. Saves current mode
        2. Switches to VIDEO mode
        3. Generates video
        4. Restores previous mode
        
        Returns video generation result.
        """
        previous_mode = self.current_mode
        
        try:
            # Step 1: Switch to VIDEO mode
            logger.info("Switching to VIDEO mode for generation...")
            switch_result = await self.switch_to_mode(GPUMode.VIDEO)
            
            if switch_result.get("status") != "success":
                return {"status": "error", "message": f"Failed to switch mode: {switch_result}"}
            
            # Step 2: Generate video
            logger.info("Starting video generation...")
            from neural_engine.specialized_systems.video_generator import get_video_generator
            
            generator = get_video_generator()
            result = await generator.animate_image(
                input_image_path=input_image_path,
                num_frames=num_frames,
                fps=fps,
                motion_bucket_id=motion_bucket_id,
                seed=seed
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            # Step 3: Restore previous mode
            logger.info(f"Restoring previous mode: {previous_mode.value}")
            await self.switch_to_mode(previous_mode)


# Global singleton
_gpu_controller: Optional[GPUController] = None


def get_gpu_controller() -> GPUController:
    """Get or create global GPUController instance."""
    global _gpu_controller
    if _gpu_controller is None:
        _gpu_controller = GPUController()
    return _gpu_controller
