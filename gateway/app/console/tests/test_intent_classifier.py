import pytest
from typing import List
from gateway.app.console.intent_classifier import add_custom_rule, IntentRule, INTENT_RULES

class TestAddCustomRule:

    @pytest.fixture(autouse=True)
    def clear_rules(self):
        INTENT_RULES.clear()

    def test_happy_path(self):
        # Normal inputs
        add_custom_rule("test_mode", ["hello", "world"], 50, "Test Rule")
        assert len(INTENT_RULES) == 1
        assert INTENT_RULES[0].mode == "test_mode"
        assert INTENT_RULES[0].keywords == ["hello", "world"]
        assert INTENT_RULES[0].priority == 50
        assert INTENT_RULES[0].description == "Test Rule"

    def test_empty_keywords(self):
        # Empty list of keywords
        add_custom_rule("test_mode", [], 50, "Empty Keywords")
        assert len(INTENT_RULES) == 1
        assert INTENT_RULES[0].keywords == []

    def test_none_keywords(self):
        # None as keywords
        with pytest.raises(TypeError):
            add_custom_rule("test_mode", None, 50, "None Keywords")

    def test_high_priority(self):
        # Highest possible priority
        add_custom_rule("test_mode", ["hello", "world"], 100, "High Priority")
        assert INTENT_RULES[0].priority == 100

    def test_low_priority(self):
        # Lowest possible priority
        add_custom_rule("test_mode", ["hello", "world"], 0, "Low Priority")
        assert INTENT_RULES[-1].priority == 0

    def test_invalid_priority(self):
        # Invalid priority value
        with pytest.raises(ValueError):
            add_custom_rule("test_mode", ["hello", "world"], -1, "Invalid Priority")

    def test_multiple_rules(self):
        # Adding multiple rules and checking sorting
        add_custom_rule("mode1", ["keyword1"], 70, "Rule 1")
        add_custom_rule("mode2", ["keyword2"], 60, "Rule 2")
        add_custom_rule("mode3", ["keyword3"], 80, "Rule 3")
        assert [rule.priority for rule in INTENT_RULES] == [80, 70, 60]

    def test_description_not_required(self):
        # Description is optional
        add_custom_rule("test_mode", ["hello", "world"], 50)
        assert len(INTENT_RULES) == 1
        assert INTENT_RULES[0].description == ""

    def test_async_behavior(self):
        # Since the function does not involve async operations, this test is a placeholder
        assert True