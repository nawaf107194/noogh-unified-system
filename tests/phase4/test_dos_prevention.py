"""
Resource Exhaustion DoS Prevention Tests

Tests for preventing denial-of-service through resource exhaustion:
- Memory bomb attacks
- CPU exhaustion attacks
- Disk filling attacks
- Fork bomb prevention
- File descriptor exhaustion
- Network connection exhaustion

OWASP References:
- CWE-400: Uncontrolled Resource Consumption
- CWE-770: Allocation Without Limits
- CWE-789: Memory Allocation with Excessive Size Value
"""
import pytest
import asyncio
import time
import threading
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


@dataclass
class DoSAttempt:
    """Record of a DoS attempt."""
    attack_type: str
    resource_requested: str
    amount_requested: float
    blocked: bool
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# MOCK DOS PREVENTION SYSTEM
# =============================================================================

class ResourceQuota:
    """Per-user/process resource quota."""
    
    def __init__(
        self,
        max_memory_mb: int = 1024,
        max_cpu_seconds: int = 60,
        max_open_files: int = 100,
        max_threads: int = 50,
        max_network_connections: int = 100,
        max_disk_write_mb: int = 1024
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_seconds = max_cpu_seconds
        self.max_open_files = max_open_files
        self.max_threads = max_threads
        self.max_network_connections = max_network_connections
        self.max_disk_write_mb = max_disk_write_mb
        
        # Current usage
        self.used_memory_mb = 0
        self.used_cpu_seconds = 0
        self.open_files = 0
        self.active_threads = 1
        self.network_connections = 0
        self.disk_written_mb = 0


class MockDoSPrevention:
    """DoS prevention system with resource quotas."""
    
    def __init__(self, default_quota: ResourceQuota = None):
        self.default_quota = default_quota or ResourceQuota()
        self.user_quotas: Dict[str, ResourceQuota] = {}
        self.dos_attempts: List[DoSAttempt] = []
        self.blocked_count = 0
        
        # Rate limiting
        self.allocation_timestamps: List[float] = []
        self.max_allocations_per_second = 100
    
    def get_quota(self, user_id: str) -> ResourceQuota:
        """Get quota for user (uses default limits from constructor)."""
        if user_id not in self.user_quotas:
            # Copy limits from default_quota
            self.user_quotas[user_id] = ResourceQuota(
                max_memory_mb=self.default_quota.max_memory_mb,
                max_cpu_seconds=self.default_quota.max_cpu_seconds,
                max_open_files=self.default_quota.max_open_files,
                max_threads=self.default_quota.max_threads,
                max_network_connections=self.default_quota.max_network_connections,
                max_disk_write_mb=self.default_quota.max_disk_write_mb,
            )
        return self.user_quotas[user_id]
    
    def request_memory(self, user_id: str, amount_mb: int) -> bool:
        """Request memory allocation."""
        quota = self.get_quota(user_id)
        projected = quota.used_memory_mb + amount_mb
        
        # Check rate limiting
        if not self._check_rate_limit():
            self.dos_attempts.append(DoSAttempt(
                attack_type="memory_bomb",
                resource_requested="memory",
                amount_requested=amount_mb,
                blocked=True,
                reason="Rate limit exceeded"
            ))
            self.blocked_count += 1
            return False
        
        # Check quota
        if projected > quota.max_memory_mb:
            self.dos_attempts.append(DoSAttempt(
                attack_type="memory_exhaustion",
                resource_requested="memory",
                amount_requested=amount_mb,
                blocked=True,
                reason=f"Would exceed quota ({projected}MB > {quota.max_memory_mb}MB)"
            ))
            self.blocked_count += 1
            return False
        
        quota.used_memory_mb = projected
        return True
    
    def request_threads(self, user_id: str, count: int) -> bool:
        """Request thread creation."""
        quota = self.get_quota(user_id)
        projected = quota.active_threads + count
        
        # Detect fork bomb patterns
        if count > 10:  # Suspicious large thread request
            self.dos_attempts.append(DoSAttempt(
                attack_type="fork_bomb",
                resource_requested="threads",
                amount_requested=count,
                blocked=True,
                reason="Excessive thread creation attempt"
            ))
            self.blocked_count += 1
            return False
        
        if projected > quota.max_threads:
            self.dos_attempts.append(DoSAttempt(
                attack_type="thread_exhaustion",
                resource_requested="threads",
                amount_requested=count,
                blocked=True,
                reason=f"Would exceed quota ({projected} > {quota.max_threads})"
            ))
            self.blocked_count += 1
            return False
        
        quota.active_threads = projected
        return True
    
    def request_file_handles(self, user_id: str, count: int) -> bool:
        """Request file handles."""
        quota = self.get_quota(user_id)
        projected = quota.open_files + count
        
        if projected > quota.max_open_files:
            self.dos_attempts.append(DoSAttempt(
                attack_type="file_descriptor_exhaustion",
                resource_requested="file_handles",
                amount_requested=count,
                blocked=True,
                reason=f"Would exceed quota ({projected} > {quota.max_open_files})"
            ))
            self.blocked_count += 1
            return False
        
        quota.open_files = projected
        return True
    
    def request_disk_write(self, user_id: str, amount_mb: int) -> bool:
        """Request disk write."""
        quota = self.get_quota(user_id)
        projected = quota.disk_written_mb + amount_mb
        
        if projected > quota.max_disk_write_mb:
            self.dos_attempts.append(DoSAttempt(
                attack_type="disk_filling",
                resource_requested="disk",
                amount_requested=amount_mb,
                blocked=True,
                reason=f"Would exceed quota ({projected}MB > {quota.max_disk_write_mb}MB)"
            ))
            self.blocked_count += 1
            return False
        
        quota.disk_written_mb = projected
        return True
    
    def request_network_connection(self, user_id: str) -> bool:
        """Request network connection."""
        quota = self.get_quota(user_id)
        
        if quota.network_connections >= quota.max_network_connections:
            self.dos_attempts.append(DoSAttempt(
                attack_type="connection_exhaustion",
                resource_requested="network",
                amount_requested=1,
                blocked=True,
                reason=f"Connection limit reached ({quota.max_network_connections})"
            ))
            self.blocked_count += 1
            return False
        
        quota.network_connections += 1
        return True
    
    def _check_rate_limit(self) -> bool:
        """Check allocation rate limit."""
        now = time.time()
        
        # Remove old timestamps
        self.allocation_timestamps = [
            t for t in self.allocation_timestamps 
            if now - t < 1.0
        ]
        
        if len(self.allocation_timestamps) >= self.max_allocations_per_second:
            return False
        
        self.allocation_timestamps.append(now)
        return True


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def dos_prevention():
    """Create DoS prevention system."""
    return MockDoSPrevention()


@pytest.fixture
def strict_prevention():
    """Create DoS prevention with strict limits."""
    return MockDoSPrevention(ResourceQuota(
        max_memory_mb=256,
        max_threads=10,
        max_open_files=20,
        max_network_connections=10,
    ))


# =============================================================================
# MEMORY EXHAUSTION TESTS
# =============================================================================

class TestMemoryExhaustion:
    """Test memory exhaustion prevention."""
    
    def test_normal_memory_request_allowed(self, dos_prevention):
        """Test normal memory requests are allowed."""
        allowed = dos_prevention.request_memory("user1", 100)  # 100MB
        
        assert allowed
    
    def test_large_memory_request_blocked(self, dos_prevention):
        """Test large memory requests are blocked."""
        # Request more than quota
        allowed = dos_prevention.request_memory("user1", 2000)  # 2GB
        
        assert not allowed
        assert any(a.attack_type == "memory_exhaustion" for a in dos_prevention.dos_attempts)
    
    def test_repeated_requests_exhaust_quota(self, dos_prevention):
        """Test repeated requests eventually exhaust quota."""
        user = "attacker"
        blocked = False
        
        # Try to allocate in chunks
        for _ in range(20):
            if not dos_prevention.request_memory(user, 100):  # 100MB each
                blocked = True
                break
        
        assert blocked, "Quota should be exhausted"
    
    def test_memory_bomb_rate_limited(self, dos_prevention):
        """Test rapid memory allocations are rate limited."""
        blocked = False
        
        # Rapid-fire allocations
        for _ in range(200):
            if not dos_prevention.request_memory("attacker", 1):
                blocked = True
                break
        
        assert blocked, "Rate limiting should trigger"


# =============================================================================
# FORK BOMB PREVENTION TESTS
# =============================================================================

class TestForkBombPrevention:
    """Test fork bomb prevention."""
    
    def test_normal_thread_creation_allowed(self, dos_prevention):
        """Test normal thread creation is allowed."""
        allowed = dos_prevention.request_threads("user1", 2)
        
        assert allowed
    
    def test_excessive_threads_blocked(self, dos_prevention):
        """Test excessive thread creation is blocked."""
        allowed = dos_prevention.request_threads("attacker", 50)  # Large batch
        
        assert not allowed
        assert any(a.attack_type == "fork_bomb" for a in dos_prevention.dos_attempts)
    
    def test_gradual_thread_exhaustion(self, strict_prevention):
        """Test gradual thread exhaustion is prevented."""
        user = "attacker"
        blocked = False
        
        # Strict limit is 10 threads, starting at 1
        # Try to create threads gradually - should block before reaching limit
        for i in range(15):
            if not strict_prevention.request_threads(user, 1):
                blocked = True
                break
        
        assert blocked, "Thread quota should be exhausted"


# =============================================================================
# FILE DESCRIPTOR EXHAUSTION TESTS
# =============================================================================

class TestFileDescriptorExhaustion:
    """Test file descriptor exhaustion prevention."""
    
    def test_normal_file_open_allowed(self, dos_prevention):
        """Test normal file opening is allowed."""
        allowed = dos_prevention.request_file_handles("user1", 1)
        
        assert allowed
    
    def test_excessive_files_blocked(self, strict_prevention):
        """Test excessive file opening is blocked."""
        blocked = False
        
        # Strict limit is 20 files
        for _ in range(25):
            if not strict_prevention.request_file_handles("attacker", 1):
                blocked = True
                break
        
        assert blocked, "File handle quota should be exhausted"


# =============================================================================
# DISK FILLING ATTACK TESTS
# =============================================================================

class TestDiskFillingAttack:
    """Test disk filling attack prevention."""
    
    def test_normal_disk_write_allowed(self, dos_prevention):
        """Test normal disk writes are allowed."""
        allowed = dos_prevention.request_disk_write("user1", 10)  # 10MB
        
        assert allowed
    
    def test_large_disk_write_blocked(self, dos_prevention):
        """Test large disk writes are blocked."""
        allowed = dos_prevention.request_disk_write("attacker", 2000)  # 2GB
        
        assert not allowed
        assert any(a.attack_type == "disk_filling" for a in dos_prevention.dos_attempts)


# =============================================================================
# NETWORK EXHAUSTION TESTS
# =============================================================================

class TestNetworkExhaustion:
    """Test network connection exhaustion prevention."""
    
    def test_normal_connection_allowed(self, dos_prevention):
        """Test normal connections are allowed."""
        allowed = dos_prevention.request_network_connection("user1")
        
        assert allowed
    
    def test_connection_limit_enforced(self, strict_prevention):
        """Test connection limit is enforced."""
        user = "attacker"
        blocked = False
        
        # Strict limit is 10 connections
        for _ in range(15):
            if not strict_prevention.request_network_connection(user):
                blocked = True
                break
        
        assert blocked, "Connection limit should be enforced"


# =============================================================================
# MULTI-USER ISOLATION TESTS
# =============================================================================

class TestMultiUserIsolation:
    """Test that one user's quota doesn't affect others."""
    
    def test_user_quotas_isolated(self, dos_prevention):
        """Test that user quotas are isolated."""
        # User1 exhausts their quota
        for _ in range(15):
            dos_prevention.request_memory("user1", 100)
        
        # User2 should still be able to allocate
        allowed = dos_prevention.request_memory("user2", 100)
        
        assert allowed, "User2's quota should be independent"
    
    def test_attacker_doesnt_affect_legitimate(self, dos_prevention):
        """Test attacker doesn't exhaust resources for legitimate users."""
        # Attacker hits rate limit
        for _ in range(150):
            dos_prevention.request_memory("attacker", 1)
        
        # Legitimate user should still work
        time.sleep(1.1)  # Wait for rate limit window to reset
        allowed = dos_prevention.request_memory("legitimate", 50)
        
        assert allowed


# =============================================================================
# AUDIT SUMMARY
# =============================================================================

class TestDoSPreventionAuditSummary:
    """Generate DoS prevention audit summary."""
    
    def test_generate_audit_summary(self, dos_prevention, strict_prevention):
        """Run DoS prevention tests and generate summary."""
        results = {
            "memory_attacks_blocked": 0,
            "fork_bombs_blocked": 0,
            "file_exhaustion_blocked": 0,
            "disk_attacks_blocked": 0,
            "network_attacks_blocked": 0,
        }
        
        # Test memory attack
        if not dos_prevention.request_memory("attacker", 5000):
            results["memory_attacks_blocked"] += 1
        
        # Test fork bomb
        if not dos_prevention.request_threads("attacker", 100):
            results["fork_bombs_blocked"] += 1
        
        # Test file descriptor exhaustion
        for _ in range(150):
            dos_prevention.request_file_handles("attacker", 1)
        if not dos_prevention.request_file_handles("attacker", 1):
            results["file_exhaustion_blocked"] += 1
        
        # Test disk attack
        if not dos_prevention.request_disk_write("attacker", 5000):
            results["disk_attacks_blocked"] += 1
        
        # Test network exhaustion
        for _ in range(150):
            strict_prevention.request_network_connection("attacker")
        if not strict_prevention.request_network_connection("attacker"):
            results["network_attacks_blocked"] += 1
        
        print(f"\n{'='*60}")
        print("DOS PREVENTION AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Memory Attacks Blocked: {results['memory_attacks_blocked']}")
        print(f"Fork Bombs Blocked: {results['fork_bombs_blocked']}")
        print(f"File Exhaustion Blocked: {results['file_exhaustion_blocked']}")
        print(f"Disk Attacks Blocked: {results['disk_attacks_blocked']}")
        print(f"Network Attacks Blocked: {results['network_attacks_blocked']}")
        print(f"Total Blocked: {dos_prevention.blocked_count + strict_prevention.blocked_count}")
        print(f"{'='*60}\n")
        
        # All attack types should be blocked
        assert results["memory_attacks_blocked"] == 1
        assert results["fork_bombs_blocked"] == 1
        assert results["disk_attacks_blocked"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
