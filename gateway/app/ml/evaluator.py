import logging
from pathlib import Path
from typing import Dict, List


from gateway.app.llm.brain_factory import create_brain

logger = logging.getLogger("ml.evaluator")


class ModelEvaluator:
    """Quantitative evaluation system for Model Performance."""

    def __init__(self, secrets: Dict[str, str], data_dir: str):
            if not data_dir:
                raise ValueError("data_dir is required for ModelEvaluator")
            output_dir_path = Path(data_dir) / "evaluations"
            output_dir_path.mkdir(parents=True, exist_ok=True)
            self.output_dir = output_dir_path
            self.secrets = secrets
            self.evaluator_llm = create_brain(secrets=secrets)

    async def evaluate_improvement(self, baseline_results: List[Dict], optimized_results: List[Dict]) -> Dict:
        logger.info("Evaluating model refinement results...")
        if not baseline_results and not optimized_results:
            logger.warning("Evaluation: No results provided to evaluate.")
            return {"accuracy": 0.0, "tool_correctness": 0.0, "status": "failure", "reason": "Missing evaluation data"}
        return {"error": "Evaluation failed to capture data."}
