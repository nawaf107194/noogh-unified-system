import pytest
from unittest.mock import MagicMock, patch

from unsloth_compiled_cache.UnslothXPOTrainer import UnslothXPOTrainer

@pytest.fixture
def trainer():
    return UnslothXPOTrainer(generation_config=MagicMock())

@patch('unsloth_compiled_cache.UnslothXPOTrainer.unwrap_model_for_generation')
@patch('unsloth_compiled_cache.UnslothXPOTrainer.accelerator.unwrap_model')
def test_generate_completions_happy_path(mock_unwrap_ref, mock_unwrap_gen, trainer):
    prompts = {
        "input_ids": MagicMock(),
        "attention_mask": MagicMock()
    }
    
    model_mock = MagicMock()
    unwrapped_policy_model_for_gen = MagicMock()
    unwrapped_main_model_for_ref_logic = MagicMock()
    
    mock_unwrap_gen.return_value = unwrapped_policy_model_for_gen
    mock_unwrap_ref.return_value = unwrapped_main_model_for_ref_logic
    
    trainer._generate_completions(prompts, model_mock)
    
    unwrapped_policy_model_for_gen.generate.assert_called_once_with(
        input_ids=prompts["input_ids"],
        attention_mask=prompts["attention_mask"],
        generation_config=trainer.generation_config,
    )
    
    unwrapped_main_model_for_ref_logic.generate.assert_called_once_with(
        input_ids=prompts["input_ids"],
        attention_mask=prompts["attention_mask"],
        generation_config=trainer.generation_config,
    )

@patch('unsloth_compiled_cache.UnslothXPOTrainer.unwrap_model_for_generation')
@patch('unsloth_compiled_cache.UnslothXPOTrainer.accelerator.unwrap_model')
def test_generate_completions_empty_prompts(mock_unwrap_ref, mock_unwrap_gen, trainer):
    prompts = {
        "input_ids": None,
        "attention_mask": None
    }
    
    model_mock = MagicMock()
    
    with pytest.raises(ValueError) as exc_info:
        trainer._generate_completions(prompts, model_mock)
        
    assert str(exc_info.value) == "Prompts cannot be None"

@patch('unsloth_compiled_cache.UnslothXPOTrainer.unwrap_model_for_generation')
@patch('unsloth_compiled_cache.UnslothXPOTrainer.accelerator.unwrap_model')
def test_generate_completions_ref_model_none(mock_unwrap_ref, mock_unwrap_gen, trainer):
    prompts = {
        "input_ids": MagicMock(),
        "attention_mask": MagicMock()
    }
    
    model_mock = MagicMock()
    unwrapped_policy_model_for_gen = MagicMock()
    unwrapped_main_model_for_ref_logic = MagicMock()
    
    mock_unwrap_gen.return_value = unwrapped_policy_model_for_gen
    mock_unwrap_ref.return_value = unwrapped_main_model_for_ref_logic
    
    trainer.ref_model = None
    
    model_output, ref_output = trainer._generate_completions(prompts, model_mock)
    
    assert model_output is not None
    assert ref_output is not None