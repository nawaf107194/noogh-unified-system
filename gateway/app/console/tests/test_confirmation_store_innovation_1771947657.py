import pytest
from gateway.app.console.confirmation_store import ConfirmationStore
from datetime import datetime, timedelta

@pytest.fixture
def confirmation_store():
    return ConfirmationStore()

def test_cleanup_expired_happy_path(confirmation_store):
    # Arrange
    confirmation_store.pending = {
        'nonce1': {'expires': datetime.utcnow() + timedelta(seconds=1)},
        'nonce2': {'expires': datetime.utcnow() + timedelta(seconds=-1)}
    }
    
    # Act
    confirmation_store.cleanup_expired()
    
    # Assert
    assert 'nonce1' not in confirmation_store.pending
    assert 'nonce2' not in confirmation_store.pending

def test_cleanup_expired_empty(confirmation_store):
    # Arrange
    confirmation_store.pending = {}
    
    # Act
    confirmation_store.cleanup_expired()
    
    # Assert
    assert confirmation_store.pending == {}

def test_cleanup_expired_none(confirmation_store):
    # Arrange
    confirmation_store.pending = None
    
    # Act
    confirmation_store.cleanup_expired()
    
    # Assert
    assert confirmation_store.pending is None

def test_cleanup_expired_boundaries(confirmation_store):
    # Arrange
    now = datetime.utcnow()
    expiration_times = [
        now - timedelta(seconds=1),
        now,
        now + timedelta(seconds=1)
    ]
    confirmation_store.pending = {
        'nonce1': {'expires': expiration_times[0]},
        'nonce2': {'expires': expiration_times[1]},
        'nonce3': {'expires': expiration_times[2]}
    }
    
    # Act
    confirmation_store.cleanup_expired()
    
    # Assert
    assert 'nonce1' not in confirmation_store.pending
    assert 'nonce2' in confirmation_store.pending
    assert 'nonce3' in confirmation_store.pending

def test_cleanup_expired_invalid_input(confirmation_store):
    with pytest.raises(TypeError) as exc_info:
        confirmation_store.cleanup_expired(nonce='invalid')
    
    # Assert
    assert exc_info.type is TypeError
    assert str(exc_info.value) == "cleanup_expired() got an unexpected keyword argument 'nonce'"