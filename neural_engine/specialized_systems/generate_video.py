#!/usr/bin/env python3
"""
Standalone Video Generator
Runs Stable Video Diffusion in isolation without LLM to maximize GPU memory.

Usage:
    python generate_video.py <input_image> [--frames 14] [--fps 7] [--motion 127]
    
Example:
    python generate_video.py data/generated/images/img_xxx.png --frames 14
"""
import argparse
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    parser = argparse.ArgumentParser(description="Generate video from image using SVD")
    parser.add_argument("input_image", help="Path to input image")
    parser.add_argument("--frames", type=int, default=14, help="Number of frames (14-25)")
    parser.add_argument("--fps", type=int, default=7, help="Frames per second")
    parser.add_argument("--motion", type=int, default=127, help="Motion intensity (1-255)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--decode-chunk", type=int, default=4, help="Decode chunk size (lower = less VRAM)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_image):
        print(f"❌ Image not found: {args.input_image}")
        sys.exit(1)
    
    print("🎬 Standalone Video Generator")
    print("=" * 50)
    print(f"Input: {args.input_image}")
    print(f"Frames: {args.frames}")
    print(f"FPS: {args.fps}")
    print(f"Motion: {args.motion}")
    print("=" * 50)
    
    # Generate video
    print("\n📥 Loading Stable Video Diffusion...")
    
    import torch
    from datetime import datetime
    from PIL import Image
    from diffusers import StableVideoDiffusionPipeline
    from diffusers.utils import export_to_video
    from pathlib import Path
    
    # Clear any existing GPU memory
    torch.cuda.empty_cache()
    
    # Check GPU memory
    if torch.cuda.is_available():
        total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        free = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / (1024**3)
        print(f"GPU Memory: {free:.1f}GB free / {total:.1f}GB total")
    
    # Load model with maximum memory optimization
    model_id = "stabilityai/stable-video-diffusion-img2vid"
    
    pipe = StableVideoDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        variant="fp16"
    )
    
    # Use sequential CPU offload for minimum VRAM
    pipe.enable_sequential_cpu_offload()
    pipe.enable_attention_slicing()
    
    print("✅ Model loaded with CPU offload")
    
    # Prepare image
    image = Image.open(args.input_image).convert("RGB")
    image = image.resize((1024, 576))  # SVD expects this resolution
    
    # Set seed
    seed = args.seed if args.seed else int(torch.randint(0, 2**32, (1,)).item())
    generator = torch.Generator(device="cpu").manual_seed(seed)
    
    print(f"\n🎥 Generating {args.frames} frames (seed={seed})...")
    
    # Generate frames
    frames = pipe(
        image,
        num_frames=args.frames,
        motion_bucket_id=args.motion,
        noise_aug_strength=0.02,
        decode_chunk_size=args.decode_chunk,
        generator=generator
    ).frames[0]
    
    # Save video
    output_dir = Path("data/generated/videos")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"video_{timestamp}_{seed}.mp4"
    
    export_to_video(frames, str(output_path), fps=args.fps)
    
    duration = args.frames / args.fps
    print(f"\n✅ Video saved: {output_path}")
    print(f"   Duration: {duration:.1f} seconds")
    print(f"   Seed: {seed}")
    
    # Cleanup
    del pipe
    torch.cuda.empty_cache()
    
    print("\n🎉 Done!")
    return str(output_path)


if __name__ == "__main__":
    result = asyncio.run(main())
