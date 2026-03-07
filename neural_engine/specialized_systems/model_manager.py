"""
AI Model Manager - Orchestrate and manage multiple AI models.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AIModelType(Enum):
    """Types of AI models"""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    NLP = "nlp"
    VISION = "vision"
    GENERATIVE = "generative"
    EMBEDDING = "embedding"
    REASONING = "reasoning"


class AIModel:
    """Wrapper for an AI model"""

    def __init__(self, name: str, model_type: AIModelType, model: Any, metadata: Optional[Dict] = None):
        self.name = name
        self.type = model_type
        self.model = model
        self.metadata = metadata or {}
        self.usage_count = 0
        self.total_inference_time = 0.0
        self.created_at = datetime.now()

    async def predict(self, input_data: Any) -> Any:
        """Make prediction"""
        start_time = datetime.now()

        # Call model
        if hasattr(self.model, "predict"):
            result = await self.model.predict(input_data)
        elif callable(self.model):
            result = await self.model(input_data)
        else:
            raise ValueError(f"Model {self.name} is not callable")

        # Update stats
        inference_time = (datetime.now() - start_time).total_seconds()
        self.usage_count += 1
        self.total_inference_time += inference_time

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        avg_time = self.total_inference_time / self.usage_count if self.usage_count > 0 else 0

        return {
            "name": self.name,
            "type": self.type.value,
            "usage_count": self.usage_count,
            "total_time": self.total_inference_time,
            "avg_inference_time": avg_time,
            "metadata": self.metadata,
        }


class AIModelManager:
    """
    Manage multiple AI models.
    Handles registration, selection, and orchestration.
    """

    def __init__(self):
        self.models: Dict[str, AIModel] = {}
        self.model_by_type: Dict[AIModelType, List[str]] = {t: [] for t in AIModelType}
        logger.info("AIModelManager initialized")

    def register_model(
        self, name: str, model_type: AIModelType, model: Any, metadata: Optional[Dict] = None
    ) -> AIModel:
        """Register a new model"""
        if name in self.models:
            raise ValueError(f"Model {name} already registered")

        ai_model = AIModel(name, model_type, model, metadata)
        self.models[name] = ai_model
        self.model_by_type[model_type].append(name)

        logger.info(f"Registered model: {name} ({model_type.value})")
        return ai_model

    def unregister_model(self, name: str):
        """Unregister a model"""
        if name not in self.models:
            raise ValueError(f"Model {name} not found")

        model = self.models[name]
        self.model_by_type[model.type].remove(name)
        del self.models[name]

        logger.info(f"Unregistered model: {name}")

    async def predict(self, model_name: str, input_data: Any) -> Any:
        """Make prediction using a specific model"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        model = self.models[model_name]
        return await model.predict(input_data)

    async def predict_with_type(
        self, model_type: AIModelType, input_data: Any, prefer_model: Optional[str] = None
    ) -> Any:
        """
        Make prediction using any model of the given type.

        Args:
            model_type: Type of model to use
            input_data: Input for prediction
            prefer_model: Preferred model name (if available)
        """
        available_models = self.model_by_type.get(model_type, [])

        if not available_models:
            raise ValueError(f"No models available for type: {model_type.value}")

        # Use preferred model if available
        if prefer_model and prefer_model in available_models:
            model_name = prefer_model
        else:
            # Use least-used model for load balancing
            model_name = min(available_models, key=lambda n: self.models[n].usage_count)

        return await self.predict(model_name, input_data)

    def get_model(self, name: str) -> Optional[AIModel]:
        """Get a model by name"""
        return self.models.get(name)

    def get_models_by_type(self, model_type: AIModelType) -> List[AIModel]:
        """Get all models of a specific type"""
        model_names = self.model_by_type.get(model_type, [])
        return [self.models[name] for name in model_names]

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        total_usage = sum(m.usage_count for m in self.models.values())

        type_counts = {t.value: len(models) for t, models in self.model_by_type.items() if models}

        model_stats = {name: model.get_stats() for name, model in self.models.items()}

        return {
            "total_models": len(self.models),
            "models_by_type": type_counts,
            "total_predictions": total_usage,
            "model_stats": model_stats,
        }

    def list_models(self) -> List[str]:
        """List all registered models"""
        return list(self.models.keys())


# Global instance
ai_model_manager = AIModelManager()
