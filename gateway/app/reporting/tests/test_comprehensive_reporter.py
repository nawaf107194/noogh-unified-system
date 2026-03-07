import pytest

def test_get_reporter_happy_path():
    reporter = get_reporter()
    assert isinstance(reporter, ComprehensiveReporter)

def test_get_reporter_edge_case_none():
    global _reporter
    _reporter = None
    reporter = get_reporter()
    assert isinstance(reporter, ComprehensiveReporter)
    assert reporter is not None

def test_get_reporter_edge_case_existing():
    global _reporter
    _reporter = ComprehensiveReporter()
    reporter1 = get_reporter()
    reporter2 = get_reporter()
    assert reporter1 is reporter2

def test_get_reporter_error_case_invalid_input():
    with pytest.raises(TypeError):
        get_reporter(arg="invalid")