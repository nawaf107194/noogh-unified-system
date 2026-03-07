# gateway/app/ml/__init__.py

from gateway.app.ml.evaluator import Evaluator
from gateway.app.ml.curriculum import Curriculum
from gateway.app.ml.dream_worker import DreamWorker

class MLModelFactory:
    @staticmethod
    def create_model(model_type: str, **kwargs):
        if model_type == "evaluator":
            return Evaluator(**kwargs)
        elif model_type == "curriculum":
            return Curriculum(**kwargs)
        elif model_type == "dream_worker":
            return DreamWorker(**kwargs)
        else:
            raise ValueError(f"Unknown model type: {model_type}")