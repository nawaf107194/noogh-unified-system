"""
Model Trainer with LoRA/QLoRA Support
Efficient fine-tuning for HuggingFace models
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import torch

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Training configuration"""

    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    warmup_steps: int = 100
    max_length: int = 512
    save_steps: int = 100
    logging_steps: int = 10
    eval_steps: int = 50


@dataclass
class LoRAConfig:
    """LoRA configuration"""

    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = None

    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]


class ModelTrainer:
    """
    Fine-tune models using LoRA/QLoRA
    Supports HuggingFace transformers
    """

    def __init__(
        self,
        base_model: str = "mistralai/Mistral-7B-v0.1",
        use_lora: bool = True,
        use_qlora: bool = False,
        lora_config: Optional[LoRAConfig] = None,
        training_config: Optional[TrainingConfig] = None,
    ):
        """
        Initialize trainer

        Args:
            base_model: HuggingFace model name
            use_lora: Use LoRA for efficient training
            use_qlora: Use QLoRA (4-bit quantization + LoRA)
            lora_config: LoRA configuration
            training_config: Training configuration
        """
        self.base_model = base_model
        self.use_lora = use_lora
        self.use_qlora = use_qlora
        self.lora_config = lora_config or LoRAConfig()
        self.training_config = training_config or TrainingConfig()

        self.model = None
        self.tokenizer = None
        self.trainer = None

        logger.info(f"ModelTrainer initialized for {base_model}")
        logger.info(f"LoRA: {use_lora}, QLoRA: {use_qlora}")

    def load_model(self):
        """Load base model and tokenizer"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

            logger.info(f"Loading model: {self.base_model}")

            # Tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Model loading config
            if self.use_qlora:
                # 4-bit quantization for QLoRA
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.base_model, quantization_config=bnb_config, device_map="auto", trust_remote_code=True
                )
                logger.info("Loaded model with 4-bit quantization (QLoRA)")
            else:
                # Regular loading
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.base_model, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
                )
                logger.info("Loaded model in FP16")

            # Apply LoRA if enabled
            if self.use_lora or self.use_qlora:
                self._apply_lora()

            return self.model, self.tokenizer

        except ImportError as e:
            logger.error(f"Missing dependencies: {e}")
            logger.error("Install with: pip install transformers peft bitsandbytes accelerate")
            raise

    def _apply_lora(self):
        """Apply LoRA to the model"""
        try:
            from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

            # Prepare model for k-bit training if using QLoRA
            if self.use_qlora:
                self.model = prepare_model_for_kbit_training(self.model)

            # LoRA config
            peft_config = LoraConfig(
                r=self.lora_config.r,
                lora_alpha=self.lora_config.lora_alpha,
                lora_dropout=self.lora_config.lora_dropout,
                target_modules=self.lora_config.target_modules,
                bias="none",
                task_type="CAUSAL_LM",
            )

            # Apply LoRA
            self.model = get_peft_model(self.model, peft_config)
            self.model.print_trainable_parameters()

            logger.info("LoRA applied successfully")

        except ImportError:
            logger.error("peft library not installed. Install with: pip install peft")
            raise

    def prepare_dataset(self, dataset, template: str = None):
        """
        Prepare dataset for training

        Args:
            dataset: HuggingFace dataset or list of examples
            template: Formatting template
        """
        if template is None:
            template = """### Instruction:
{instruction}

