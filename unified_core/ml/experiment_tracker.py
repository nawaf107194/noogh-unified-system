"""
Weights & Biases Experiment Tracker

Tracks training experiments for reproducibility and comparison.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    logger.warning("wandb not installed. pip install wandb")


class ExperimentTracker:
    """Tracks ML experiments using Weights & Biases."""
    
    def __init__(
        self,
        project: str = "noogh-tool-selection",
        entity: Optional[str] = None,
        tags: Optional[List[str]] = None,
        offline: bool = False,
    ):
        self.project = project
        self.entity = entity
        self.tags = tags or []
        self.offline = offline
        self.run = None
        
        if not WANDB_AVAILABLE:
            logger.warning("W&B not available - logging disabled")
    
    def start_run(
        self,
        name: str,
        config: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> bool:
        """Start a new experiment run."""
        if not WANDB_AVAILABLE:
            return False
        
        try:
            self.run = wandb.init(
                project=self.project,
                entity=self.entity,
                name=name,
                config=config,
                tags=self.tags,
                notes=notes,
                mode="offline" if self.offline else "online",
            )
            logger.info(f"W&B run started: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to start W&B run: {e}")
            return False
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log training metrics."""
        if self.run:
            wandb.log(metrics, step=step)
    
    def log_hyperparameters(self, hparams: Dict[str, Any]):
        """Log hyperparameters."""
        if self.run:
            wandb.config.update(hparams)
    
    def log_artifact(
        self,
        name: str,
        artifact_type: str,
        path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a model or dataset artifact."""
        if not self.run:
            return
        
        artifact = wandb.Artifact(
            name=name,
            type=artifact_type,
            metadata=metadata,
        )
        artifact.add_dir(path)
        self.run.log_artifact(artifact)
        logger.info(f"Logged artifact: {name}")
    
    def log_dataset(self, name: str, path: str, version: str = "v1"):
        """Log a training dataset."""
        self.log_artifact(
            name=f"{name}-{version}",
            artifact_type="dataset",
            path=path,
            metadata={"version": version},
        )
    
    def log_model(self, name: str, path: str, metrics: Optional[Dict[str, float]] = None):
        """Log a trained model."""
        self.log_artifact(
            name=name,
            artifact_type="model",
            path=path,
            metadata={"final_metrics": metrics or {}},
        )
    
    def log_summary(self, summary: Dict[str, Any]):
        """Log run summary at the end."""
        if self.run:
            for key, value in summary.items():
                wandb.run.summary[key] = value
    
    def finish(self):
        """End the current run."""
        if self.run:
            wandb.finish()
            self.run = None
            logger.info("W&B run finished")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()


class LocalExperimentTracker:
    """Fallback tracker that logs locally when W&B is unavailable."""
    
    def __init__(self, log_dir: str = "experiments"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_run = None
        self.run_data = {}
    
    def start_run(self, name: str, config: Dict[str, Any], notes: Optional[str] = None):
        self.current_run = name
        self.run_data = {
            "name": name,
            "config": config,
            "notes": notes,
            "started_at": datetime.now().isoformat(),
            "metrics": [],
        }
        return True
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        self.run_data["metrics"].append({"step": step, **metrics})
    
    def log_hyperparameters(self, hparams: Dict[str, Any]):
        self.run_data["config"].update(hparams)
    
    def log_summary(self, summary: Dict[str, Any]):
        self.run_data["summary"] = summary
    
    def finish(self):
        if self.current_run:
            self.run_data["finished_at"] = datetime.now().isoformat()
            log_file = self.log_dir / f"{self.current_run}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, "w") as f:
                json.dump(self.run_data, f, indent=2)
            logger.info(f"Experiment logged to: {log_file}")
            self.current_run = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()


def get_tracker(use_wandb: bool = True, **kwargs) -> ExperimentTracker:
    """Get the appropriate experiment tracker."""
    if use_wandb and WANDB_AVAILABLE:
        return ExperimentTracker(**kwargs)
    else:
        return LocalExperimentTracker(**kwargs)
