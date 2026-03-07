import pytest
from neural_engine.nlp_processor import NLPProcessor

class TestTokenize:

    def setup_method(self):
        self.processor = NLPProcessor()

    @pytest.mark.parametrize("text, expected", [
        ("This is a test.", ["This", "is", "a", "test."]),
        ("One more example with punctuation!", ["One", "more", "example", "with", "punctuation!"]),
        ("Numbers 123 should be kept together.", ["Numbers", "123", "should", "be", "kept", "together."]),
    ])
    def test_happy_path(self, text, expected):
        result = self.processor.tokenize(text)
        assert result == expected

    @pytest.mark.parametrize("text, expected", [
        ("", []),
        (None, []),
        (" ", []),
        ("\t", []),
        ("\n", []),
        ("   ", []),
    ])
    def test_edge_cases(self, text, expected):
        result = self.processor.tokenize(text)
        assert result == expected

    @pytest.mark.parametrize("text, expected", [
        ([], None),
        (123, None),
        ({"key": "value"}, None),
        (True, None),
        (False, None),
    ])
    def test_error_cases(self, text, expected):
        result = self.processor.tokenize(text)
        assert result == expected

    @pytest.mark.asyncio
    async def test_async_behavior(self):
        with pytest.raises(NotImplementedError):
            await self.processor.tokenize("This should raise an error.")