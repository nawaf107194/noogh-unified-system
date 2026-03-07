"""
Resource Limit Enforcement Tests

Tests for enforcing resource limits and preventing abuse:
- CPU usage limits
- Memory allocation limits
- GPU memory limits
- Disk I/O limits
- Network bandwidth limits
- Process/thread limits

OWASP References:
- CWE-400: Uncontrolled Resource Consumption
- CWE-770: Allocation Without Limits
"""
import pytest
import asyncio
import time
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# =============================================================================
# MOCK CLASSES - Always use mocks for testing isolation
# =============================================================================

@dataclass
class CPUMetrics:
    """CPU utilization metrics."""
    usage_percent: float
    usage_per_core: List[float] = field(default_factory=list)
    frequency_mhz: float = 0.0
    core_count: int = 4
    thread_count: int = 8


@dataclass
class MemoryMetrics:
    """Memory utilization metrics."""
    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percent: float
    swap_total_bytes: int = 0
    swap_used_bytes: int = 0
    swap_percent: float = 0.0


@dataclass
class GPUMetrics:
    """GPU utilization metrics."""
    device_id: int
    name: str
    memory_total_mb: int
    memory_used_mb: int
    memory_free_mb: int
    memory_percent: float
    gpu_utilization: float
    temperature_c: float = 0.0
    power_draw_w: float = 0.0


@dataclass
class ResourceLimits:
    """Resource limit configuration."""
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 80.0
    max_gpu_memory_percent: float = 90.0
    max_disk_percent: float = 90.0
    max_processes: int = 1000
    max_threads: int = 5000
    max_open_files: int = 10000
    max_network_connections: int = 1000


@dataclass
class LimitViolation:
    """Record of a limit violation."""
    resource: str
    current_value: float
    limit_value: float
    severity: str  # warning, critical
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# MOCK RESOURCE ENFORCER
# =============================================================================

class MockResourceEnforcer:
    """Enforces resource limits and tracks violations."""
    
    def __init__(self, limits: ResourceLimits = None):
        self.limits = limits or ResourceLimits()
        self.violations: List[LimitViolation] = []
        self.enforcement_enabled = True
        
        # Simulated current values
        self._current_cpu = 50.0
        self._current_memory = 60.0
        self._current_gpu_memory = 70.0
        self._process_count = 100
        self._thread_count = 500
    
    def check_cpu_limit(self, requested_percent: float) -> bool:
        """Check if CPU usage would exceed limit."""
        projected = self._current_cpu + requested_percent
        
        if projected > self.limits.max_cpu_percent:
            self.violations.append(LimitViolation(
                resource="cpu",
                current_value=projected,
                limit_value=self.limits.max_cpu_percent,
                severity="warning" if projected < 100 else "critical"
            ))
            return False if self.enforcement_enabled else True
        return True
    
    def check_memory_limit(self, requested_bytes: int, total_bytes: int) -> bool:
        """Check if memory allocation would exceed limit."""
        requested_percent = (requested_bytes / total_bytes) * 100
        projected = self._current_memory + requested_percent
        
        if projected > self.limits.max_memory_percent:
            self.violations.append(LimitViolation(
                resource="memory",
                current_value=projected,
                limit_value=self.limits.max_memory_percent,
                severity="warning" if projected < 95 else "critical"
            ))
            return False if self.enforcement_enabled else True
        return True
    
    def check_gpu_memory_limit(self, requested_mb: int, total_mb: int) -> bool:
        """Check if GPU memory allocation would exceed limit."""
        requested_percent = (requested_mb / total_mb) * 100
        projected = self._current_gpu_memory + requested_percent
        
        if projected > self.limits.max_gpu_memory_percent:
            self.violations.append(LimitViolation(
                resource="gpu_memory",
                current_value=projected,
                limit_value=self.limits.max_gpu_memory_percent,
                severity="critical"
            ))
            return False if self.enforcement_enabled else True
        return True
    
    def check_process_limit(self) -> bool:
        """Check if process count would exceed limit."""
        if self._process_count >= self.limits.max_processes:
            self.violations.append(LimitViolation(
                resource="processes",
                current_value=self._process_count,
                limit_value=self.limits.max_processes,
                severity="critical"
            ))
            return False
        return True
    
    def get_remaining_capacity(self) -> Dict[str, float]:
        """Get remaining capacity for each resource."""
        return {
            "cpu_percent": max(0, self.limits.max_cpu_percent - self._current_cpu),
            "memory_percent": max(0, self.limits.max_memory_percent - self._current_memory),
            "gpu_memory_percent": max(0, self.limits.max_gpu_memory_percent - self._current_gpu_memory),
            "processes": max(0, self.limits.max_processes - self._process_count),
            "threads": max(0, self.limits.max_threads - self._thread_count),
        }


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def enforcer():
    """Create resource enforcer with default limits."""
    return MockResourceEnforcer()


