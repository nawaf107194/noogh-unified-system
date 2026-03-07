"""
Image Generator - Stable Diffusion Integration
Provides text-to-image, image-to-image, and inpainting capabilities
"""
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

# Output directory for generated images
OUTPUT_DIR = Path(os.getenv("NOOGH_DATA_DIR", "./data")) / "generated" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ImageGenerator:
    """
    AI-powered image generation using Stable Diffusion.
    Supports text-to-image, image-to-image, and inpainting.
    """
    
    def __init__(self, model_id: str = "runwayml/stable-diffusion-v1-5"):
        """
        Initialize the image generator.
        
        Args:
            model_id: HuggingFace model ID for Stable Diffusion
        """
        self.model_id = model_id
        self.pipe = None
        self.device = "cuda"
        self._initialized = False
        logger.info(f"ImageGenerator initialized with model: {model_id}")
    
    async def initialize(self):
        """Lazy load the Stable Diffusion pipeline."""
        if self._initialized:
            return
        
        try:
            import torch
            from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
            
            logger.info(f"Loading Stable Diffusion model: {self.model_id}")
            
            # Load with optimizations for RTX 5070 (12GB VRAM)
            self.pipe = StableDiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16,
                safety_checker=None,  # Disable for speed (internal use)
                variant="fp16"
            )
            
            # Use faster scheduler
            self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipe.scheduler.config
            )
            
            # Move to GPU
            self.pipe = self.pipe.to(self.device)
            
            # Enable memory optimizations
            self.pipe.enable_attention_slicing()
            # self.pipe.enable_xformers_memory_efficient_attention()  # If xformers installed
            
            self._initialized = True
            logger.info("✅ Stable Diffusion model loaded successfully")
            
        except ImportError as e:
            logger.error(f"Missing dependency for image generation: {e}")
            logger.error("Install with: pip install diffusers transformers accelerate")
            raise RuntimeError(f"Image generation not available: {e}")
        except Exception as e:
            logger.error(f"Failed to load Stable Diffusion: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "ugly, blurry, low quality, distorted",
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 25,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        num_images: int = 1
    ) -> Dict[str, Any]:
        """
        Generate image from text prompt.
        
        Args:
            prompt: Text description of the image to generate
            negative_prompt: What to avoid in the image
            width: Image width (must be divisible by 8)
            height: Image height (must be divisible by 8)
            num_inference_steps: Number of denoising steps
            guidance_scale: How closely to follow the prompt (7-12 typical)
            seed: Random seed for reproducibility
            num_images: Number of images to generate
            
        Returns:
            Dictionary with generated image paths and metadata
        """
        await self.initialize()
        
        import torch
        
        # Set seed for reproducibility
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            seed = int(torch.randint(0, 2**32, (1,)).item())
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        logger.info(f"Generating image: '{prompt[:50]}...' (seed={seed})")
        
        # Run generation in thread to not block event loop
        def _generate():
            return self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                num_images_per_prompt=num_images
            )
        
        result = await asyncio.to_thread(_generate)
        
        # Save images
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_paths = []
        
        for i, image in enumerate(result.images):
            filename = f"img_{timestamp}_{seed}_{i}.png"
            filepath = OUTPUT_DIR / filename
            image.save(filepath)
            image_paths.append(str(filepath))
            logger.info(f"Saved image: {filepath}")
        
        return {
            "status": "success",
            "images": image_paths,
            "count": len(image_paths),
            "prompt": prompt,
            "seed": seed,
            "parameters": {
                "width": width,
                "height": height,
                "steps": num_inference_steps,
                "guidance_scale": guidance_scale
            }
        }
    
    async def image_to_image(
        self,
        prompt: str,
        input_image_path: str,
        strength: float = 0.75,
        negative_prompt: str = "ugly, blurry, low quality",
        num_inference_steps: int = 25,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transform an existing image based on a prompt.
        
        Args:
            prompt: Text description of desired transformation
            input_image_path: Path to input image
            strength: How much to transform (0-1, higher = more change)
            negative_prompt: What to avoid
            num_inference_steps: Denoising steps
            guidance_scale: Prompt adherence
            seed: Random seed
            
        Returns:
            Dictionary with transformed image path
        """
        await self.initialize()
        
        import torch
        from PIL import Image
        from diffusers import StableDiffusionImg2ImgPipeline
        
        # Load input image
        init_image = Image.open(input_image_path).convert("RGB")
        init_image = init_image.resize((512, 512))
        
        # Use img2img pipeline
        img2img_pipe = StableDiffusionImg2ImgPipeline(**self.pipe.components)
        
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            seed = int(torch.randint(0, 2**32, (1,)).item())
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        def _transform():
            return img2img_pipe(
                prompt=prompt,
                image=init_image,
                strength=strength,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator
            )
        
        result = await asyncio.to_thread(_transform)
        
        # Save result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"img2img_{timestamp}_{seed}.png"
        filepath = OUTPUT_DIR / filename
        result.images[0].save(filepath)
        
        return {
            "status": "success",
            "image": str(filepath),
            "prompt": prompt,
            "seed": seed,
            "strength": strength
        }
    
    def unload(self):
        """Unload model to free GPU memory."""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
            self._initialized = False
            
            import torch
            torch.cuda.empty_cache()
            
            logger.info("ImageGenerator unloaded, GPU memory freed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get generator status."""
        return {
            "initialized": self._initialized,
            "model": self.model_id,
            "device": self.device,
            "output_dir": str(OUTPUT_DIR)
        }


# Global singleton
_image_generator: Optional[ImageGenerator] = None


def get_image_generator() -> ImageGenerator:
    """Get or create global ImageGenerator instance."""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator
