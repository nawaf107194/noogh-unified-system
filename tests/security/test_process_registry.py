"""
Unit tests for Global Process Registry

Tests nonce-based PID verification and ownership enforcement.
"""

import pytest
from unified_core.core.process_registry import GlobalProcessRegistry, ProcessRecord


@pytest.fixture
def registry():
    """Get fresh registry instance for each test."""
    return GlobalProcessRegistry.get_instance()


def test_nonce_generation_unique(registry):
    """Nonces must be unique across registrations."""
    nonces = set()
    
    for i in range(1000):
        nonce = registry.register(
            pid=1000 + i,
            user_id="test",
            command=["test"]
        )
        assert nonce not in nonces, "Nonce collision detected"
        assert len(nonce) == 64, "Nonce should be 32-byte hex (64 chars)"
        nonces.add(nonce)
    
    # Cleanup
    for i in range(1000):
        registry.unregister(1000 + i)


def test_verify_correct_nonce(registry):
    """Correct nonce allows kill."""
    nonce = registry.register(pid=1234, user_id="alice", command=["test"])
    
    assert registry.verify(pid=1234, nonce=nonce, user_id="alice")
    
    # Cleanup
    registry.unregister(1234)


def test_verify_wrong_nonce(registry):
    """Wrong nonce blocks kill."""
    nonce = registry.register(pid=1234, user_id="alice", command=["test"])
    
    assert not registry.verify(pid=1234, nonce="wrong_nonce", user_id="alice")
    
    # Cleanup
    registry.unregister(1234)


def test_verify_wrong_user(registry):
    """Different user cannot kill process."""
    nonce = registry.register(pid=1234, user_id="alice", command=["test"])
    
    assert not registry.verify(pid=1234, nonce=nonce, user_id="bob")
    
    # Cleanup
    registry.unregister(1234)


def test_admin_can_kill_any(registry):
    """Admin can kill any process."""
    nonce = registry.register(pid=1234, user_id="alice", command=["test"])
    
    assert registry.verify(pid=1234, nonce=nonce, user_id="admin")
    
    # Cleanup
    registry.unregister(1234)


def test_pid_not_registered(registry):
    """Verification fails for unregistered PID."""
    assert not registry.verify(pid=9999, nonce="fake", user_id="alice")


def test_mark_killed(registry):
    """Marking process as killed updates record."""
    nonce = registry.register(pid=1234, user_id="alice", command=["test"])
    
    registry.mark_killed(pid=1234, exit_code=0)
    
    stats = registry.get_stats()
    assert stats["killed_count"] >= 1
    
    # Cleanup
    registry.unregister(1234)


def test_get_user_processes(registry):
    """User can list their own processes."""
    nonce1 = registry.register(pid=1234, user_id="alice", command=["cmd1"])
    nonce2 = registry.register(pid=1235, user_id="alice", command=["cmd2"])
    nonce3 = registry.register(pid=1236, user_id="bob", command=["cmd3"])
    
    alice_procs = registry.get_user_processes("alice")
    assert len(alice_procs) >= 2
    assert all(p["pid"] in [1234, 1235] for p in alice_procs)
    
    bob_procs = registry.get_user_processes("bob")
    assert len(bob_procs) >= 1
    assert bob_procs[0]["pid"] == 1236
    
    # Cleanup
    registry.unregister(1234)
    registry.unregister(1235)
    registry.unregister(1236)


def test_registry_stats(registry):
    """Registry statistics are accurate."""
    # Register some processes
    n1 = registry.register(pid=2001, user_id="user1", command=["cmd1"])
    n2 = registry.register(pid=2002, user_id="user1", command=["cmd2"])
    
    stats = registry.get_stats()
    assert stats["total_processes"] >= 2
    assert stats["unique_nonces"] >= 2
    
    # Mark one as killed
    registry.mark_killed(pid=2001)
    stats = registry.get_stats()
    assert stats["killed_count"] >= 1
    
    # Cleanup
    registry.unregister(2001)
    registry.unregister(2002)
