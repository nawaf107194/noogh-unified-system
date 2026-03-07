"""
Video Generator - Image Animation and Video Synthesis
Provides image-to-video, text-to-video, and animation capabilities
"""
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

# Output directory for generated videos
OUTPUT_DIR = Path(os.getenv("NOOGH_DATA_DIR", "./data")) / "generated" / "videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class VideoGenerator:
    """
    AI-powered video generation using Stable Video Diffusion.
    Supports image-to-video animation and text-to-video synthesis.
    """
    
    def __init__(self, model_id: str = "stabilityai/stable-video-diffusion-img2vid-xt"):
        """
        Initialize the video generator.
        
        Args:
            model_id: HuggingFace model ID for video generation
        """
        self.model_id = model_id
        self.pipe = None
        self.device = "cuda"
        self._initialized = False
        logger.info(f"VideoGenerator initialized with model: {model_id}")
    
    async def initialize(self):
        """Lazy load the video generation pipeline."""
        if self._initialized:
            return
        
        try:
            import torch
            from diffusers import StableVideoDiffusionPipeline
            from diffusers.utils import load_image, export_to_video
            
            logger.info(f"Loading video generation model: {self.model_id}")
            
            # Load with optimizations for low VRAM
            self.pipe = StableVideoDiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16,
                variant="fp16"
            )
            
            # Use CPU offload for low VRAM (don't call .to(device) with cpu_offload!)
            self.pipe.enable_sequential_cpu_offload()
            
            # Enable memory efficient attention
            self.pipe.enable_attention_slicing()
            
            self._initialized = True
            logger.info("✅ Video generation model loaded with CPU offload")
            
        except ImportError as e:
            logger.error(f"Missing dependency for video generation: {e}")
            logger.error("Install with: pip install diffusers[torch] transformers accelerate")
            raise RuntimeError(f"Video generation not available: {e}")
        except Exception as e:
            logger.error(f"Failed to load video model: {e}")
            raise
    
    async def animate_image(
        self,
        input_image_path: str,
        num_frames: int = 25,
        fps: int = 7,
        motion_bucket_id: int = 127,
        noise_aug_strength: float = 0.02,
        decode_chunk_size: int = 8,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Animate a static image into a video.
        
        Args:
            input_image_path: Path to the input image
            num_frames: Number of frames to generate (14-25)
            fps: Frames per second for output video
            motion_bucket_id: Motion intensity (1-255, higher = more motion)
            noise_aug_strength: Noise augmentation strength
            decode_chunk_size: Chunk size for decoding (lower = less VRAM)
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary with generated video path and metadata
        """
        await self.initialize()
        
        import torch
        from PIL import Image
        from diffusers.utils import export_to_video
        
        # Load and prepare input image
        image = Image.open(input_image_path).convert("RGB")
        image = image.resize((1024, 576))  # SVD expects this resolution
        
        # Set seed
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cpu").manual_seed(seed)
        else:
            seed = int(torch.randint(0, 2**32, (1,)).item())
            generator = torch.Generator(device="cpu").manual_seed(seed)
        
        logger.info(f"Animating image: {input_image_path} (frames={num_frames}, seed={seed})")
        
        def _generate():
            frames = self.pipe(
                image,
                num_frames=num_frames,
                motion_bucket_id=motion_bucket_id,
                noise_aug_strength=noise_aug_strength,
                decode_chunk_size=decode_chunk_size,
                generator=generator
            ).frames[0]
            return frames
        
        frames = await asyncio.to_thread(_generate)
        
        # Save video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}_{seed}.mp4"
        filepath = OUTPUT_DIR / filename
        
        export_to_video(frames, str(filepath), fps=fps)
        
        logger.info(f"Saved video: {filepath}")
        
        return {
            "status": "success",
            "video_path": str(filepath),
            "input_image": input_image_path,
            "seed": seed,
            "parameters": {
                "num_frames": num_frames,
                "fps": fps,
                "motion_bucket_id": motion_bucket_id,
                "duration_sec": num_frames / fps
            }
        }
    
    async def text_to_video(
        self,
        prompt: str,
        num_frames: int = 25,
        fps: int = 7,
        width: int = 512,
        height: int = 512,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate video directly from text prompt.
        First generates an image, then animates it.
        
        Args:
            prompt: Text description of the video
            num_frames: Number of frames
            fps: Frames per second
            width: Frame width
            height: Frame height
            seed: Random seed
            
        Returns:
            Dictionary with generated video path
        """
        # Import image generator for the first frame
        from neural_engine.specialized_systems.image_generator import get_image_generator
        
        logger.info(f"Text-to-video: '{prompt[:50]}...'")
        
        # Step 1: Generate initial image
        image_gen = get_image_generator()
        image_result = await image_gen.generate(
            prompt=prompt,
            width=width,
            height=height,
            seed=seed
        )
        
        if image_result.get("status") != "success":
            return {"status": "error", "message": "Failed to generate initial image"}
        
        initial_image_path = image_result["images"][0]
        seed = image_result["seed"]
        
        # Step 2: Animate the image
        video_result = await self.animate_image(
            input_image_path=initial_image_path,
            num_frames=num_frames,
            fps=fps,
            seed=seed
        )
        
        video_result["prompt"] = prompt
        video_result["initial_image"] = initial_image_path
        
        return video_result
    
    def unload(self):
        """Unload model to free GPU memory."""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
            self._initialized = False
            
            import torch
            torch.cuda.empty_cache()
            
            logger.info("VideoGenerator unloaded, GPU memory freed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get generator status."""
        return {
            "initialized": self._initialized,
            "model": self.model_id,
            "device": self.device,
            "output_dir": str(OUTPUT_DIR),
            "capabilities": [
                "image_to_video",
                "text_to_video"
            ]
        }


# Global singleton
_video_generator: Optional[VideoGenerator] = None


def get_video_generator() -> VideoGenerator:
    """Get or create global VideoGenerator instance."""
    global _video_generator
    if _video_generator is None:
        _video_generator = VideoGenerator()
    return _video_generator
