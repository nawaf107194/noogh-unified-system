import pytest

from src.train_gemma3n import score_format, RewardScorer

class TestScoreFormat:

    def test_happy_path(self):
        text = "This is a well-formatted response with multiple\n\nparagraphs and