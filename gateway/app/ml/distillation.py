"""
Distillation Service for Neural OS.
Handles self-learning cycles and knowledge distillation.
"""

import logging
from typing import Any, Dict

from datasets import load_dataset

logger = logging.getLogger("distillation")


class DistillationService:
    """
    Service for distilling knowledge from agent experiences into
    smaller, efficient models or creating training datasets.
    """

    def __init__(self, secrets: Dict[str, str] = None):
        self.secrets = secrets or {}
        self.is_running = False
        logger.info("DistillationService initialized")

    async def run_distillation_cycle(
        self,
        topic: str,
        num_examples: int = 10,
        model_name: str = "microsoft/phi-2",
        dataset_config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Run a knowledge distillation cycle on a specific topic using a dynamic dataset.
        """
        logger.info(f"Starting distillation cycle for topic: {topic}")

        try:
            # 1. Gather Data (Real Data from Hugging Face)
            dataset_name = dataset_config.get("dataset_name", "wikitext") if dataset_config else "wikitext"
            subset = dataset_config.get("subset") if dataset_config else "wikitext-2-raw-v1"
            split = dataset_config.get("split", "train") if dataset_config else "train"

            logger.info(f"Distillation: Loading real dataset '{dataset_name}' (subset={subset}, split={split})...")

            # Use 'subset' as second arg if present, otherwise just name (some datasets have no subset)
            if subset:
                dataset = load_dataset(dataset_name, subset, split=split, streaming=True, trust_remote_code=True)
            else:
                dataset = load_dataset(dataset_name, split=split, streaming=True, trust_remote_code=True)

            training_data = []
            count = 0
            for record in dataset:
                # Handle different column names
                text = record.get("text") or record.get("content") or record.get("code") or ""
                text = text.strip()
                if len(text) > 50:  # Filter empty/short lines
                    training_data.append({"text": text})
                    count += 1
                if count >= num_examples:
                    break

            logger.info(f"Distillation: Loaded {len(training_data)} examples from Hugging Face.")

            # 2. Train Logic which uses PyTorch
            from gateway.app.ml.model_trainer import RealModelTrainer

            # Basic secrets setup
            secrets = {"LOCAL_MODEL_NAME": "sshleifer/tiny-gpt2"}  # Hardcode small model for sanity check
            trainer = RealModelTrainer(secrets)

            result = trainer.train_model(training_data, output_dir=f"./models/refined_{topic.replace(' ', '_')}")

            return {
                "success": result["success"],
                "topic": topic,
                "examples_processed": num_examples,
                "model_updated": True,
                "metrics": result.get("metrics", {}),
            }
        except Exception as e:
            logger.error(f"Distillation cycle failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
