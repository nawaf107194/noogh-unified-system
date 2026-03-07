"""
GPU Security and Monitoring Tests

Tests for GPU resource security:
- GPU memory isolation
- CUDA context security
- GPU power/thermal limits
- Multi-GPU allocation fairness
- GPU driver security considerations

OWASP References:
- CWE-400: Uncontrolled Resource Consumption
- CWE-770: Allocation Without Limits
"""
import pytest
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
    temperature_c: float
    power_draw_w: float
    power_limit_w: float


@dataclass
class GPUAllocation:
    """GPU memory allocation record."""
    user_id: str
    device_id: int
    memory_mb: int
    allocated_at: datetime = field(default_factory=datetime.now)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class GPUAlert:
    """GPU-related alert."""
    device_id: int
    alert_type: str
    level: AlertLevel
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# MOCK GPU SECURITY MANAGER
# =============================================================================

class MockGPUSecurityManager:
    """Manages GPU security and resource allocation."""
    
    def __init__(self, num_gpus: int = 2, memory_per_gpu_mb: int = 24 * 1024):
        self.num_gpus = num_gpus
        self.memory_per_gpu_mb = memory_per_gpu_mb
        
        # Simulated GPU state
        self.gpu_memory_used: Dict[int, int] = {i: 0 for i in range(num_gpus)}
        self.gpu_temperature: Dict[int, float] = {i: 45.0 for i in range(num_gpus)}
        self.gpu_power: Dict[int, float] = {i: 150.0 for i in range(num_gpus)}
        
        # Allocations
        self.allocations: List[GPUAllocation] = []
        self.user_allocations: Dict[str, Dict[int, int]] = {}  # user -> {gpu_id -> mb}
        
        # Limits
        self.max_memory_per_user_mb = memory_per_gpu_mb // 2  # 50% per user
        self.power_limit_w = 350.0
        self.temp_limit_c = 83.0
        self.temp_warning_c = 75.0
        
        # Alerts
        self.alerts: List[GPUAlert] = []
    
    def get_gpu_metrics(self, device_id: int) -> GPUMetrics:
        """Get current GPU metrics."""
        if device_id >= self.num_gpus:
            raise ValueError(f"Invalid GPU device ID: {device_id}")
        
        used = self.gpu_memory_used[device_id]
        return GPUMetrics(
            device_id=device_id,
            name=f"NVIDIA RTX 4090 #{device_id}",
            memory_total_mb=self.memory_per_gpu_mb,
            memory_used_mb=used,
            memory_free_mb=self.memory_per_gpu_mb - used,
            memory_percent=(used / self.memory_per_gpu_mb) * 100,
            gpu_utilization=50.0,
            temperature_c=self.gpu_temperature[device_id],
            power_draw_w=self.gpu_power[device_id],
            power_limit_w=self.power_limit_w,
        )
    
    def allocate_gpu_memory(self, user_id: str, device_id: int, memory_mb: int) -> bool:
        """Allocate GPU memory for user."""
        if device_id >= self.num_gpus:
            return False
        
        # Check total GPU memory
        current_used = self.gpu_memory_used[device_id]
        if current_used + memory_mb > self.memory_per_gpu_mb:
            self.alerts.append(GPUAlert(
                device_id=device_id,
                alert_type="memory_exhaustion",
                level=AlertLevel.CRITICAL,
                message=f"GPU {device_id} memory exhausted",
                value=current_used + memory_mb,
                threshold=self.memory_per_gpu_mb,
            ))
            return False
        
        # Check per-user limit
        user_used = self.user_allocations.get(user_id, {}).get(device_id, 0)
        if user_used + memory_mb > self.max_memory_per_user_mb:
            self.alerts.append(GPUAlert(
                device_id=device_id,
                alert_type="user_quota_exceeded",
                level=AlertLevel.WARNING,
                message=f"User {user_id} quota exceeded on GPU {device_id}",
                value=user_used + memory_mb,
                threshold=self.max_memory_per_user_mb,
            ))
            return False
        
        # Allocate
        self.gpu_memory_used[device_id] += memory_mb
        if user_id not in self.user_allocations:
            self.user_allocations[user_id] = {}
        if device_id not in self.user_allocations[user_id]:
            self.user_allocations[user_id][device_id] = 0
        self.user_allocations[user_id][device_id] += memory_mb
        
        self.allocations.append(GPUAllocation(
            user_id=user_id,
            device_id=device_id,
            memory_mb=memory_mb,
        ))
        
        return True
    
    def release_gpu_memory(self, user_id: str, device_id: int, memory_mb: int):
        """Release GPU memory."""
        if device_id in self.gpu_memory_used:
            self.gpu_memory_used[device_id] = max(0, self.gpu_memory_used[device_id] - memory_mb)
        
        if user_id in self.user_allocations and device_id in self.user_allocations[user_id]:
            self.user_allocations[user_id][device_id] = max(
                0, self.user_allocations[user_id][device_id] - memory_mb
            )
    
    def check_thermal_limits(self) -> List[GPUAlert]:
        """Check GPU temperatures and generate alerts."""
        alerts = []
        for device_id, temp in self.gpu_temperature.items():
            if temp >= self.temp_limit_c:
                alerts.append(GPUAlert(
                    device_id=device_id,
                    alert_type="thermal_critical",
                    level=AlertLevel.CRITICAL,
                    message=f"GPU {device_id} temperature critical: {temp}°C",
                    value=temp,
                    threshold=self.temp_limit_c,
                ))
            elif temp >= self.temp_warning_c:
                alerts.append(GPUAlert(
                    device_id=device_id,
                    alert_type="thermal_warning",
                    level=AlertLevel.WARNING,
                    message=f"GPU {device_id} temperature high: {temp}°C",
                    value=temp,
                    threshold=self.temp_warning_c,
                ))
        
        self.alerts.extend(alerts)
        return alerts
    
    def check_power_limits(self) -> List[GPUAlert]:
        """Check GPU power draw and generate alerts."""
        alerts = []
        for device_id, power in self.gpu_power.items():
            if power >= self.power_limit_w:
                alerts.append(GPUAlert(
                    device_id=device_id,
                    alert_type="power_limit",
                    level=AlertLevel.WARNING,
                    message=f"GPU {device_id} at power limit: {power}W",
                    value=power,
                    threshold=self.power_limit_w,
                ))
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_user_usage(self, user_id: str) -> Dict[int, int]:
        """Get user's GPU memory usage per device."""
        return self.user_allocations.get(user_id, {})


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def gpu_manager():
    """Create GPU security manager."""
    return MockGPUSecurityManager()


