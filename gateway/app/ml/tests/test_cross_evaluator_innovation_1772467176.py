import pytest

class MockResponse:
    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)

@pytest.fixture
def mock_response():
    return MockResponse({})

def test_extract_domain_score_happy_path(mock_response):
    res = MockResponse({
        "details": [
            {
                "eval": {
                    "optimized": {
                        "accuracy": 8.5
                    }
                }
            }
        ]
    })
    assert _extract_domain_score(res) == 8.5

def test_extract_domain_score_empty_res(mock_response):
    res = mock_response
    assert _extract_domain_score(res) == 0.0

def test_extract_domain_score_none_res():
    assert _extract_domain_score(None) == 0.0

def test_extract_domain_score_missing_accuracy(mock_response):
    res = MockResponse({
        "details": [
            {
                "eval": {}
            }
        ]
    })
    assert _extract_domain_score(res) == 5.5

def test_extract_domain_score_nested_structure_error(mock_response):
    res = MockResponse({
        "details": []
    })
    assert _extract_domain_score(res) == 0.0