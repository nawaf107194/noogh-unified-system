import pytest
import httpx

def safe_text(r: httpx.Response) -> str:
    try:
        return r.text[:2000]
    except Exception:
        return "<unreadable>"

@pytest.mark.parametrize("input_data, expected_output", [
    (httpx.Response(200, content="Hello World"), "Hello World"),
    (httpx.Response(200, content="a" * 1999), "a" * 1999),
    (httpx.Response(200, content="a" * 2000), "a" * 2000),
    (httpx.Response(200, content="a" * 2001), "a" * 2000),
    (httpx.Response(404, content=None), "<unreadable>"),
    (httpx.Response(500, content=b'\x00' * 2000), "<unreadable>"),
    (None, "<unreadable>"),
])
def test_safe_text(input_data, expected_output):
    assert safe_text(input_data) == expected_output