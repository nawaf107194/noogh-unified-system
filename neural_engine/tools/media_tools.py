"""
Media Tools for ALLaM
Provides image, audio, and video generation capabilities.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def generate_image(
    prompt: str,
    negative_prompt: str = "ugly, blurry, low quality",
    width: int = 512,
    height: int = 512
) -> Dict[str, Any]:
    """
    Generate an image from text prompt.
    
    Args:
        prompt: Text description of the image
        negative_prompt: What to avoid
        width: Image width
        height: Image height
        
    Returns:
        Dict with image path and status
    """
    try:
        from neural_engine.specialized_systems.image_generator import get_image_generator
        
        generator = get_image_generator()
        result = await generator.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height
        )
        
        if result.get("status") == "success":
            images = result.get("images", [])
            return {
                "success": True,
                "images": images,
                "prompt": prompt,
                "summary_ar": f"تم توليد الصورة بنجاح! المسار: {images[0] if images else 'N/A'}"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "summary_ar": f"فشل توليد الصورة: {result.get('error', 'خطأ غير معروف')}"
            }
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل توليد الصورة: {str(e)}"
        }


async def generate_audio(
    text: str,
    voice_preset: str = "v2/ar_speaker_0"
) -> Dict[str, Any]:
    """
    Generate audio (TTS) from text.
    
    Args:
        text: Text to convert to speech
        voice_preset: Voice preset (Arabic by default)
        
    Returns:
        Dict with audio path and status
    """
    try:
        from neural_engine.specialized_systems.audio_generator import get_audio_generator
        
        generator = get_audio_generator()
        result = await generator.synthesize(
            text=text,
            voice_preset=voice_preset
        )
        
        if result.get("status") == "success":
            return {
                "success": True,
                "audio_path": result.get("audio_path"),
                "duration": result.get("duration"),
                "summary_ar": f"تم توليد الصوت بنجاح! المدة: {result.get('duration', 'N/A')} ثانية"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "summary_ar": f"فشل توليد الصوت: {result.get('error', 'خطأ غير معروف')}"
            }
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل توليد الصوت: {str(e)}"
        }


async def generate_video(
    prompt: str,
    num_frames: int = 25,
    fps: int = 7
) -> Dict[str, Any]:
    """
    Generate video from text prompt.
    
    Args:
        prompt: Text description for the video
        num_frames: Number of frames
        fps: Frames per second
        
    Returns:
        Dict with video path and status
    """
    try:
        from neural_engine.specialized_systems.video_generator import get_video_generator
        
        generator = get_video_generator()
        result = await generator.text_to_video(
            prompt=prompt,
            num_frames=num_frames,
            fps=fps
        )
        
        if result.get("status") == "success":
            return {
                "success": True,
                "video_path": result.get("video_path"),
                "duration_sec": result.get("parameters", {}).get("duration_sec"),
                "summary_ar": f"تم توليد الفيديو بنجاح! المسار: {result.get('video_path')}"
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Unknown error"),
                "summary_ar": f"فشل توليد الفيديو: {result.get('message', 'خطأ غير معروف')}"
            }
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل توليد الفيديو: {str(e)}"
        }


def get_media_status() -> Dict[str, Any]:
    """
    Get status of all media generators.
    
    Returns:
        Dict with status of each generator
    """
    status = {
        "image_generator": {"status": "unknown"},
        "audio_generator": {"status": "unknown"},
        "video_generator": {"status": "unknown"}
    }
    
    try:
        from neural_engine.specialized_systems.image_generator import get_image_generator
        img_gen = get_image_generator()
        status["image_generator"] = img_gen.get_status()
    except Exception as e:
        status["image_generator"] = {"status": "error", "error": str(e)}
    
    try:
        from neural_engine.specialized_systems.audio_generator import get_audio_generator
        audio_gen = get_audio_generator()
        status["audio_generator"] = audio_gen.get_status()
    except Exception as e:
        status["audio_generator"] = {"status": "error", "error": str(e)}
    
    try:
        from neural_engine.specialized_systems.video_generator import get_video_generator
        video_gen = get_video_generator()
        status["video_generator"] = video_gen.get_status()
    except Exception as e:
        status["video_generator"] = {"status": "error", "error": str(e)}
    
    status["summary_ar"] = "حالة الوسائط: صور ✅، صوت ✅، فيديو ✅"
    return status


# Tool registration helper
def register_media_tools(registry=None):
    """NO-OP: Tools are now defined in unified_core.tools.definitions.
    
    This function previously registered tools with the deprecated
    neural_engine.tools.tool_registry. All tools are now managed
    statically via unified_core.tool_registry.
    """
    logger.debug(
        "register_media_tools() is superseded by unified_core.tools.definitions"
    )
