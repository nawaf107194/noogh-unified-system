import logging
from typing import Dict, Optional

try:
    from .experiment_manager import ExperimentManager
except ImportError:
    ExperimentManager = None
from .hf_data_manager import HFDataManager
try:
    from .model_trainer import RealModelTrainer as ModelTrainer
except ImportError:
    ModelTrainer = None

logger = logging.getLogger("ml.tools")


class MLTools:
    """Agent tools for Machine Learning tasks."""

    def __init__(self, data_dir: str):
        if not data_dir:
            data_dir = "."
        self.data_dir = data_dir

    def load_and_analyze_dataset(self, dataset_name: str, config: Optional[Dict] = None) -> Dict:
        """Tool: Load and analyze a dataset from HuggingFace."""
        try:
            mgr = HFDataManager(data_dir=self.data_dir)
            cfg_name = config.get("config_name") if config else None
            split = config.get("split", "train") if config else "train"

            dataset = mgr.load_dataset(dataset_name, config_name=cfg_name, split=split)
            analysis = mgr.prepare_training_data(
                dataset,
                text_column=config.get("text_column", "text") if config else "text",
                label_column=config.get("label_column") if config else None,
            )
            return {"success": True, "dataset_name": dataset_name, "rows": len(dataset), "analysis": analysis}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def train_text_classifier(
        self, dataset_name: str, model_name: str = "distilbert-base-uncased", config: Optional[Dict] = None
    ) -> Dict:
        """Tool: Train a text classifier."""
        try:
            mgr = HFDataManager(data_dir=self.data_dir)
            dataset = mgr.load_dataset(dataset_name, split="train")

            trainer = ModelTrainer(data_dir=self.data_dir)
            result = trainer.train_classification_model(
                dataset=dataset,
                model_name=model_name,
                text_column=config.get("text_column", "text") if config else "text",
                label_column=config.get("label_column", "label") if config else "label",
                config=config.get("training_config") if config else None,
            )

            if result["success"]:
                expm = ExperimentManager(data_dir=self.data_dir)
                eid = expm.create_experiment(f"train_{dataset_name}")
                expm.log_training_run(
                    experiment_id=eid,
                    run_name=f"run_{model_name}",
                    parameters={"model": model_name, "dataset": dataset_name},
                    metrics=result["metrics"],
                    artifacts={"model": result["model_path"]},
                    model_info={"task_type": "classification", "model_name": model_name},
                )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_datasets(self, query: str) -> Dict:
            """Tool: Search HuggingFace Hub."""
            if not query.strip():
                logger.warning("Empty query received, returning default")
                return {"success": False, "error": "Empty query"}

            try:
                mgr = HFDataManager(data_dir=self.data_dir)
                results = mgr.search_datasets(query)
                return {"success": True, "results": results}
            except Exception as e:
                logger.error(f"Error searching datasets: {e}")
                return {"success": False, "error": str(e)}
