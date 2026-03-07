import hashlib
import logging
import os
from typing import Any, Dict, List

import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

logger = logging.getLogger("model_trainer")


class RealModelTrainer:
    """
    Handles ACTUAL fine-tuning of LLMs using PyTorch and Transformers.
    No simulations.
    """

    def __init__(self, secrets: Dict[str, str]):
            self.secrets = secrets
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.refined_path = "./refined_model"

            config_path = os.path.join(self.refined_path, "config.json")
            if os.path.exists(config_path):
                self.model_name = self.refined_path
                logger.info(f"RealModelTrainer: Found existing refined model at {self.refined_path}. Loading it.")
            else:
                self.model_name = secrets.get("LOCAL_MODEL_NAME", "sshleifer/tiny-gpt2")
                logger.info(f"RealModelTrainer: No refined model found. Starting fresh with {self.model_name}")

            logger.info(f"RealModelTrainer initialized on {self.device}")

    def _get_model_hash(self, model):
        """Calculate SHA256 hash of the embedding weights."""
        try:
            # Try specific layer for GPT2/Tiny
            w = model.transformer.wte.weight.detach().cpu().numpy().tobytes()
            return hashlib.sha256(w).hexdigest()
        except Exception:
            # Fallback for generic
            return "unknown_hash"

    def train_model(self, data: List[Dict[str, str]], output_dir: str = "./refined_model") -> Dict[str, Any]:
        """
        Fine-tune the model on the provided data.
        """
        logger.info("Starting ACTUAL training cycle...")

        try:
            # 1. Load Model & Tokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)

            # 1.5 PROOF: Log Weight Hash BEFORE
            hash_before = self._get_model_hash(model)
            logger.info(f"HASH_BEFORE: {hash_before}")

            # Ensure pad token exists
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # 2. Prepare Dataset
            dataset = Dataset.from_list(data)

            def tokenize_function(examples):
                return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

            tokenized_datasets = dataset.map(tokenize_function, batched=True)

            # 3. Training Arguments
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=1,  # Keep it fast for now
                per_device_train_batch_size=1,
                logging_steps=1,
                save_steps=100,
                learning_rate=5e-5,
                weight_decay=0.01,
                no_cuda=False if self.device == "cuda" else True,
                report_to="none",  # Disable wandb/tensorboard for internal use
            )

            # 4. Trainer
            data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_datasets,
                data_collator=data_collator,
            )

            # 5. Train
            result = trainer.train()

            # 6. Save
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)

            # 6.5 PROOF: Log Weight Hash AFTER
            hash_after = self._get_model_hash(model)
            logger.info(f"HASH_AFTER:  {hash_after}")

            if hash_before != hash_after:
                logger.info("SUCCESS: Weights have changed! Learning occurred.")
            else:
                logger.warning("WARNING: Weights identical. Training may have been ineffective (LR too low?).")

            logger.info(f"Training complete. Loss: {result.training_loss}")

            return {
                "success": True,
                "training_loss": result.training_loss,
                "global_step": result.global_step,
                "metrics": result.metrics,
            }

        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