### Response:
{response}"""

        def format_example(example):
            text = template.format(instruction=example["instruction"], response=example["response"])
            return self.tokenizer(
                text, truncation=True, max_length=self.training_config.max_length, padding="max_length"
            )

        if hasattr(dataset, "map"):
            # HuggingFace dataset
            tokenized = dataset.map(format_example, remove_columns=dataset.column_names)
        else:
            # List of examples
            from datasets import Dataset

            dataset = Dataset.from_list(dataset)
            tokenized = dataset.map(format_example, remove_columns=dataset.column_names)

        logger.info(f"Prepared {len(tokenized)} examples for training")
        return tokenized

    def train(self, train_dataset, eval_dataset=None, output_dir: str = "./models/finetuned", **kwargs):
        """
        Train the model

        Args:
            train_dataset: Training dataset
            eval_dataset: Evaluation dataset (optional)
            output_dir: Output directory for checkpoints
            **kwargs: Additional training arguments
        """
        try:
            from transformers import DataCollatorForLanguageModeling, Trainer, TrainingArguments

            if self.model is None:
                self.load_model()

            # Prepare datasets
            train_data = self.prepare_dataset(train_dataset)
            eval_data = self.prepare_dataset(eval_dataset) if eval_dataset else None

            # Training arguments
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=self.training_config.num_epochs,
                per_device_train_batch_size=self.training_config.batch_size,
                gradient_accumulation_steps=self.training_config.gradient_accumulation_steps,
                learning_rate=self.training_config.learning_rate,
                warmup_steps=self.training_config.warmup_steps,
                logging_steps=self.training_config.logging_steps,
                save_steps=self.training_config.save_steps,
                eval_steps=self.training_config.eval_steps if eval_data else None,
                evaluation_strategy="steps" if eval_data else "no",
                save_total_limit=3,
                fp16=True,
                optim="paged_adamw_8bit" if self.use_qlora else "adamw_torch",
                report_to="none",
                **kwargs,
            )

            # Data collator
            data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=False)

            # Trainer
            self.trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_data,
                eval_dataset=eval_data,
                data_collator=data_collator,
            )

            # Train
            logger.info("Starting training...")
            self.trainer.train()

            # Save final model
            self.save_model(output_dir)

            logger.info(f"Training complete! Model saved to {output_dir}")

        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            raise

    def save_model(self, output_dir: str):
            """Save the trained model"""
            if not isinstance(output_dir, str):
                raise TypeError("The 'output_dir' parameter must be a string.")
        
            if not output_dir:
                raise ValueError("The 'output_dir' parameter cannot be an empty string.")

            try:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise RuntimeError(f"Failed to create directory '{output_dir}': {e}") from e

            if self.use_lora or self.use_qlora:
                # Save LoRA adapters
                try:
                    self.model.save_pretrained(output_dir)
                    self.tokenizer.save_pretrained(output_dir)
                    logger.info(f"Saved LoRA adapters to {output_dir}")
                except Exception as e:
                    logger.error(f"Failed to save LoRA adapters to {output_dir}: {e}")
                    raise RuntimeError(f"Failed to save LoRA adapters to {output_dir}.") from e
            else:
                # Save full model
                try:
                    self.model.save_pretrained(output_dir)
                    self.tokenizer.save_pretrained(output_dir)
                    logger.info(f"Saved full model to {output_dir}")
                except Exception as e:
                    logger.error(f"Failed to save full model to {output_dir}: {e}")
                    raise RuntimeError(f"Failed to save full model to {output_dir}.") from e

    def load_trained_model(self, model_path: str):
        """Load a trained model"""
        try:
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading trained model from {model_path}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)

            if self.use_lora or self.use_qlora:
                # Load base model + LoRA adapters
                base_model = AutoModelForCausalLM.from_pretrained(
                    self.base_model, torch_dtype=torch.float16, device_map="auto"
                )
                self.model = PeftModel.from_pretrained(base_model, model_path)
                logger.info("Loaded model with LoRA adapters")
            else:
                # Load full model
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path, torch_dtype=torch.float16, device_map="auto"
                )
                logger.info("Loaded full model")

            return self.model, self.tokenizer

        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise

    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        """Generate text using the trained model"""
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not loaded. Call load_model() or load_trained_model() first")

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove prompt from response
        if prompt in response:
            response = response.replace(prompt, "").strip()

        return response
