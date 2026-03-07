import pytest

class TestWeighImportance:
    @pytest.fixture
    def setup_attention_mechanism(self):
        class MockAttentionMechanism:
            def __init__(self, urgent_keywords):
                self.urgent_keywords = urgent_keywords

            def weigh_importance(self, input_data: dict) -> dict:
                score = 0.5
                text_content = input_data.get("content", "")
                if not text_content:
                    return input_data
                if any(kw in text_content.lower() for kw in self.urgent_keywords):
                    score = 0.9
                input_data["attention_score"] = score
                return input_data

        return MockAttentionMechanism(["emergency", "urgent"])

    def test_happy_path(self, setup_attention_mechanism):
        input_data = {"content": "This is an urgent message"}
        result = setup_attention_mechanism.weigh_importance(input_data)
        assert result == {"content": "This is an urgent message", "attention_score": 0.9}

    def test_empty_content(self, setup_attention_mechanism):
        input_data = {"content": ""}
        result = setup_attention_mechanism.weigh_importance(input_data)
        assert result == {"content": "", "attention_score": 0.5}

    def test_none_content(self, setup_attention_mechanism):
        input_data = {"content": None}
        result = setup_attention_mechanism.weigh_importance(input_data)
        assert result == {"content": None, "attention_score": 0.5}

    def test_no_content_key(self, setup_attention_mechanism):
        input_data = {}
        result = setup_attention_mechanism.weigh_importance(input_data)
        assert result == {}

    def test_invalid_input_type(self, setup_attention_mechanism):
        with pytest.raises(TypeError):
            setup_attention_mechanism.weigh_importance(123)

    def test_non_string_content(self, setup_attention_mechanism):
        input_data = {"content": 123}
        result = setup_attention_mechanism.weigh_importance(input_data)
        assert result == {"content": 123, "attention_score": 0.5}

    def test_case_insensitivity(self, setup_attention_mechanism):
        input_data = {"content": "URGENT MESSAGE"}
        result = setup_attention_mechanism.weigh_importance(input_data)
        assert result == {"content": "URGENT MESSAGE", "attention_score": 0.9}

    def test_multiple_urgent_keywords(self, setup_attention_mechanism):
        input_data = {"content": "Emergency situation, very urgent!"}
        result = setup_attention_mechanism.weigh_importance(input_data)
        assert result == {"content": "Emergency situation, very urgent!", "attention_score": 0.9}