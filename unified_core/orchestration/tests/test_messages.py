import pytest
from unittest.mock import patch
from time import time
from datetime import timedelta

class Message:
    def __init__(self, timestamp, ttl_ms):
        self.timestamp = timestamp
        self.ttl_ms = ttl_ms

    def is_expired(self) -> bool:
        """Check if message has exceeded TTL"""
        elapsed_ms = (time() - self.timestamp) * 1000
        return elapsed_ms > self.ttl_ms

@pytest.fixture
def message():
    current_time = time()
    return Message(current_time, 10000)  # 10 seconds TTL

def test_is_expired_happy_path(message):
    assert not message.is_expired()

@patch('time.time')
def test_is_expired_expired(mock_time, message):
    mock_time.return_value += message.ttl_ms / 1000 + 1
    assert message.is_expired()

@patch('time.time')
def test_is_expired_edge_case_zero_ttl(mock_time):
    message = Message(time(), 0)
    assert message.is_expired()

@patch('time.time')
def test_is_expired_edge_case_negative_ttl(mock_time):
    message = Message(time(), -1000)
    assert message.is_expired()

@patch('time.time')
def test_is_expired_edge_case_future_timestamp(mock_time):
    future_time = time() + 100000
    message = Message(future_time, 10000)
    assert not message.is_expired()

@patch('time.time')
def test_is_expired_invalid_ttl_string(mock_time):
    with pytest.raises(TypeError):
        message = Message(time(), "not_a_number")
        message.is_expired()

@patch('time.time')
def test_is_expired_invalid_timestamp_string(mock_time):
    with pytest.raises(TypeError):
        message = Message("not_a_number", 10000)
        message.is_expired()

@patch('time.time')
def test_is_expired_async_behavior(mock_time):
    # Since the function does not involve async operations,
    # we can still test it as a synchronous function.
    mock_time.return_value += message.ttl_ms / 1000 + 1
    assert message.is_expired()