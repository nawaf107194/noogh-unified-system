"""
Dataset Builder for Fine-tuning
Prepares training data for model fine-tuning
"""

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    """Single training example"""

    instruction: str
    response: str
    metadata: Optional[Dict[str, Any]] = None


class DatasetBuilder:
    """
    Builds and prepares datasets for fine-tuning
    Supports JSON, CSV, and TXT formats
    """

    def __init__(self):
        self.examples: List[TrainingExample] = []
        logger.info("DatasetBuilder initialized")

    def from_json(self, file_path: str) -> "DatasetBuilder":
        """
        Load dataset from JSON file

        Format:
        [
            {
                "instruction": "question or task",
                "response": "answer or completion",
                "metadata": {...}  # optional
            }
        ]
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            example = TrainingExample(
                instruction=item["instruction"], response=item["response"], metadata=item.get("metadata")
            )
            self.examples.append(example)

        logger.info(f"Loaded {len(self.examples)} examples from {file_path}")
        return self

    def from_csv(
        self, file_path: str, instruction_col: str = "instruction", response_col: str = "response"
    ) -> "DatasetBuilder":
        """Load dataset from CSV file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                example = TrainingExample(
                    instruction=row[instruction_col],
                    response=row[response_col],
                    metadata={k: v for k, v in row.items() if k not in [instruction_col, response_col]},
                )
                self.examples.append(example)

        logger.info(f"Loaded {len(self.examples)} examples from {file_path}")
        return self

    def from_text_pairs(self, file_path: str, separator: str = "###") -> "DatasetBuilder":
        """
        Load from text file with instruction-response pairs

        Format:
        instruction 1
        ###
        response 1

        instruction 2
        ###
        response 2
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        pairs = content.split("\n\n")
        for pair in pairs:
            if separator in pair:
                parts = pair.split(separator)
                if len(parts) == 2:
                    example = TrainingExample(instruction=parts[0].strip(), response=parts[1].strip())
                    self.examples.append(example)

        logger.info(f"Loaded {len(self.examples)} examples from {file_path}")
        return self

    def add_example(
        self, instruction: str, response: str, metadata: Optional[Dict[str, Any]] = None
    ) -> "DatasetBuilder":
        """Add a single example"""
        example = TrainingExample(instruction=instruction, response=response, metadata=metadata)
        self.examples.append(example)
        return self

    def split(self, train_ratio: float = 0.8) -> Tuple[List[TrainingExample], List[TrainingExample]]:
        """Split dataset into train and validation sets"""
        import random

        shuffled = self.examples.copy()
        random.shuffle(shuffled)

        split_idx = int(len(shuffled) * train_ratio)
        train_set = shuffled[:split_idx]
        val_set = shuffled[split_idx:]

        logger.info(f"Split: {len(train_set)} train, {len(val_set)} validation")
        return train_set, val_set

    def to_hf_dataset(self):
        """Convert to HuggingFace Dataset format"""
        try:
            from datasets import Dataset

            data_dict = {
                "instruction": [ex.instruction for ex in self.examples],
                "response": [ex.response for ex in self.examples],
            }

            dataset = Dataset.from_dict(data_dict)
            logger.info(f"Created HuggingFace dataset with {len(dataset)} examples")
            return dataset

        except ImportError:
            logger.error("datasets library not installed. Install with: pip install datasets")
            raise

    def format_for_training(self, template: str = None) -> List[str]:
        """
        Format examples for training

        Default template:
        ### Instruction:
        {instruction}

        ### Response:
        {response}
        """
        if template is None:
            template = """### Instruction:
{instruction}

### Response:
{response}"""

        formatted = []
        for ex in self.examples:
            text = template.format(instruction=ex.instruction, response=ex.response)
            formatted.append(text)

        return formatted

    def save_to_json(self, output_path: str):
        """Save dataset to JSON file"""
        data = [
            {"instruction": ex.instruction, "response": ex.response, "metadata": ex.metadata} for ex in self.examples
        ]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(data)} examples to {output_path}")

    def validate(self) -> Dict[str, Any]:
        """Validate dataset quality"""
        stats = {
            "total_examples": len(self.examples),
            "avg_instruction_length": 0,
            "avg_response_length": 0,
            "empty_instructions": 0,
            "empty_responses": 0,
            "very_short_responses": 0,  # < 10 chars
        }

        if not self.examples:
            return stats

        total_inst_len = 0
        total_resp_len = 0

        for ex in self.examples:
            inst_len = len(ex.instruction)
            resp_len = len(ex.response)

            total_inst_len += inst_len
            total_resp_len += resp_len

            if inst_len == 0:
                stats["empty_instructions"] += 1
            if resp_len == 0:
                stats["empty_responses"] += 1
            if resp_len < 10:
                stats["very_short_responses"] += 1

        stats["avg_instruction_length"] = total_inst_len / len(self.examples)
        stats["avg_response_length"] = total_resp_len / len(self.examples)

        logger.info(f"Dataset validation: {stats}")
        return stats

    def __len__(self) -> int:
        return len(self.examples)

    def __repr__(self) -> str:
        return f"DatasetBuilder({len(self.examples)} examples)"


# Example usage and helper functions
def create_sample_dataset(topic: str = "general") -> DatasetBuilder:
    """Create a sample dataset for testing"""
    builder = DatasetBuilder()

    if topic == "tech":
        samples = [
            ("ما هو Docker؟", "Docker هو منصة لتطوير ونشر التطبيقات في حاويات معزولة."),
            ("كيف أستخدم Git؟", "Git هو نظام لإدارة الإصدارات. استخدم git init لبدء مشروع جديد."),
            ("اشرح Kubernetes", "Kubernetes هو نظام لإدارة الحاويات على نطاق واسع."),
        ]
    elif topic == "science":
        samples = [
            ("ما هي نظرية النسبية؟", "نظرية النسبية لأينشتاين تصف العلاقة بين الزمان والمكان."),
            ("اشرح الجاذبية", "الجاذبية هي قوة تجذب الأجسام نحو بعضها البعض."),
        ]
    else:
        samples = [
            ("كيف أتعلم البرمجة؟", "ابدأ بلغة بسيطة مثل Python، ثم تدرب على حل المشاكل."),
            ("ما هو الذكاء الاصطناعي؟", "الذكاء الاصطناعي هو محاكاة الذكاء البشري بواسطة الآلات."),
        ]

    for instruction, response in samples:
        builder.add_example(instruction, response)

    return builder
