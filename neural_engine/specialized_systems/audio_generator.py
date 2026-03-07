"""
Audio Generator - Text-to-Speech and Voice Synthesis
Provides TTS, voice cloning, and audio generation capabilities
"""
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

# Output directory for generated audio
OUTPUT_DIR = Path(os.getenv("NOOGH_DATA_DIR", "./data")) / "generated" / "audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class AudioGenerator:
    """
    AI-powered audio generation using Bark/Coqui TTS.
    Supports text-to-speech, voice cloning, and multilingual synthesis.
    """
    
    def __init__(self, model_type: str = "bark"):
        """
        Initialize the audio generator.
        
        Args:
            model_type: "bark" for Bark TTS or "coqui" for Coqui TTS
        """
        self.model_type = model_type
        self.model = None
        self.processor = None
        self.device = "cuda"
        self._initialized = False
        logger.info(f"AudioGenerator initialized with model type: {model_type}")
    
    async def initialize(self):
        """Lazy load the TTS model."""
        if self._initialized:
            return
        
        try:
            if self.model_type == "bark":
                await self._init_bark()
            else:
                await self._init_coqui()
            
            self._initialized = True
            logger.info("✅ Audio generation model loaded successfully")
            
        except ImportError as e:
            logger.error(f"Missing dependency for audio generation: {e}")
            logger.error("Install with: pip install bark transformers scipy")
            raise RuntimeError(f"Audio generation not available: {e}")
        except Exception as e:
            logger.error(f"Failed to load audio model: {e}")
            raise
    
    async def _init_bark(self):
        """Initialize Bark TTS model."""
        import torch
        from transformers import AutoProcessor, BarkModel
        
        logger.info("Loading Bark TTS model...")
        
        model_id = "suno/bark-small"  # Use small for faster generation
        
        self.processor = AutoProcessor.from_pretrained(model_id)
        
        # Load on CPU to avoid device mismatch issues
        self.model = BarkModel.from_pretrained(
            model_id,
            torch_dtype=torch.float32
        )
        # Keep on CPU - Bark small is fast enough
        self.device = "cpu"
        
        logger.info("Bark TTS model loaded on CPU")
    
    async def _init_coqui(self):
        """Initialize Coqui TTS model."""
        try:
            from TTS.api import TTS
            
            logger.info("Loading Coqui TTS model...")
            
            # Use a multilingual model
            self.model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
            self.model.to(self.device)
            
            logger.info("Coqui TTS model loaded")
        except ImportError:
            logger.warning("Coqui TTS not available, falling back to Bark")
            await self._init_bark()
    
    async def synthesize(
        self,
        text: str,
        voice_preset: str = "v2/ar_speaker_0",  # Arabic voice by default
        output_format: str = "wav",
        sample_rate: int = 24000
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to convert to speech
            voice_preset: Voice preset (e.g., "v2/ar_speaker_0" for Arabic)
            output_format: Output format (wav, mp3)
            sample_rate: Audio sample rate
            
        Returns:
            Dictionary with audio file path and metadata
        """
        await self.initialize()
        
        logger.info(f"Synthesizing speech: '{text[:50]}...'")
        
        if self.model_type == "bark":
            return await self._synthesize_bark(text, voice_preset, sample_rate)
        else:
            return await self._synthesize_coqui(text, voice_preset, sample_rate)
    
    async def _synthesize_bark(
        self,
        text: str,
        voice_preset: str,
        sample_rate: int
    ) -> Dict[str, Any]:
        """Generate speech using Bark."""
        import torch
        import scipy.io.wavfile as wavfile
        
        def _generate():
            # Bark-small doesn't use voice_preset, just text
            inputs = self.processor(
                text,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                audio_array = self.model.generate(**inputs)
            
            return audio_array.cpu().numpy().squeeze()
        
        audio_array = await asyncio.to_thread(_generate)
        
        # Save audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"speech_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        wavfile.write(str(filepath), sample_rate, audio_array)
        
        logger.info(f"Saved audio: {filepath}")
        
        return {
            "status": "success",
            "audio_path": str(filepath),
            "text": text,
            "voice": "bark-small",
            "sample_rate": sample_rate,
            "duration_sec": len(audio_array) / sample_rate
        }
    
    async def _synthesize_coqui(
        self,
        text: str,
        voice_preset: str,
        sample_rate: int
    ) -> Dict[str, Any]:
        """Generate speech using Coqui TTS."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"speech_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        def _generate():
            self.model.tts_to_file(
                text=text,
                file_path=str(filepath),
                language="ar"  # Arabic
            )
        
        await asyncio.to_thread(_generate)
        
        return {
            "status": "success",
            "audio_path": str(filepath),
            "text": text,
            "voice": "xtts_v2",
            "sample_rate": sample_rate
        }
    
    async def clone_voice(
        self,
        text: str,
        reference_audio_path: str,
        output_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Clone a voice from reference audio and synthesize new speech.
        
        Args:
            text: Text to speak in cloned voice
            reference_audio_path: Path to reference audio file
            output_format: Output audio format
            
        Returns:
            Dictionary with generated audio path
        """
        await self.initialize()
        
        if self.model_type != "coqui":
            return {
                "status": "error",
                "message": "Voice cloning requires Coqui TTS"
            }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cloned_{timestamp}.wav"
        filepath = OUTPUT_DIR / filename
        
        def _clone():
            self.model.tts_to_file(
                text=text,
                file_path=str(filepath),
                speaker_wav=reference_audio_path,
                language="ar"
            )
        
        await asyncio.to_thread(_clone)
        
        return {
            "status": "success",
            "audio_path": str(filepath),
            "text": text,
            "reference": reference_audio_path
        }
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voice presets."""
        # Bark voice presets
        voices = [
            "v2/ar_speaker_0",  # Arabic
            "v2/ar_speaker_1",
            "v2/en_speaker_0",  # English
            "v2/en_speaker_1",
            "v2/en_speaker_2",
            "v2/en_speaker_3",
            "v2/de_speaker_0",  # German
            "v2/fr_speaker_0",  # French
            "v2/es_speaker_0",  # Spanish
            "v2/zh_speaker_0",  # Chinese
        ]
        return voices
    
    def unload(self):
        """Unload model to free GPU memory."""
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            self._initialized = False
            
            import torch
            torch.cuda.empty_cache()
            
            logger.info("AudioGenerator unloaded, GPU memory freed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get generator status."""
        return {
            "initialized": self._initialized,
            "model_type": self.model_type,
            "device": self.device,
            "output_dir": str(OUTPUT_DIR),
            "available_voices": self.get_available_voices()
        }


# Global singleton
_audio_generator: Optional[AudioGenerator] = None


def get_audio_generator() -> AudioGenerator:
    """Get or create global AudioGenerator instance."""
    global _audio_generator
    if _audio_generator is None:
        _audio_generator = AudioGenerator()
    return _audio_generator
