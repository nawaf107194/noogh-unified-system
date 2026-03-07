import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from datasets import Dataset, load_dataset
from huggingface_hub import HfApi

logger = logging.getLogger("ml.data")


class HFDataManager:
    """Manager for loading and handling datasets from HuggingFace Hub."""

    def __init__(self, data_dir: str):
        if not data_dir:
            raise ValueError("data_dir is required for HFDataManager")
        self.cache_dir = Path(data_dir) / "hf_datasets"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api = HfApi()
        self.loaded_datasets = {}

    def load_dataset(
        self,
        dataset_name: str,
        config_name: Optional[str] = None,
        split: str = "train",
        use_auth_token: Optional[str] = None,
        streaming: bool = False,
    ) -> Dataset:
        cache_key = f"{dataset_name}_{config_name}_{split}"
        if cache_key in self.loaded_datasets:
            return self.loaded_datasets[cache_key]

        try:
            logger.info(f"Loading dataset: {dataset_name} (config: {config_name})")
            kwargs = {
                "path": dataset_name,
                "name": config_name,
                "cache_dir": str(self.cache_dir / dataset_name.replace("/", "_")),
                "streaming": streaming,
            }
            if use_auth_token:
                kwargs["token"] = use_auth_token

            if split:
                try:
                    dataset = load_dataset(**kwargs, split=split)
                except Exception as split_error:
                    logger.warning(f"Split '{split}' failed, attempting auto-detection.")
                    from datasets import get_dataset_split_names

                    available_splits = get_dataset_split_names(dataset_name, config_name)
                    if available_splits:
                        fallback = "train" if "train" in available_splits else (available_splits[0])
                        dataset = load_dataset(**kwargs, split=fallback)
                    else:
                        raise split_error
            else:
                dataset = load_dataset(**kwargs)

            self.loaded_datasets[cache_key] = dataset
            return dataset
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise

    def search_datasets(self, query: str, limit: int = 10) -> List[Dict]:
            if not query.strip():
                logger.warning("Empty query received, returning default")
                return []

            try:
                datasets = self.api.list_datasets(search=query, limit=limit, full=False)
                results = []
                for ds in datasets:
                    description = getattr(ds, "description", "") or "No description"
                    tags = getattr(ds, "tags", [])
                    last_modified = getattr(ds, "lastModified", None)
                    results.append(
                        {
                            "id": ds.id,
                            "description": f"{description[:200]}...",
                            "downloads": getattr(ds, "downloads", 0),
                            "likes": getattr(ds, "likes", 0),
                            "tags": tags[:5] if tags else [],
                            "author": getattr(ds, "author", None),
                            "last_modified": last_modified.isoformat() if last_modified else None,
                        }
                    )
                return results
            except Exception as e:
                logger.error(f"Dataset search failed: {e}")
                return []

    def prepare_training_data(
        self,
        dataset: Dataset,
        text_column: str = "text",
        label_column: Optional[str] = None,
        max_samples: Optional[int] = None,
    ) -> Dict:
        total_samples = len(dataset)
        columns = dataset.column_names
        sample_data = {}
        if total_samples > 0:
            sample = dataset[0]
            for key in list(sample.keys())[:3]:
                if isinstance(sample[key], (str, int, float)):
                    sample_data[key] = str(sample[key])[:100]

        task_type = self._infer_task_type(dataset, label_column)
        return {
            "success": True,
            "task_type": task_type,
            "stats": {"total_samples": total_samples, "columns": columns, "sample_data": sample_data},
        }

    def _infer_task_type(self, dataset: Dataset, label_column: Optional[str]) -> str:
        if not label_column:
            return "text_generation"
        try:
            sample = dataset[0]
            label = sample.get(label_column)
            if isinstance(label, (int, float)):
                subset = dataset.select(range(min(100, len(dataset))))
                unique_labels = set(subset[label_column])
                return "classification" if len(unique_labels) <= 20 else "regression"
            elif isinstance(label, str):
                return "sequence_classification"
            elif isinstance(label, list):
                return "multi_label_classification"
        except Exception:
            pass
        return "text_generation"

    def create_custom_dataset(self, data: List[Dict], dataset_name: str) -> str:
        try:
            df = pd.DataFrame(data)
            dataset = Dataset.from_pandas(df)
            local_path = self.cache_dir / f"custom_{dataset_name}"
            dataset.save_to_disk(str(local_path))
            return str(local_path)
        except Exception as e:
            logger.error(f"Failed to create custom dataset: {e}")
            raise
