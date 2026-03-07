import json
import time
from pathlib import Path
from typing import Dict, List

import yaml

from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.logging import get_logger
from gateway.app.llm.remote_brain import RemoteBrainService

logger = get_logger("training_harness")


class TrainingHarness:
    """
    Executes a dataset of tasks and produces a performance report.
    """

    def __init__(self, dataset_path: str = None, dataset: List[Dict] = None, output_path: str = "training_report.json"):
        if dataset_path:
            self.dataset_path = Path(dataset_path)
            self.dataset = None
        else:
            self.dataset_path = None
            self.dataset = dataset

        self.output_path = Path(output_path)
        self.results = []

    def __init__(self, dataset=None, dataset_path=None):
        self.dataset = dataset
        self.dataset_path = dataset_path

    def load_dataset(self) -> List[Dict]:
        if not isinstance(self.dataset_path, str):
            raise TypeError("dataset_path must be a string")

        if self.dataset:
            if not isinstance(self.dataset, list) or not all(isinstance(item, dict) for item in self.dataset):
                raise TypeError("dataset must be a list of dictionaries")
            return self.dataset

        supported_formats = ['.json', '.yaml', '.yml']
        if not any(self.dataset_path.endswith(ext) for ext in supported_formats):
            raise ValueError(f"Unsupported dataset format: {self.dataset_path}")

        try:
            with open(self.dataset_path, "r") as file:
                if self.dataset_path.endswith(".json"):
                    data = json.load(file)
                elif self.dataset_path.endswith((".yaml", ".yml")):
                    data = yaml.safe_load(file)

                if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                    raise ValueError("Loaded dataset is not a list of dictionaries")

                return data
        except FileNotFoundError:
            logger.error(f"File not found: {self.dataset_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from: {self.dataset_path}")
            raise
        except yaml.YAMLError:
            logger.error(f"Failed to decode YAML from: {self.dataset_path}")
            raise

    def run(self, kernel: AgentKernel) -> List[Dict]:
        dataset = self.load_dataset()
        logger.info(f"Loaded {len(dataset)} tasks")
        if self.dataset_path:
            logger.info(f"Source: {self.dataset_path}")

        start_time = time.time()
        for i, item in enumerate(dataset):
            task = item.get("task")
            expected = item.get("expected")
            logger.info(f"Running task {i+1}/{len(dataset)}: {task[:50]}...")

            # Reset kernel for each task
            kernel.reset()

            task_start = time.time()
            result = kernel.process(task)
            duration = (time.time() - task_start) * 1000

            self.results.append(
                {
                    "index": i,
                    "task": task,
                    "expected": expected,
                    "success": result.success,
                    "answer": result.answer,
                    "steps": result.steps,
                    "error": result.error,
                    "duration_ms": duration,
                }
            )

        total_duration = time.time() - start_time
        self.save_report(total_duration)
        return self.results

    def save_report(self, total_duration: float):
        success_count = sum(1 for r in self.results if r["success"])
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_tasks": len(self.results),
            "success_rate": success_count / len(self.results) if self.results else 0,
            "total_duration_s": total_duration,
            "average_duration_ms": (total_duration * 1000) / len(self.results) if self.results else 0,
            "results": self.results,
        }

        with open(self.output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Training report saved to {self.output_path}")
        print("\nHARNESS SUMMARY:")
        print(f"Tasks: {len(self.results)}")
        print(f"Success Rate: {report['success_rate']:.2%}")
        print(f"Total Duration: {total_duration:.2f}s")


if __name__ == "__main__":
    # Example usage
    # python3 -m noogh.app.tools.training_harness dataset.json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m noogh.app.tools.training_harness <dataset_path>")
        sys.exit(1)

    dataset = sys.argv[1]
    brain = RemoteBrainService()
    kernel = AgentKernel(brain=brain, strict_protocol=True, sandbox_service=get_sandbox_service())
    harness = TrainingHarness(dataset)
    harness.run(kernel)
