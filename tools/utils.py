# tools/test_serializer.py

from .utils import safe_divide

def test_serialization():
    result = safe_divide(10, 2)
    assert result == 5