@pytest.fixture
def hot_gpu_manager():
    """Create GPU manager with high temperatures."""
    manager = MockGPUSecurityManager()
    manager.gpu_temperature = {0: 80.0, 1: 85.0}  # Hot GPUs
    return manager


# =============================================================================
# GPU MEMORY ALLOCATION TESTS
# =============================================================================

class TestGPUMemoryAllocation:
    """Test GPU memory allocation security."""
    
    def test_normal_allocation_succeeds(self, gpu_manager):
        """Test normal GPU memory allocation succeeds."""
        success = gpu_manager.allocate_gpu_memory("user1", 0, 4096)  # 4GB
        
        assert success
        assert gpu_manager.gpu_memory_used[0] == 4096
    
    def test_excessive_allocation_blocked(self, gpu_manager):
        """Test allocation exceeding GPU memory is blocked."""
        # Try to allocate more than total GPU memory
        success = gpu_manager.allocate_gpu_memory("user1", 0, 30000)  # 30GB
        
        assert not success
        assert any(a.alert_type == "memory_exhaustion" for a in gpu_manager.alerts)
    
    def test_user_quota_enforced(self, gpu_manager):
        """Test per-user quota is enforced."""
        # Try to allocate more than 50% per user
        success = gpu_manager.allocate_gpu_memory("user1", 0, 15000)  # ~15GB
        
        assert not success
        assert any(a.alert_type == "user_quota_exceeded" for a in gpu_manager.alerts)
    
    def test_multiple_users_isolation(self, gpu_manager):
        """Test multiple users can allocate independently."""
        success1 = gpu_manager.allocate_gpu_memory("user1", 0, 8000)
        success2 = gpu_manager.allocate_gpu_memory("user2", 0, 8000)
        
        assert success1
        assert success2
        assert gpu_manager.gpu_memory_used[0] == 16000


# =============================================================================
# GPU MEMORY RELEASE TESTS
# =============================================================================

class TestGPUMemoryRelease:
    """Test GPU memory release."""
    
    def test_memory_release(self, gpu_manager):
        """Test memory can be released."""
        gpu_manager.allocate_gpu_memory("user1", 0, 4096)
        gpu_manager.release_gpu_memory("user1", 0, 4096)
        
        assert gpu_manager.gpu_memory_used[0] == 0
    
    def test_partial_release(self, gpu_manager):
        """Test partial memory release."""
        gpu_manager.allocate_gpu_memory("user1", 0, 4096)
        gpu_manager.release_gpu_memory("user1", 0, 2048)
        
        assert gpu_manager.gpu_memory_used[0] == 2048


