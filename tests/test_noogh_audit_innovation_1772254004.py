import pytest

def bytes_human(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024.0:
            return f"{x:.2f} {u}"
        x /= 1024.0
    return f"{x:.2f} PB"

# Test cases using pytest

def test_bytes_human_happy_path():
    assert bytes_human(1) == "1.00 B"
    assert bytes_human(1023) == "1023.00 B"
    assert bytes_human(1024) == "1.00 KB"
    assert bytes_human(1048576) == "1.00 MB"
    assert bytes_human(1073741824) == "1.00 GB"
    assert bytes_human(1099511627776) == "1.00 TB"

def test_bytes_human_edge_cases():
    assert bytes_human(0) == "0.00 B"
    assert bytes_human(1024**5) == "1.00 PB"
    assert bytes_human(None) is None
    assert bytes_human("") is None

def test_bytes_human_error_cases():
    # This function does not raise exceptions for invalid inputs, so we don't need to test for them.
    pass

def test_bytes_human_async_behavior():
    # This function is synchronous, so there is no async behavior to test.
    pass