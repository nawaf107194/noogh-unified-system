import pytest
from typing import List
from gateway.app.ml.curriculum import get_all_domains, CURRICULUM

@pytest.fixture
def mock_curriculum(monkeypatch):
    # Mock the CURRICULUM dictionary to ensure consistent test results
    monkeypatch.setattr('gateway.app.ml.curriculum.CURRICULUM', {
        'data_science': ['statistics', 'machine_learning'],
        'software_engineering': ['algorithms', 'programming_languages'],
        'cybersecurity': ['network_security', 'ethical_hacking']
    })

def test_get_all_domains_happy_path(mock_curriculum):
    # Test with normal inputs - should return all keys in the curriculum
    expected_domains = ['data_science', 'software_engineering', 'cybersecurity']
    assert get_all_domains() == expected_domains

def test_get_all_domains_empty_curriculum(monkeypatch):
    # Test edge case where the curriculum is empty
    monkeypatch.setattr('gateway.app.ml.curriculum.CURRICULUM', {})
    assert get_all_domains() == []

def test_get_all_domains_none_curriculum(monkeypatch):
    # Test edge case where the curriculum is None
    monkeypatch.setattr('gateway.app.ml.curriculum.CURRICULUM', None)
    with pytest.raises(AttributeError):
        get_all_domains()

def test_get_all_domains_invalid_input(monkeypatch):
    # Test error case where the input is invalid (not a dictionary)
    monkeypatch.setattr('gateway.app.ml.curriculum.CURRICULUM', "InvalidInput")
    with pytest.raises(AttributeError):
        get_all_domains()

# Since the function does not involve any async operations, no async tests are necessary.