@pytest.fixture
def strict_enforcer():
    """Create resource enforcer with strict limits."""
    return MockResourceEnforcer(ResourceLimits(
        max_cpu_percent=50.0,
        max_memory_percent=50.0,
        max_gpu_memory_percent=50.0,
        max_processes=100,
    ))


@pytest.fixture
def disabled_enforcer():
    """Create enforcer with enforcement disabled (for testing)."""
    e = MockResourceEnforcer()
    e.enforcement_enabled = False
    return e


# =============================================================================
# CPU LIMIT TESTS
# =============================================================================

class TestCPULimits:
    """Test CPU usage limit enforcement."""
    
    def test_cpu_within_limit_allowed(self, enforcer):
        """Test CPU usage within limit is allowed."""
        # Current: 50%, Limit: 80%, Request: 20%
        allowed = enforcer.check_cpu_limit(20.0)
        
        assert allowed
        assert len(enforcer.violations) == 0
    
    def test_cpu_exceeds_limit_blocked(self, enforcer):
        """Test CPU usage exceeding limit is blocked."""
        # Current: 50%, Limit: 80%, Request: 40%
        allowed = enforcer.check_cpu_limit(40.0)
        
        assert not allowed
        assert len(enforcer.violations) == 1
        assert enforcer.violations[0].resource == "cpu"
    
    def test_cpu_exactly_at_limit(self, enforcer):
        """Test CPU usage exactly at limit."""
        # Current: 50%, Limit: 80%, Request: 30% = 80%
        allowed = enforcer.check_cpu_limit(30.0)
        
        # Exactly at limit should be allowed
        assert allowed
    
    def test_strict_cpu_limit(self, strict_enforcer):
        """Test stricter CPU limits."""
        # Current: 50%, Limit: 50%, Request: 10%
        allowed = strict_enforcer.check_cpu_limit(10.0)
        
        assert not allowed  # Already at limit


# =============================================================================
# MEMORY LIMIT TESTS
# =============================================================================

class TestMemoryLimits:
    """Test memory allocation limit enforcement."""
    
    def test_memory_within_limit_allowed(self, enforcer):
        """Test memory allocation within limit is allowed."""
        total = 16 * 1024 * 1024 * 1024  # 16GB
        request = 1 * 1024 * 1024 * 1024  # 1GB (6.25%)
        
        allowed = enforcer.check_memory_limit(request, total)
        
        assert allowed
    
    def test_memory_exceeds_limit_blocked(self, enforcer):
        """Test memory allocation exceeding limit is blocked."""
        total = 16 * 1024 * 1024 * 1024  # 16GB
        request = 4 * 1024 * 1024 * 1024  # 4GB (25%)
        
        # Current: 60%, Limit: 80%, Request: 25% = 85%
        allowed = enforcer.check_memory_limit(request, total)
        
        assert not allowed
    
    def test_memory_violation_recorded(self, enforcer):
        """Test that memory violations are recorded."""
        total = 16 * 1024 * 1024 * 1024
        request = 10 * 1024 * 1024 * 1024  # Large request
        
        enforcer.check_memory_limit(request, total)
        
        assert len(enforcer.violations) >= 1
        violation = [v for v in enforcer.violations if v.resource == "memory"][0]
        assert violation.severity in ("warning", "critical")


# =============================================================================
# GPU MEMORY LIMIT TESTS
# =============================================================================

class TestGPUMemoryLimits:
    """Test GPU memory limit enforcement."""
    
    def test_gpu_memory_within_limit_allowed(self, enforcer):
        """Test GPU memory allocation within limit is allowed."""
        total = 24 * 1024  # 24GB in MB
        request = 4 * 1024  # 4GB
        
        allowed = enforcer.check_gpu_memory_limit(request, total)
        
        assert allowed
    
    def test_gpu_memory_exceeds_limit_blocked(self, enforcer):
        """Test GPU memory exceeding limit is blocked."""
        total = 24 * 1024  # 24GB in MB
        request = 8 * 1024  # 8GB (33%) + current 70% = 103%
        
        allowed = enforcer.check_gpu_memory_limit(request, total)
        
        assert not allowed
        assert any(v.resource == "gpu_memory" for v in enforcer.violations)


