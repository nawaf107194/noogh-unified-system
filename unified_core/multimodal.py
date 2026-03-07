"""
Multimodal Generation Interfaces
Text, Image, Audio, and Video generation wrappers
"""
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import torch

logger = logging.getLogger("unified_core.neural.multimodal")


class GenerationType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass
class GenerationRequest:
    """Unified generation request."""
    prompt: str
    generation_type: GenerationType
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    seed: Optional[int] = None
    
    # Image specific
    width: int = 512
    height: int = 512
    num_inference_steps: int = 30
    guidance_scale: float = 7.5
    
    # Audio specific
    duration_seconds: float = 5.0
    sample_rate: int = 22050
    
    # Video specific
    fps: int = 8
    num_frames: int = 16
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Unified generation result."""
    success: bool
    generation_type: GenerationType
    content: Any = None  # str, bytes, or path
    content_path: Optional[str] = None
    tokens_generated: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class GeneratorInterface(ABC):
    """Abstract interface for all generators."""
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        pass


# ============================================
# TEXT GENERATION (LLM)
# ============================================

class TextGenerator(GeneratorInterface):
    """
    LLM text generation wrapper.
    Supports local models (Mistral, Llama) and API-based (OpenAI, Claude).
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.1",
        device: str = "auto",
        load_in_8bit: bool = False,
        max_memory: Optional[Dict[int, str]] = None
    ):
        self.model_path = model_path
        self.model_name = model_name
        self.device = device
        self.load_in_8bit = load_in_8bit
        self.max_memory = max_memory
        
        self._model = None
        self._tokenizer = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Load the model."""
        if self._initialized:
            return True
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            model_source = self.model_path or self.model_name
            
            self._tokenizer = AutoTokenizer.from_pretrained(model_source)
            
            load_kwargs = {}
            if self.device == "auto":
                load_kwargs["device_map"] = "auto"
            if self.load_in_8bit:
                load_kwargs["load_in_8bit"] = True
            if self.max_memory:
                load_kwargs["max_memory"] = self.max_memory
            
            self._model = AutoModelForCausalLM.from_pretrained(
                model_source,
                torch_dtype=torch.float16,
                **load_kwargs
            )
            
            self._initialized = True
            logger.info(f"TextGenerator initialized: {model_source}")
            return True
            
        except Exception as e:
            logger.error(f"TextGenerator init failed: {e}")
            return False
    
    async def is_available(self) -> bool:
        return self._initialized
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        import time
        start = time.perf_counter()
        
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized:
            return GenerationResult(
                success=False,
                generation_type=GenerationType.TEXT,
                error="Model not initialized"
            )
        
        try:
            inputs = self._tokenizer(
                request.prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            ).to(self._model.device)
            
            if request.seed is not None:
                torch.manual_seed(request.seed)
            
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    do_sample=request.temperature > 0,
                    pad_token_id=self._tokenizer.eos_token_id
                )
            
            generated_text = self._tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )
            
            return GenerationResult(
                success=True,
                generation_type=GenerationType.TEXT,
                content=generated_text,
                tokens_generated=len(outputs[0]) - inputs.input_ids.shape[1],
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return GenerationResult(
                success=False,
                generation_type=GenerationType.TEXT,
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )


# ============================================
# IMAGE GENERATION (Stable Diffusion / Flux)
# ============================================

class ImageGenerator(GeneratorInterface):
    """
    Image generation using Stable Diffusion or Flux.
    """
    
    def __init__(
        self,
        model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
        device: str = "cuda",
        use_refiner: bool = False,
        safety_checker: bool = True
    ):
        self.model_id = model_id
        self.device = device
        self.use_refiner = use_refiner
        self.safety_checker = safety_checker
        
        self._pipeline = None
        self._refiner = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        if self._initialized:
            return True
        
        try:
            from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline
            
            self._pipeline = StableDiffusionXLPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True
            ).to(self.device)
            
            if not self.safety_checker:
                self._pipeline.safety_checker = None
            
            # Enable memory optimizations
            self._pipeline.enable_model_cpu_offload()
            
            self._initialized = True
            logger.info(f"ImageGenerator initialized: {self.model_id}")
            return True
            
        except Exception as e:
            logger.error(f"ImageGenerator init failed: {e}")
            return False
    
    async def is_available(self) -> bool:
        return self._initialized
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        import time
        import io
        start = time.perf_counter()
        
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized:
            return GenerationResult(
                success=False,
                generation_type=GenerationType.IMAGE,
                error="Pipeline not initialized"
            )
        
        try:
            generator = None
            if request.seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(request.seed)
            
            image = self._pipeline(
                prompt=request.prompt,
                width=request.width,
                height=request.height,
                num_inference_steps=request.num_inference_steps,
                guidance_scale=request.guidance_scale,
                generator=generator
            ).images[0]
            
            # Convert to bytes
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
            
            return GenerationResult(
                success=True,
                generation_type=GenerationType.IMAGE,
                content=image_bytes,
                execution_time_ms=(time.perf_counter() - start) * 1000,
                metadata={
                    "width": request.width,
                    "height": request.height,
                    "steps": request.num_inference_steps
                }
            )
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return GenerationResult(
                success=False,
                generation_type=GenerationType.IMAGE,
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )


# ============================================
# AUDIO GENERATION (TTS / Music)
# ============================================

class AudioGenerator(GeneratorInterface):
    """
    Audio generation using TTS or music models.
    """
    
    def __init__(
        self,
        tts_model: str = "tts_models/en/ljspeech/tacotron2-DDC",
        device: str = "cuda"
    ):
        self.tts_model = tts_model
        self.device = device
        
        self._tts = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        if self._initialized:
            return True
        
        try:
            from TTS.api import TTS
            
            self._tts = TTS(model_name=self.tts_model, progress_bar=False, gpu=self.device == "cuda")
            self._initialized = True
            logger.info(f"AudioGenerator initialized: {self.tts_model}")
            return True
            
        except Exception as e:
            logger.error(f"AudioGenerator init failed: {e}")
            return False
    
    async def is_available(self) -> bool:
        return self._initialized
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        import time
        import tempfile
        start = time.perf_counter()
        
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized:
            return GenerationResult(
                success=False,
                generation_type=GenerationType.AUDIO,
                error="TTS not initialized"
            )
        
        try:
            # Generate to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                output_path = f.name
            
            self._tts.tts_to_file(
                text=request.prompt,
                file_path=output_path
            )
            
            # Read audio bytes
            with open(output_path, "rb") as f:
                audio_bytes = f.read()
            
            return GenerationResult(
                success=True,
                generation_type=GenerationType.AUDIO,
                content=audio_bytes,
                content_path=output_path,
                execution_time_ms=(time.perf_counter() - start) * 1000,
                metadata={"sample_rate": request.sample_rate}
            )
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return GenerationResult(
                success=False,
                generation_type=GenerationType.AUDIO,
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )


# ============================================
# VIDEO GENERATION
# ============================================

class VideoGenerator(GeneratorInterface):
    """
    Video generation using text-to-video models.
    """
    
    def __init__(
        self,
        model_id: str = "damo-vilab/text-to-video-ms-1.7b",
        device: str = "cuda"
    ):
        self.model_id = model_id
        self.device = device
        
        self._pipeline = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        if self._initialized:
            return True
        
        try:
            from diffusers import DiffusionPipeline
            
            self._pipeline = DiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16,
                variant="fp16"
            ).to(self.device)
            
            self._pipeline.enable_model_cpu_offload()
            
            self._initialized = True
            logger.info(f"VideoGenerator initialized: {self.model_id}")
            return True
            
        except Exception as e:
            logger.error(f"VideoGenerator init failed: {e}")
            return False
    
    async def is_available(self) -> bool:
        return self._initialized
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        import time
        start = time.perf_counter()
        
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized:
            return GenerationResult(
                success=False,
                generation_type=GenerationType.VIDEO,
                error="Pipeline not initialized"
            )
        
        try:
            generator = None
            if request.seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(request.seed)
            
            video_frames = self._pipeline(
                prompt=request.prompt,
                num_frames=request.num_frames,
                num_inference_steps=request.num_inference_steps,
                generator=generator
            ).frames
            
            # Export to file
            from diffusers.utils import export_to_video
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                output_path = f.name
            
            export_to_video(video_frames, output_path, fps=request.fps)
            
            with open(output_path, "rb") as f:
                video_bytes = f.read()
            
            return GenerationResult(
                success=True,
                generation_type=GenerationType.VIDEO,
                content=video_bytes,
                content_path=output_path,
                execution_time_ms=(time.perf_counter() - start) * 1000,
                metadata={
                    "fps": request.fps,
                    "num_frames": request.num_frames
                }
            )
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return GenerationResult(
                success=False,
                generation_type=GenerationType.VIDEO,
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )


# ============================================
# UNIFIED MULTIMODAL HUB
# ============================================

class MultimodalHub:
    """
    Central hub for all generation capabilities.
    Routes requests to appropriate generators.
    """
    
    def __init__(self):
        self.generators: Dict[GenerationType, GeneratorInterface] = {}
        self._initialized = False
    
    def register_generator(self, gen_type: GenerationType, generator: GeneratorInterface):
        """Register a generator for a modality."""
        self.generators[gen_type] = generator
        logger.info(f"Registered generator for {gen_type.value}")
    
    async def initialize_all(self) -> Dict[GenerationType, bool]:
        """Initialize all registered generators."""
        results = {}
        for gen_type, generator in self.generators.items():
            results[gen_type] = await generator.is_available() or await self._init_generator(generator)
        self._initialized = True
        return results
    
    async def _init_generator(self, generator: GeneratorInterface) -> bool:
        if hasattr(generator, 'initialize'):
            return await generator.initialize()
        return False
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content based on request type."""
        generator = self.generators.get(request.generation_type)
        
        if not generator:
            return GenerationResult(
                success=False,
                generation_type=request.generation_type,
                error=f"No generator registered for {request.generation_type.value}"
            )
        
        if not await generator.is_available():
            return GenerationResult(
                success=False,
                generation_type=request.generation_type,
                error=f"Generator for {request.generation_type.value} is not available"
            )
        
        return await generator.generate(request)
    
    def get_available_modalities(self) -> List[GenerationType]:
        """Get list of available generation types."""
        available = []
        for gen_type, gen in self.generators.items():
            # Check if generator is initialized
            if gen._initialized if hasattr(gen, '_initialized') else False:
                available.append(gen_type)
        return available

