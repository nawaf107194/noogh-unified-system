import pytest

from neural_engine.autonomy.code_doctor import get_code_doctor, CodeDoctor

@pytest.fixture(autouse=True)
def _reset_code_doctor():
    global _code_doctor
    _code_doctor = None
    yield
    _code_doctor = None

def test_get_code_doctor_happy_path():
    """Test the happy path of get_code_doctor."""
    doc1 = get_code_doctor()
    doc2 = get_code_doctor()
    assert doc1 is not None
    assert doc2 is not None
    assert doc1 == doc2

def test_get_code_doctor_edge_case_none():
    """Test the edge case where _code_doctor is None."""
    global _code_doctor
    _code_doctor = None
    doc = get_code_doctor()
    assert doc is not None

def test_get_code_doctor_edge_case_not_none():
    """Test the edge case where _code_doctor is already set."""
    global _code_doctor
    _code_doctor = CodeDoctor()
    doc = get_code_doctor()
    assert doc is not None
    assert isinstance(doc, CodeDoctor)