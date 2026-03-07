import pytest
from unittest.mock import patch, MagicMock
import torch
from noogh_unified_system.src.train_cloud import train
from noogh_unified_system.src.utils.logger import logger

# Mocking functions for testing
@patch('noogh_unified_system.src.train_cloud.load_model_for_training')
@patch('noogh_unified_system.src.train_cloud.load_and_score_dataset')
@patch('noogh_unified_system.src.train_cloud.SFTConfig')
@patch('noogh_unified_system.src.train_cloud.SFTTrainer')
def test_train_happy_path(SFTTrainerMock, SFTConfigMock, load_and_score_datasetMock, load_model_for_trainingMock):
    # Mock inputs
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_train_ds = MagicMock()
    mock_eval_ds = MagicMock()
    
    # Set up mocks
    load_model_for_trainingMock.return_value = (mock_model, mock_tokenizer)
    load_and_score_datasetMock.return_value = {"train": mock_train_ds, "test": mock_eval_ds}
    SFTConfigMock.return_value = MagicMock()
    SFTTrainerMock.return_value.train.return_value = {"training_loss": 0.1234, "metrics": {"train_runtime": 123}}
    
    # Call the function
    result = train()
    
    # Assertions
    assert result == {"training_loss": 0.1234, "metrics": {"train_runtime": 123}}
    load_model_for_trainingMock.assert_called_once()
    load_and_score_datasetMock.assert_called_once()
    SFTConfigMock.assert_called_once_with(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        warmup_ratio=WARMUP_RATIO,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        bf16=True,                 # A100 supports bf16 natively
        logging_steps=50,
        save_strategy="steps",
        save_steps=1000,
        save_total_limit=3,
        eval_strategy="steps",
        eval_steps=1000,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_grad_norm=0.3,
        dataloader_pin_memory=True,
        max_length=MAX_SEQ_LENGTH,
        dataset_text_field="text",
        packing=True,              
    )
    SFTTrainerMock.assert_called_once_with(
        model=mock_model,
        processing_class=mock_tokenizer,
        train_dataset=mock_train_ds,
        eval_dataset=mock_eval_ds,
        args=SFTConfigMock.return_value,
    )
    mock_model.save_pretrained.assert_called_once_with(str(LORA_OUTPUT))
    mock_tokenizer.save_pretrained.assert_called_once_with(str(LORA_OUTPUT))
    
@patch('noogh_unified_system.src.train_cloud.load_model_for_training')
@patch('noogh_unified_system.src.train_cloud.load_and_score_dataset')
def test_train_gpu_not_available(load_and_score_datasetMock, load_model_for_trainingMock):
    # Mock inputs
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    
    # Set up mocks
    load_model_for_trainingMock.return_value = (mock_model, mock_tokenizer)
    load_and_score_datasetMock.return_value = {"train": [], "test": []}
    
    # Patch torch.cuda.is_available to return False
    with patch('torch.cuda.is_available', return_value=False):
        result = train()
        
    assert result is None
    logger.error.assert_called_once_with("❌ No GPU available!")
    
@patch('noogh_unified_system.src.train_cloud.load_model_for_training')
@patch('noogh_unified_system.src.train_cloud.load_and_score_dataset')
def test_train_empty_dataset(load_and_score_datasetMock, load_model_for_trainingMock):
    # Mock inputs
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    
    # Set up mocks
    load_model_for_trainingMock.return_value = (mock_model, mock_tokenizer)
    load_and_score_datasetMock.return_value = {"train": [], "test": []}
    
    # Call the function
    result = train()
    
    assert result is None
    logger.error.assert_called_once_with("❌ No data available!")
    
# Add more tests for edge cases and error scenarios as needed