# =============================================================================
# THERMAL PROTECTION TESTS
# =============================================================================

class TestThermalProtection:
    """Test GPU thermal protection."""
    
    def test_normal_temperature_no_alert(self, gpu_manager):
        """Test normal temperature generates no alerts."""
        alerts = gpu_manager.check_thermal_limits()
        
        assert len(alerts) == 0
    
    def test_high_temperature_warning(self, hot_gpu_manager):
        """Test high temperature generates warning."""
        alerts = hot_gpu_manager.check_thermal_limits()
        
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.WARNING for a in alerts)
    
    def test_critical_temperature_alert(self, hot_gpu_manager):
        """Test critical temperature generates critical alert."""
        alerts = hot_gpu_manager.check_thermal_limits()
        
        assert any(a.level == AlertLevel.CRITICAL for a in alerts)


# =============================================================================
# POWER LIMIT TESTS
# =============================================================================

class TestPowerLimits:
    """Test GPU power limit monitoring."""
    
    def test_normal_power_no_alert(self, gpu_manager):
        """Test normal power usage generates no alerts."""
        alerts = gpu_manager.check_power_limits()
        
        assert len(alerts) == 0
    
    def test_power_limit_alert(self, gpu_manager):
        """Test power limit generates alert."""
        gpu_manager.gpu_power[0] = 350.0  # At limit
        
        alerts = gpu_manager.check_power_limits()
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "power_limit"


# =============================================================================
# MULTI-GPU TESTS
# =============================================================================

class TestMultiGPU:
    """Test multi-GPU allocation."""
    
    def test_allocate_across_gpus(self, gpu_manager):
        """Test allocation across multiple GPUs."""
        success1 = gpu_manager.allocate_gpu_memory("user1", 0, 4096)
        success2 = gpu_manager.allocate_gpu_memory("user1", 1, 4096)
        
        assert success1
        assert success2
        assert gpu_manager.gpu_memory_used[0] == 4096
        assert gpu_manager.gpu_memory_used[1] == 4096
    
    def test_invalid_gpu_blocked(self, gpu_manager):
        """Test allocation to invalid GPU is blocked."""
        success = gpu_manager.allocate_gpu_memory("user1", 5, 1024)  # GPU 5 doesn't exist
        
        assert not success


# =============================================================================
# AUDIT SUMMARY
# =============================================================================

class TestGPUSecurityAuditSummary:
    """Generate GPU security audit summary."""
    
    def test_generate_audit_summary(self, gpu_manager, hot_gpu_manager):
        """Run GPU security tests and generate summary."""
        results = {
            "memory_quota_enforced": False,
            "thermal_alerts_generated": False,
            "power_monitoring_active": False,
            "multi_user_isolation": False,
        }
        
        # Test memory quota
        if not gpu_manager.allocate_gpu_memory("user1", 0, 15000):
            results["memory_quota_enforced"] = True
        
        # Test thermal alerts
        alerts = hot_gpu_manager.check_thermal_limits()
        if len(alerts) > 0:
            results["thermal_alerts_generated"] = True
        
        # Test power monitoring
        hot_gpu_manager.gpu_power[0] = 350.0
        power_alerts = hot_gpu_manager.check_power_limits()
        if len(power_alerts) > 0:
            results["power_monitoring_active"] = True
        
        # Test multi-user isolation
        gpu_manager2 = MockGPUSecurityManager()
        gpu_manager2.allocate_gpu_memory("user1", 0, 10000)
        if gpu_manager2.allocate_gpu_memory("user2", 0, 10000):
            results["multi_user_isolation"] = True
        
        print(f"\n{'='*60}")
        print("GPU SECURITY AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Memory Quota Enforced: {'✓' if results['memory_quota_enforced'] else '✗'}")
        print(f"Thermal Alerts: {'✓' if results['thermal_alerts_generated'] else '✗'}")
        print(f"Power Monitoring: {'✓' if results['power_monitoring_active'] else '✗'}")
        print(f"Multi-User Isolation: {'✓' if results['multi_user_isolation'] else '✗'}")
        print(f"{'='*60}\n")
        
        assert all(results.values()), "Some GPU security features not working"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
