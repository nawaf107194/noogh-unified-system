import base64
import io
import logging
from typing import Any, Dict, List, Optional

import torch
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor, CLIPModel, CLIPProcessor

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Processes visual inputs using vision transformers (CLIP, BLIP).
    Provides image understanding, captioning, and similarity search.
    
    CRITICAL FIX: Models are now lazy-loaded on first use to prevent
    import-time memory allocation that bypasses ModelAuthority.
    """

    def __init__(self, use_gpu: bool = True):
        import os

        # Check environment override first
        env_device = os.environ.get("NOOGH_VISION_DEVICE")
        if env_device:
            self.device = env_device
        else:
            # Default to CPU for vision to save VRAM for LLM/Training
            self.device = "cpu"

        # LAZY LOADING: Models are None until first use
        self.clip_model = None
        self.clip_processor = None
        self.blip_model = None
        self.blip_processor = None
        self._initialized = False

        logger.info(f"ImageProcessor configured for {self.device} (models will load on first use)")

    def _ensure_models_loaded(self):
        """
        Lazy load models on first actual use.
        This prevents import-time loading that causes memory exhaustion.
        """
        if self._initialized:
            return

        logger.info(f"Loading vision models on demand (device: {self.device})...")

        # Initialize CLIP for image understanding
        try:
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_model.to(self.device)
            logger.info(f"CLIP model loaded on {self.device}")
        except Exception as e:
            logger.error(f"Error loading CLIP: {e}")
            self.clip_model = None
            self.clip_processor = None

        # Initialize BLIP for image captioning
        try:
            self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.blip_model.to(self.device)
            logger.info(f"BLIP model loaded on {self.device}")
        except Exception as e:
            logger.error(f"Error loading BLIP: {e}")
            self.blip_model = None
            self.blip_processor = None

        self._initialized = True
        logger.info("Vision models initialized on demand")

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process an image and extract features, captions, and embeddings.

        Args:
            image_path: Path to image file or base64 encoded image

        Returns:
            Dictionary with image analysis results
        """
        # Ensure models are loaded before processing
        self._ensure_models_loaded()
        
        try:
            # Load image
            if image_path.startswith("data:image"):
                # Base64 encoded image
                image_data = image_path.split(",")[1]
                image = Image.open(io.BytesIO(base64.b64decode(image_data)))
            else:
                # File path
                image = Image.open(image_path)

            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            result = {
                "size": image.size,
                "mode": image.mode,
                "format": image.format if hasattr(image, "format") else "unknown",
            }

            # Generate caption with BLIP
            if self.blip_model and self.blip_processor:
                caption = self._generate_caption(image)
                result["caption"] = caption

            # Generate embedding with CLIP
            if self.clip_model and self.clip_processor:
                embedding = self._generate_embedding(image)
                result["embedding"] = embedding
                result["embedding_dim"] = len(embedding) if embedding else 0

            # Classify with CLIP (zero-shot)
            if self.clip_model and self.clip_processor:
                categories = self._classify_image(image)
                result["categories"] = categories

            logger.info(f"Image processed: {result.get('caption', 'No caption')[:50]}")
            return result

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {"error": str(e), "description": "Failed to process image"}

    def _generate_caption(self, image: Image.Image) -> str:
        """Generate a caption for the image using BLIP."""
        self._ensure_models_loaded()
        try:
            inputs = self.blip_processor(image, return_tensors="pt").to(self.device)

            with torch.no_grad():
                generated_ids = self.blip_model.generate(**inputs, max_length=50)

            caption = self.blip_processor.decode(generated_ids[0], skip_special_tokens=True)
            return caption

        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return "Caption generation failed"

    def _generate_embedding(self, image: Image.Image) -> Optional[List[float]]:
        """Generate image embedding using CLIP."""
        self._ensure_models_loaded()
        try:
            inputs = self.clip_processor(images=image, return_tensors="pt").to(self.device)

            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)

            # Normalize and convert to list
            embedding = image_features[0].cpu().numpy().tolist()
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def _classify_image(self, image: Image.Image, categories: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Zero-shot image classification using CLIP.

        Args:
            image: PIL Image
            categories: List of category labels (default: common categories)

        Returns:
            Dictionary mapping categories to probabilities
        """
        self._ensure_models_loaded()
        
        if categories is None:
            categories = [
                "a photo of a person",
                "a photo of an animal",
                "a photo of a building",
                "a photo of nature",
                "a photo of food",
                "a photo of a vehicle",
                "a photo of technology",
                "a screenshot of code",
                "a diagram or chart",
                "abstract art",
            ]

        try:
            inputs = self.clip_processor(text=categories, images=image, return_tensors="pt", padding=True).to(
                self.device
            )

            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)[0]

            # Create category -> probability mapping
            results = {cat: float(prob) for cat, prob in zip(categories, probs.cpu().numpy())}

            # Sort by probability
            results = dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

            return results

        except Exception as e:
            logger.error(f"Error classifying image: {e}")
            return {}

    def compare_images(self, image1_path: str, image2_path: str) -> float:
        """
        Compare two images and return similarity score.

        Returns:
            Similarity score between 0 and 1
        """
        self._ensure_models_loaded()
        try:
            # Load images
            img1 = Image.open(image1_path).convert("RGB")
            img2 = Image.open(image2_path).convert("RGB")

            # Get embeddings
            emb1 = self._generate_embedding(img1)
            emb2 = self._generate_embedding(img2)

            if emb1 and emb2:
                # Cosine similarity
                emb1_tensor = torch.tensor(emb1)
                emb2_tensor = torch.tensor(emb2)

                similarity = torch.nn.functional.cosine_similarity(emb1_tensor.unsqueeze(0), emb2_tensor.unsqueeze(0))

                return float(similarity.item())

            return 0.0

        except Exception as e:
            logger.error(f"Error comparing images: {e}")
            return 0.0

    def search_by_text(self, image_paths: List[str], query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search images by text query using CLIP.

        Args:
            image_paths: List of image file paths
            query: Text query
            top_k: Number of top results to return

        Returns:
            List of results with image paths and similarity scores
        """
        self._ensure_models_loaded()
        try:
            # Load all images
            images = [Image.open(path).convert("RGB") for path in image_paths]

            # Process text and images
            inputs = self.clip_processor(text=[query], images=images, return_tensors="pt", padding=True).to(self.device)

            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_text = outputs.logits_per_text
                probs = logits_per_text.softmax(dim=1)[0]

            # Create results
            results = [{"path": path, "score": float(score)} for path, score in zip(image_paths, probs.cpu().numpy())]

            # Sort and return top_k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Error in text search: {e}")
            return []
