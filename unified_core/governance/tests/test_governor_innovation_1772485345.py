import pytest
from unified_core.governance.governor import classify, DecisionImpact

def test_classify_happy_path():
    assert classify("process.spawn") == DecisionImpact.MEDIUM

def test_classify_empty_string():
    assert classify("") is None

def test_classify_none_value():
    assert classify(None) is None

def test_classify_invalid_component_type():
    assert classify(123) is None