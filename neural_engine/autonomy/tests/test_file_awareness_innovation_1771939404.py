import pytest
from neural_engine.autonomy.file_awareness import FileCategory, _build_category_patterns

def test_build_category_patterns_happy_path():
    instance = _build_category_patterns()
    assert isinstance(instance.compiled_patterns, dict)
    for category in FileCategory:
        patterns = instance.compiled_patterns.get(category)
        assert isinstance(patterns, list)
        for pattern in patterns:
            assert isinstance(pattern, re.Pattern)

def test_build_category_patterns_edge_case_empty():
    original_authority_patterns = _build_category_patterns.AUTHORITY_PATTERNS
    original_pattern_patterns = _build_category_patterns.PATTERN_PATTERNS
    original_historical_patterns = _build_category_patterns.HISTORICAL_PATTERNS
    original_sensitive_patterns = _build_category_patterns.SENSITIVE_PATTERNS
    original_generated_patterns = _build_category_patterns.GENERATED_PATTERNS
    original_data_patterns = _build_category_patterns.DATA_PATTERNS

    try:
        _build_category_patterns.AUTHORITY_PATTERNS = []
        _build_category_patterns.PATTERN_PATTERNS = []
        _build_category_patterns.HISTORICAL_PATTERNS = []
        _build_category_patterns.SENSITIVE_PATTERNS = []
        _build_category_patterns.GENERATED_PATTERNS = []
        _build_category_patterns.DATA_PATTERNS = []

        instance = _build_category_patterns()
        for category in FileCategory:
            patterns = instance.compiled_patterns.get(category)
            assert isinstance(patterns, list)
            assert len(patterns) == 0
    finally:
        _build_category_patterns.AUTHORITY_PATTERNS = original_authority_patterns
        _build_category_patterns.PATTERN_PATTERNS = original_pattern_patterns
        _build_category_patterns.HISTORICAL_PATTERNS = original_historical_patterns
        _build_category_patterns.SENSITIVE_PATTERNS = original_sensitive_patterns
        _build_category_patterns.GENERATED_PATTERNS = original_generated_patterns
        _build_category_patterns.DATA_PATTERNS = original_data_patterns

def test_build_category_patterns_edge_case_none():
    original_authority_patterns = _build_category_patterns.AUTHORITY_PATTERNS
    original_pattern_patterns = _build_category_patterns.PATTERN_PATTERNS
    original_historical_patterns = _build_category_patterns.HISTORICAL_PATTERNS
    original_sensitive_patterns = _build_category_patterns.SENSITIVE_PATTERNS
    original_generated_patterns = _build_category_patterns.GENERATED_PATTERNS
    original_data_patterns = _build_category_patterns.DATA_PATTERNS

    try:
        _build_category_patterns.AUTHORITY_PATTERNS = None
        _build_category_patterns.PATTERN_PATTERNS = None
        _build_category_patterns.HISTORICAL_PATTERNS = None
        _build_category_patterns.SENSITIVE_PATTERNS = None
        _build_category_patterns.GENERATED_PATTERNS = None
        _build_category_patterns.DATA_PATTERNS = None

        instance = _build_category_patterns()
        for category in FileCategory:
            patterns = instance.compiled_patterns.get(category)
            assert isinstance(patterns, list)
            assert len(patterns) == 0
    finally:
        _build_category_patterns.AUTHORITY_PATTERNS = original_authority_patterns
        _build_category_patterns.PATTERN_PATTERNS = original_pattern_patterns
        _build_category_patterns.HISTORICAL_PATTERNS = original_historical_patterns
        _build_category_patterns.SENSITIVE_PATTERNS = original_sensitive_patterns
        _build_category_patterns.GENERATED_PATTERNS = original_generated_patterns
        _build_category_patterns.DATA_PATTERNS = original_data_patterns

def test_build_category_patterns_error_case_invalid_input():
    original_authority_patterns = _build_category_patterns.AUTHORITY_PATTERNS

    try:
        _build_category_patterns.AUTHORITY_PATTERNS = "not a list"

        with pytest.raises(TypeError):
            _build_category_patterns()
    finally:
        _build_category_patterns.AUTHORITY_PATTERNS = original_authority_patterns