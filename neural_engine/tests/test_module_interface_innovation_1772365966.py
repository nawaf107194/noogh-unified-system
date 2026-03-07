import pytest

from neural_engine.module_interface import ModuleMetadata, ModuleStatus

class TestModuleMetadata:

    def test_is_ready_happy_path(self):
        module_metadata = ModuleMetadata(status=ModuleStatus.READY)
        assert module_metadata.is_ready() is True

    def test_is_ready_edge_case_none_status(self):
        module_metadata = ModuleMetadata(status=None)
        assert module_metadata.is_ready() is False

    def test_is_ready_edge_case_empty_status(self):
        module_metadata = ModuleMetadata(status='')
        assert module_metadata.is_ready() is False

    def test_is_ready_edge_case_boundary_status(self):
        module_metadata = ModuleMetadata(status=ModuleStatus.NOT_READY)
        assert module_metadata.is_ready() is False