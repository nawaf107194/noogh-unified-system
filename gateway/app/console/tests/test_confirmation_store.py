import pytest
from gateway.app.console.confirmation_store import ConfirmationStore

@pytest.fixture
def confirmation_store():
    return ConfirmationStore()

def test_cleanup_expired_happy_path(confirmation_store):
    # Arrange
    confirmation_store.pending = {
        "nonce1": {"expires": datetime.utcnow() + timedelta(hours=1)},
        "nonce2": {"expires": datetime.utcnow() - timedelta(hours=1)}
    }
    
    # Act
    confirmation_store.cleanup_expired()
    
    # Assert
    assert len(confirmation_store.pending) == 1
    assert "nonce1" in confirmation_store.pending
    assert "nonce2" not in confirmation_store.pending

def test_cleanup_expired_empty(confirmation_store):
    # Arrange
    confirmation_store.pending = {}
    
    # Act
    confirmation_store.cleanup_expired()
    
    # Assert
    assert len(confirmation_store.pending) == 0

def test_cleanup_expired_none(confirmation_store):
    # Arrange
    confirmation_store.pending = None
    
    # Act
    confirmation_store.cleanup_expired()
    
    # Assert
    assert confirmation_store.pending is None

def test_cleanup_expired_boundary(confirmation_store):
    # Arrange
    now = datetime.utcnow()
    boundarynonce = "boundary_nonce"
    confirmation_store.pending = {
        "boundarynonce": {"expires": now}
    }
    
    # Act
    confirmation_store.cleanup_expired()
    
    # Assert
    assert len(confirmation_store.pending) == 1
    assert "boundarynonce" in confirmation_store.pending

def test_cleanup_expired_invalid_input(confirmation_store):
    # Arrange
    confirmation_store.pending = {
        "invalid_nonce": {"expires": "not_a_datetime"}
    }
    
    # Act & Assert (should not raise any exceptions)
    confirmation_store.cleanup_expired()
    
    # Cleanup assertion
    assert len(confirmation_store.pending) == 1
    assert "invalid_nonce" in confirmation_store.pending