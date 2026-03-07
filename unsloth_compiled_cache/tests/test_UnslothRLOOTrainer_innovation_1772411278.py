import pytest

from unittest.mock import MagicMock, patch

from noogh_unified_system.src.unsloth_compiled_cache.UnslothRLOOTrainer import UnslothRLOOTrainer, RepeatSampler

class TestUnslothRLOOTrainer:

    @patch('noogh_unified_system.src.unsloth_compiled_cache.UnslothRLOOTrainer.RepeatSampler')
    def test_get_eval_sampler_happy_path(self, mock_repeat_sampler):
        # Arrange
        trainer = UnslothRLOOTrainer(args=MagicMock(), num_generations=5)
        eval_dataset = MagicMock()

        # Act
        result = trainer._get_eval_sampler(eval_dataset)

        # Assert
        mock_repeat_sampler.assert_called_once_with(
            data_source=eval_dataset,
            mini_repeat_count=trainer.num_generations,
            seed=trainer.args.seed,
        )
        assert isinstance(result, RepeatSampler)

    @patch('noogh_unified_system.src.unsloth_compiled_cache.UnslothRLOOTrainer.RepeatSampler')
    def test_get_eval_sampler_edge_case_none_dataset(self, mock_repeat_sampler):
        # Arrange
        trainer = UnslothRLOOTrainer(args=MagicMock(), num_generations=5)
        eval_dataset = None

        # Act
        result = trainer._get_eval_sampler(eval_dataset)

        # Assert
        mock_repeat_sampler.assert_not_called()
        assert result is None

    @patch('noogh_unified_system.src.unsloth_compiled_cache.UnslothRLOOTrainer.RepeatSampler')
    def test_get_eval_sampler_edge_case_empty_dataset(self, mock_repeat_sampler):
        # Arrange
        trainer = UnslothRLOOTrainer(args=MagicMock(), num_generations=5)
        eval_dataset = MagicMock(__len__=lambda self: 0)

        # Act
        result = trainer._get_eval_sampler(eval_dataset)

        # Assert
        mock_repeat_sampler.assert_not_called()
        assert result is None

    @patch('noogh_unified_system.src.unsloth_compiled_cache.UnslothRLOOTrainer.RepeatSampler')
    def test_get_eval_sampler_error_case_invalid_args(self, mock_repeat_sampler):
        # Arrange
        trainer = UnslothRLOOTrainer(args=None, num_generations=5)
        eval_dataset = MagicMock()

        # Act and Assert
        with pytest.raises(AttributeError):
            trainer._get_eval_sampler(eval_dataset)