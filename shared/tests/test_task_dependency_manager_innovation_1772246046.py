import pytest

from shared.task_dependency_manager import TaskDependencyManager

class TestTaskDependencyManager:

    @pytest.fixture
    def manager(self):
        return TaskDependencyManager()

    def test_happy_path(self, manager):
        assert isinstance(manager.tasks, dict)
        assert isinstance(manager.dependencies, dict)

    def test_empty_input(self, manager):
        # No need to explicitly check for empty input as the __init__ method does not accept any parameters
        assert isinstance(manager.tasks, dict)
        assert isinstance(manager.dependencies, dict)

    def test_none_input(self):
        with pytest.raises(TypeError) as exc_info:
            TaskDependencyManager(None)
        assert str(exc_info.value) == "__init__() takes 1 positional argument but 2 were given"

    def test_boundary_conditions(self):
        # No need to explicitly check boundary conditions as the __init__ method does not accept any parameters
        manager = TaskDependencyManager()
        assert isinstance(manager.tasks, dict)
        assert isinstance(manager.dependencies, dict)

    def test_error_cases(self):
        with pytest.raises(TypeError) as exc_info:
            TaskDependencyManager("invalid_input")
        assert str(exc_info.value) == "__init__() takes 1 positional argument but 2 were given"