import pytest

from unsloth_compiled_cache.UnslothPPOTrainer import UnslothPPOTrainer, null_ref_context
from unittest.mock import MagicMock, patch

@pytest.fixture
def trainer():
    return UnslothPPOTrainer(
        model=MagicMock(),
        accelerator=MagicMock(),
        is_peft_model=True,
        ref_adapter_name=None,
        model_adapter_name="default"
    )

@patch('unsloth_compiled_cache.UnslothPPOTrainer.nullcontext')
def test_null_ref_context_happy_path(mock_nullcontext, trainer):
    with null_ref_context() as ctx:
        mock_nullcontext.assert_called_once()
        assert ctx == nullcontext()

@patch('unsloth_compiled_cache.UnslothPPOTrainer.nullcontext')
def test_null_ref_context_with_adapter(mock_nullcontext, trainer):
    trainer.ref_adapter_name = "adapter1"
    with null_ref_context() as ctx:
        mock_nullcontext.assert_called_once()
        assert ctx == nullcontext()
        trainer.model.policy.set_adapter.assert_called_once_with("adapter1")
    trainer.model.policy.set_adapter.assert_called_with(trainer.model_adapter_name or "default")

def test_null_ref_context_unwrap_model_failure(trainer):
    trainer.accelerator.unwrap_model.side_effect = ValueError
    with pytest.raises(ValueError):
        null_ref_context()

def test_null_ref_context_no_ref_adapter(trainer):
    trainer.ref_adapter_name = None
    with null_ref_context() as ctx:
        assert ctx == nullcontext()
        trainer.model.policy.set_adapter.assert_not_called()

def test_null_ref_context_invalid_model(trainer):
    trainer.model = None
    with pytest.raises(AttributeError):
        null_ref_context()