"""
API Routes for Specialized Systems
Exposes autonomous learning, model management, and creative studio via REST API
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("specialized_systems.api")

router = APIRouter(prefix="/specialized", tags=["Specialized Systems"])


# ========================================
# Request/Response Models
# ========================================

class LearningGoalRequest(BaseModel):
    topic: str = Field(..., description="Topic to learn")
    reason: str = Field(..., description="Why to learn this")
    priority: int = Field(default=5, description="Priority 1-10")


class KnowledgeGapRequest(BaseModel):
    conversations: List[str] = Field(..., description="Recent conversations to analyze")


class DatasetSearchRequest(BaseModel):
    topic: str = Field(..., description="Topic to search datasets for")
    limit: int = Field(default=5, description="Maximum results")


class AutoTrainRequest(BaseModel):
    topic: str = Field(..., description="Topic to auto-train on")


class ModelRegisterRequest(BaseModel):
    name: str = Field(..., description="Model name")
    model_type: str = Field(..., description="Model type (nlp, vision, generative, etc)")


class ContentRequest(BaseModel):
    content_type: str = Field(..., description="Type: haiku, poem, story")
    topic: str = Field(..., description="Topic for content")


# ========================================
# Autonomous Learning Routes
# ========================================

_self_improvement = None


def get_self_improvement():
    global _self_improvement
    if _self_improvement is None:
        from neural_engine.specialized_systems.self_improvement import SelfImprovementEngine
        _self_improvement = SelfImprovementEngine()
    return _self_improvement


@router.post("/learning/identify-gaps")
async def identify_knowledge_gaps(request: KnowledgeGapRequest):
    """
    Analyze conversations to identify knowledge gaps.
    """
    try:
        engine = get_self_improvement()
        gaps = engine.identify_knowledge_gaps(request.conversations)
        return {"gaps": gaps, "count": len(gaps)}
    except Exception as e:
        logger.error(f"Failed to identify gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/create-goal")
async def create_learning_goal(request: LearningGoalRequest):
    """
    Create a new learning goal for self-improvement.
    """
    try:
        engine = get_self_improvement()
        goal = engine.create_learning_goal(request.topic, request.reason, request.priority)
        return {
            "status": "created",
            "goal": {
                "topic": goal.topic,
                "reason": goal.reason,
                "priority": goal.priority,
                "status": goal.status
            }
        }
    except Exception as e:
        logger.error(f"Failed to create goal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/search-datasets")
async def search_datasets(request: DatasetSearchRequest):
    """
    Search HuggingFace for relevant datasets on a topic.
    """
    try:
        engine = get_self_improvement()
        datasets = engine.search_huggingface_datasets(request.topic, request.limit)
        return {"datasets": datasets, "count": len(datasets)}
    except Exception as e:
        logger.error(f"Failed to search datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/auto-train")
async def auto_train_on_topic(request: AutoTrainRequest):
    """
    Automatically find datasets and train on a topic.
    This is a long-running operation.
    """
    try:
        engine = get_self_improvement()
        result = await engine.auto_train_on_topic(request.topic)
        return result
    except Exception as e:
        logger.error(f"Auto-train failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/improvement-plan")
async def get_improvement_plan():
    """
    Get the current self-improvement plan.
    """
    try:
        engine = get_self_improvement()
        plan = engine.get_improvement_plan()
        return plan
    except Exception as e:
        logger.error(f"Failed to get plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/goals")
async def list_learning_goals():
    """
    List all current learning goals.
    """
    try:
        engine = get_self_improvement()
        goals = [
            {
                "topic": g.topic,
                "reason": g.reason,
                "priority": g.priority,
                "status": g.status,
                "created_at": g.created_at.isoformat()
            }
            for g in engine.learning_goals
        ]
        return {"goals": goals, "count": len(goals)}
    except Exception as e:
        logger.error(f"Failed to list goals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# AI Model Manager Routes
# ========================================

@router.get("/models/list")
async def list_models():
    """
    List all registered AI models.
    """
    try:
        from neural_engine.specialized_systems.model_manager import ai_model_manager
        return {"models": ai_model_manager.list_models()}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/stats")
async def get_model_stats():
    """
    Get statistics for all AI models.
    """
    try:
        from neural_engine.specialized_systems.model_manager import ai_model_manager
        return ai_model_manager.get_stats()
    except Exception as e:
        logger.error(f"Failed to get model stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Creative Studio Routes
# ========================================

@router.post("/creative/generate")
async def generate_content(request: ContentRequest):
    """
    Generate creative content (haiku, etc).
    """
    try:
        from neural_engine.specialized_systems.content_generator import ContentGenerator
        generator = ContentGenerator()
        
        if request.content_type == "haiku":
            content = generator.generate_haiku(request.topic)
        else:
            content = f"Content type '{request.content_type}' not yet implemented"
        
        return {"content": content, "type": request.content_type}
    except Exception as e:
        logger.error(f"Failed to generate content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Image Generation Routes
# ========================================

class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Text description of the image")
    negative_prompt: str = Field(default="ugly, blurry, low quality", description="What to avoid")
    width: int = Field(default=512, description="Image width")
    height: int = Field(default=512, description="Image height")
    num_inference_steps: int = Field(default=25, description="Denoising steps")
    guidance_scale: float = Field(default=7.5, description="Prompt adherence")
    seed: Optional[int] = Field(default=None, description="Random seed")


class Img2ImgRequest(BaseModel):
    prompt: str = Field(..., description="Transform description")
    input_image_path: str = Field(..., description="Path to input image")
    strength: float = Field(default=0.75, description="Transform strength 0-1")


@router.post("/media/image/generate")
async def generate_image(request: ImageGenerateRequest):
    """
    Generate image from text prompt using Stable Diffusion.
    """
    try:
        from neural_engine.specialized_systems.image_generator import get_image_generator
        generator = get_image_generator()
        result = await generator.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed
        )
        return result
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media/image/transform")
async def transform_image(request: Img2ImgRequest):
    """
    Transform an existing image based on a prompt (img2img).
    """
    try:
        from neural_engine.specialized_systems.image_generator import get_image_generator
        generator = get_image_generator()
        result = await generator.image_to_image(
            prompt=request.prompt,
            input_image_path=request.input_image_path,
            strength=request.strength
        )
        return result
    except Exception as e:
        logger.error(f"Image transform failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media/image/status")
async def image_generator_status():
    """Get image generator status."""
    try:
        from neural_engine.specialized_systems.image_generator import get_image_generator
        return get_image_generator().get_status()
    except Exception as e:
        return {"initialized": False, "error": str(e)}


# ========================================
# Audio Generation Routes
# ========================================

class AudioGenerateRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    voice_preset: str = Field(default="v2/ar_speaker_0", description="Voice preset")
    sample_rate: int = Field(default=24000, description="Audio sample rate")


class VoiceCloneRequest(BaseModel):
    text: str = Field(..., description="Text to speak")
    reference_audio_path: str = Field(..., description="Path to voice reference audio")


@router.post("/media/audio/synthesize")
async def synthesize_speech(request: AudioGenerateRequest):
    """
    Synthesize speech from text using Bark TTS.
    Supports Arabic and multiple languages.
    """
    try:
        from neural_engine.specialized_systems.audio_generator import get_audio_generator
        generator = get_audio_generator()
        result = await generator.synthesize(
            text=request.text,
            voice_preset=request.voice_preset,
            sample_rate=request.sample_rate
        )
        return result
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media/audio/clone-voice")
async def clone_voice(request: VoiceCloneRequest):
    """
    Clone a voice from reference audio and generate speech.
    """
    try:
        from neural_engine.specialized_systems.audio_generator import get_audio_generator
        generator = get_audio_generator()
        result = await generator.clone_voice(
            text=request.text,
            reference_audio_path=request.reference_audio_path
        )
        return result
    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media/audio/voices")
async def list_voices():
    """List available voice presets."""
    try:
        from neural_engine.specialized_systems.audio_generator import get_audio_generator
        return {"voices": get_audio_generator().get_available_voices()}
    except Exception as e:
        return {"voices": [], "error": str(e)}


@router.get("/media/audio/status")
async def audio_generator_status():
    """Get audio generator status."""
    try:
        from neural_engine.specialized_systems.audio_generator import get_audio_generator
        return get_audio_generator().get_status()
    except Exception as e:
        return {"initialized": False, "error": str(e)}


# ========================================
# Video Generation Routes
# ========================================

class VideoAnimateRequest(BaseModel):
    input_image_path: str = Field(..., description="Path to image to animate")
    num_frames: int = Field(default=25, description="Number of frames (14-25)")
    fps: int = Field(default=7, description="Frames per second")
    motion_bucket_id: int = Field(default=127, description="Motion intensity (1-255)")
    seed: Optional[int] = Field(default=None, description="Random seed")


class TextToVideoRequest(BaseModel):
    prompt: str = Field(..., description="Text description of the video")
    num_frames: int = Field(default=25, description="Number of frames")
    fps: int = Field(default=7, description="Frames per second")
    seed: Optional[int] = Field(default=None, description="Random seed")


@router.post("/media/video/animate")
async def animate_image(request: VideoAnimateRequest):
    """
    Animate a static image into a video using Stable Video Diffusion.
    """
    try:
        from neural_engine.specialized_systems.video_generator import get_video_generator
        generator = get_video_generator()
        result = await generator.animate_image(
            input_image_path=request.input_image_path,
            num_frames=request.num_frames,
            fps=request.fps,
            motion_bucket_id=request.motion_bucket_id,
            seed=request.seed
        )
        return result
    except Exception as e:
        logger.error(f"Video animation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media/video/text-to-video")
async def text_to_video(request: TextToVideoRequest):
    """
    Generate video from text prompt.
    First generates an image, then animates it.
    """
    try:
        from neural_engine.specialized_systems.video_generator import get_video_generator
        generator = get_video_generator()
        result = await generator.text_to_video(
            prompt=request.prompt,
            num_frames=request.num_frames,
            fps=request.fps,
            seed=request.seed
        )
        return result
    except Exception as e:
        logger.error(f"Text-to-video failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media/video/status")
async def video_generator_status():
    """Get video generator status."""
    try:
        from neural_engine.specialized_systems.video_generator import get_video_generator
        return get_video_generator().get_status()
    except Exception as e:
        return {"initialized": False, "error": str(e)}


# ========================================
# Media Unload (Free GPU Memory)
# ========================================

@router.post("/media/unload/{generator_type}")
async def unload_generator(generator_type: str):
    """
    Unload a media generator to free GPU memory.
    generator_type: "image", "audio", or "video"
    """
    try:
        if generator_type == "image":
            from neural_engine.specialized_systems.image_generator import get_image_generator
            get_image_generator().unload()
        elif generator_type == "audio":
            from neural_engine.specialized_systems.audio_generator import get_audio_generator
            get_audio_generator().unload()
        elif generator_type == "video":
            from neural_engine.specialized_systems.video_generator import get_video_generator
            get_video_generator().unload()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown generator: {generator_type}")
        
        return {"status": "unloaded", "generator": generator_type}
    except Exception as e:
        logger.error(f"Unload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# GPU Controller (Smart Mode Switching)
# ========================================

class GPUModeRequest(BaseModel):
    mode: str = Field(..., description="Target mode: idle, llm, image, video")


class SmartVideoRequest(BaseModel):
    input_image_path: str = Field(..., description="Path to image to animate")
    num_frames: int = Field(default=14, description="Number of frames")
    fps: int = Field(default=7, description="Frames per second")
    motion_bucket_id: int = Field(default=127, description="Motion intensity")
    seed: Optional[int] = Field(default=None, description="Random seed")


@router.get("/gpu/status")
async def gpu_status():
    """
    Get current GPU status including mode, memory usage, and loaded models.
    """
    try:
        from neural_engine.specialized_systems.gpu_controller import get_gpu_controller
        controller = get_gpu_controller()
        return await controller.get_status()
    except Exception as e:
        logger.error(f"GPU status failed: {e}")
        return {"error": str(e)}


@router.post("/gpu/switch-mode")
async def switch_gpu_mode(request: GPUModeRequest):
    """
    Switch GPU to specified mode.
    Modes: idle, llm, image, video
    
    This will unload conflicting models and free GPU memory.
    """
    try:
        from neural_engine.specialized_systems.gpu_controller import (
            get_gpu_controller, GPUMode
        )
        
        mode_map = {
            "idle": GPUMode.IDLE,
            "llm": GPUMode.LLM,
            "image": GPUMode.IMAGE,
            "video": GPUMode.VIDEO
        }
        
        if request.mode not in mode_map:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid mode. Choose from: {list(mode_map.keys())}"
            )
        
        controller = get_gpu_controller()
        result = await controller.switch_to_mode(mode_map[request.mode])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GPU mode switch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media/video/smart-generate")
async def smart_video_generate(request: SmartVideoRequest):
    """
    Smart video generation with automatic GPU mode switching.
    
    This endpoint:
    1. Unloads LLM to free GPU memory
    2. Loads and runs Stable Video Diffusion
    3. Generates the video
    4. Restores LLM for chat functionality
    
    Use this for video generation on limited GPU memory (12GB).
    """
    try:
        from neural_engine.specialized_systems.gpu_controller import get_gpu_controller
        
        controller = get_gpu_controller()
        result = await controller.request_video_generation(
            input_image_path=request.input_image_path,
            num_frames=request.num_frames,
            fps=request.fps,
            motion_bucket_id=request.motion_bucket_id,
            seed=request.seed
        )
        return result
    except Exception as e:
        logger.error(f"Smart video generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Health Check
# ========================================

@router.get("/health")
async def health_check():
    """
    Check specialized systems health.
    """
    return {
        "status": "healthy",
        "modules": {
            "autonomous_learning": True,
            "ai_model_manager": True,
            "creative_studio": True,
            "image_generator": True,
            "audio_generator": True,
            "video_generator": True,
            "gpu_controller": True,
            "code_intelligence": True,
            "web_research": True
        }
    }


