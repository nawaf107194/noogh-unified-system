import pytest
from unittest.mock import MagicMock

class TestProcessManager:

    @pytest.fixture
    def process_manager(self):
        pm = ProcessManager()
        pm._protected_pids = {100, 200}
        pm.PROTECTED_NAMES = ['system', 'kernel']
        pm.GPU_PROCESS_NAMES = ['cuda', 'nvidia']
        return pm

    def test_infer_priority_critical_protected_pid(self, process_manager):
        assert process_manager._infer_priority("some_process", 100) == ProcessPriority.CRITICAL

    def test_infer_priority_critical_protected_name(self, process_manager):
        assert process_manager._infer_priority("systemd", 300) == ProcessPriority.CRITICAL

    def test_infer_priority_high_database_server(self, process_manager):
        assert process_manager._infer_priority("postgres-123", 400) == ProcessPriority.HIGH

    def test_infer_priority_high_gpu_process(self, process_manager):
        assert process_manager._infer_priority("cuda-process", 500) == ProcessPriority.HIGH

    def test_infer_priority_normal(self, process_manager):
        assert process_manager._infer_priority("regular-process", 600) == ProcessPriority.NORMAL

    def test_infer_priority_empty_name(self, process_manager):
        assert process_manager._infer_priority("", 700) == ProcessPriority.NORMAL

    def test_infer_priority_none_name(self, process_manager):
        assert process_manager._infer_priority(None, 800) == ProcessPriority.NORMAL

    def test_infer_priority_invalid_pid_type(self, process_manager):
        with pytest.raises(TypeError):
            process_manager._infer_priority("some_process", "not_an_int")

    def test_infer_priority_invalid_name_type(self, process_manager):
        with pytest.raises(TypeError):
            process_manager._infer_priority(123, 900)

    def test_infer_priority_async_behavior(self, process_manager):
        # Since the function does not involve async operations, this test is not applicable.
        pass