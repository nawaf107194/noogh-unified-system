import pytest
import resource
from unified_core.sandbox_service import SandboxService

class MockSandboxService(SandboxService):
    def __init__(self, max_cpu_seconds=10, max_memory_mb=512, max_output_kb=1024, max_files=100):
        super().__init__()
        self.max_cpu_seconds = max_cpu_seconds
        self.max_memory_mb = max_memory_mb
        self.max_output_kb = max_output_kb
        self.max_files = max_files

def test_set_limits_happy_path():
    service = MockSandboxService()
    service._set_limits()

    # Assert limits are set correctly
    cpu_limit = resource.getrlimit(resource.RLIMIT_CPU)
    assert cpu_limit == (10, 10)

    memory_limit = resource.getrlimit(resource.RLIMIT_AS)
    assert memory_limit == (536870912, 536870912)  # 512 MB in bytes

    file_size_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
    assert file_size_limit == (1048576, 1048576)  # 1024 KB in bytes

    process_limit = resource.getrlimit(resource.RLIMIT_NPROC)
    assert process_limit == (100, 100)

def test_set_limits_edge_cases():
    service = MockSandboxService(
        max_cpu_seconds=None,
        max_memory_mb=0,
        max_output_kb=None,
        max_files=0
    )
    service._set_limits()

    # Assert limits are set to default values (probably infinite or platform-dependent)
    cpu_limit = resource.getrlimit(resource.RLIMIT_CPU)
    assert cpu_limit == (resource.RLIM_INFINITY, resource.RLIM_INFINITY)

    memory_limit = resource.getrlimit(resource.RLIMIT_AS)
    assert memory_limit == (resource.RLIM_INFINITY, resource.RLIM_INFINITY)

    file_size_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
    assert file_size_limit == (resource.RLIM_INFINITY, resource.RLIM_INFINITY)

    process_limit = resource.getrlimit(resource.RLIMIT_NPROC)
    assert process_limit == (0, 0)  # This might vary based on the platform

def test_set_limits_error_cases():
    service = MockSandboxService(
        max_cpu_seconds=-1,
        max_memory_mb=-1,
        max_output_kb=-1,
        max_files=-1
    )
    with pytest.warns(UserWarning, match="Could not set resource limits"):
        service._set_limits()

    # Assert limits are not set and a warning is logged
    cpu_limit = resource.getrlimit(resource.RLIMIT_CPU)
    assert cpu_limit == (resource.RLIM_INFINITY, resource.RLIM_INFINITY)

    memory_limit = resource.getrlimit(resource.RLIMIT_AS)
    assert memory_limit == (resource.RLIM_INFINITY, resource.RLIM_INFINITY)

    file_size_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
    assert file_size_limit == (resource.RLIM_INFINITY, resource.RLIM_INFINITY)

    process_limit = resource.getrlimit(resource.RLIMIT_NPROC)
    assert process_limit == (0, 0)  # This might vary based on the platform