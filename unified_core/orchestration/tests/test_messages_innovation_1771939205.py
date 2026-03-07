import pytest
from unified_core.orchestration.messages import Message

def test_is_expired_happy_path():
    # Happy path: normal inputs
    message = Message(timestamp=time.time() - 5, ttl_ms=10)
    assert not message.is_expired()

def test_is_expired_edge_case_zero_ttl():
    # Edge case: zero TTL
    message = Message(timestamp=time.time(), ttl_ms=0)
    assert not message.is_expired()

def test_is_expired_edge_case_negative_ttl():
    # Edge case: negative TTL
    message = Message(timestamp=time.time() - 5, ttl_ms=-10)
    assert not message.is_expired()

def test_is_expired_boundary_case_exactly_at_ttl():
    # Boundary case: exactly at TTL
    start_time = time.time()
    message = Message(timestamp=start_time, ttl_ms=1000)
    assert not message.is_expired()  # Should return False as it's equal to TTL

def test_is_expired_boundary_case_just_before_ttl():
    # Boundary case: just before TTL
    start_time = time.time()
    message = Message(timestamp=start_time + 5, ttl_ms=1000)
    assert not message.is_expired()  # Should return False as it's less than TTL

def test_is_expired_boundary_case_just_after_ttl():
    # Boundary case: just after TTL
    start_time = time.time()
    message = Message(timestamp=start_time - 5, ttl_ms=1000)
    assert message.is_expired()  # Should return True as it's more than TTL

def test_is_expired_invalid_input_negative_timestamp():
    # Error case: invalid input (negative timestamp)
    with pytest.raises(ValueError):
        Message(timestamp=-1, ttl_ms=10)

def test_is_expired_invalid_input_non_numeric_ttl():
    # Error case: invalid input (non-numeric TTL)
    with pytest.raises(ValueError):
        Message(timestamp=time.time(), ttl_ms="not a number")