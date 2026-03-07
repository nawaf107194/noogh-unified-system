import pytest

# Assuming SandboxService is a class defined somewhere in the project
from unified_core.sandbox_service import SandboxService, _sandbox_service

def test_get_sandbox_service_happy_path():
    service1 = get_sandbox_service()
    assert isinstance(service1, SandboxService)
    service2 = get_sandbox_service()
    assert service1 == service2

def test_get_sandbox_service_edge_case_none_global():
    global _sandbox_service
    _sandbox_service = None
    service = get_sandbox_service()
    assert isinstance(service, SandboxService)

def test_get_sandbox_service_edge_case_not_none_global():
    global _sandbox_service
    _sandbox_service = SandboxService()
    service1 = get_sandbox_service()
    service2 = get_sandbox_service()
    assert service1 == service2

# Error cases are not applicable as the function does not raise any exceptions