# =============================================================================
# PROCESS/THREAD LIMIT TESTS
# =============================================================================

class TestProcessLimits:
    """Test process and thread limit enforcement."""
    
    def test_process_within_limit_allowed(self, enforcer):
        """Test process creation within limit is allowed."""
        # Current: 100, Limit: 1000
        allowed = enforcer.check_process_limit()
        
        assert allowed
    
    def test_process_at_limit_blocked(self, strict_enforcer):
        """Test process creation at limit is blocked."""
        # Current: 100, Limit: 100
        allowed = strict_enforcer.check_process_limit()
        
        assert not allowed


# =============================================================================
# CAPACITY MONITORING TESTS
# =============================================================================

class TestCapacityMonitoring:
    """Test remaining capacity monitoring."""
    
    def test_get_remaining_capacity(self, enforcer):
        """Test getting remaining capacity."""
        capacity = enforcer.get_remaining_capacity()
        
        assert "cpu_percent" in capacity
        assert "memory_percent" in capacity
        assert "gpu_memory_percent" in capacity
        assert "processes" in capacity
        assert "threads" in capacity
        
        # All should be positive with default values
        assert all(v >= 0 for v in capacity.values())
    
    def test_remaining_capacity_reflects_usage(self, enforcer):
        """Test that capacity reflects current usage."""
        # CPU: current 50%, limit 80% => remaining 30%
        capacity = enforcer.get_remaining_capacity()
        
        assert capacity["cpu_percent"] == 30.0  # 80 - 50
        assert capacity["memory_percent"] == 20.0  # 80 - 60


# =============================================================================
# ENFORCEMENT TOGGLE TESTS
# =============================================================================

class TestEnforcementToggle:
    """Test enforcement enable/disable functionality."""
    
    def test_enforcement_enabled_blocks_violations(self, enforcer):
        """Test that enabled enforcement blocks violations."""
        enforcer.enforcement_enabled = True
        
        allowed = enforcer.check_cpu_limit(50.0)  # Would exceed limit
        
        assert not allowed
    
    def test_enforcement_disabled_allows_violations(self, disabled_enforcer):
        """Test that disabled enforcement allows (but records) violations."""
        allowed = disabled_enforcer.check_cpu_limit(50.0)
        
        # Should allow but still record
        assert allowed
        assert len(disabled_enforcer.violations) > 0


# =============================================================================
# AUDIT SUMMARY
# =============================================================================

class TestResourceLimitAuditSummary:
    """Generate resource limit audit summary."""
    
    def test_generate_audit_summary(self, enforcer, strict_enforcer):
        """Run resource limit tests and generate summary."""
        results = {
            "cpu_blocked": 0,
            "memory_blocked": 0,
            "gpu_blocked": 0,
            "process_blocked": 0,
        }
        
        total = 16 * 1024 * 1024 * 1024
        
        # Test CPU limits
        if not enforcer.check_cpu_limit(50.0):
            results["cpu_blocked"] += 1
        
        # Test memory limits
        if not enforcer.check_memory_limit(10 * 1024 * 1024 * 1024, total):
            results["memory_blocked"] += 1
        
        # Test GPU limits
        if not enforcer.check_gpu_memory_limit(10 * 1024, 24 * 1024):
            results["gpu_blocked"] += 1
        
        # Test process limits (with strict enforcer)
        if not strict_enforcer.check_process_limit():
            results["process_blocked"] += 1
        
        print(f"\n{'='*60}")
        print("RESOURCE LIMIT ENFORCEMENT AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"CPU Exceeded Blocked: {results['cpu_blocked']}")
        print(f"Memory Exceeded Blocked: {results['memory_blocked']}")
        print(f"GPU Exceeded Blocked: {results['gpu_blocked']}")
        print(f"Process Exceeded Blocked: {results['process_blocked']}")
        print(f"Total Violations Recorded: {len(enforcer.violations) + len(strict_enforcer.violations)}")
        print(f"{'='*60}\n")
        
        # All exceeding limits should be blocked
        assert results["cpu_blocked"] == 1
        assert results["memory_blocked"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
