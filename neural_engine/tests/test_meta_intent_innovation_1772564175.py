import pytest
from neural_engine import ExpandedIntent
from .meta_intent import _no_expansion

def test_no_expansion_happy_path():
    query = "test query"
    result = _no_expansion(query)
    
    assert isinstance(result, ExpandedIntent)
    assert result.original_query == query
    assert result.detected_meta_intent is None
    assert result.components == []
    assert result.expansion_confidence == 1.0
    assert result.requires_all is False
    assert result.estimated_complexity == "simple"

def test_no_expansion_empty_string():
    query = ""
    result = _no_expansion(query)
    
    assert isinstance(result, ExpandedIntent)
    assert result.original_query == query
    assert result.detected_meta_intent is None
    assert result.components == []
    assert result.expansion_confidence == 1.0
    assert result.requires_all is False
    assert result.estimated_complexity == "simple"

def test_no_expansion_none_input():
    query = None
    result = _no_expansion(query)
    
    assert isinstance(result, ExpandedIntent)
    assert result.original_query is None
    assert result.detected_meta_intent is None
    assert result.components == []
    assert result.expansion_confidence == 1.0
    assert result.requires_all is False
    assert result.estimated_complexity == "simple"

def test_no_expansion_type_validation():
    result = _no_expansion("test")
    assert isinstance(result, ExpandedIntent)