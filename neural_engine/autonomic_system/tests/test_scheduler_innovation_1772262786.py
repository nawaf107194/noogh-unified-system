import pytest

class Scheduler:
    def __init__(self):
        self.tasks = []
        self.logger = Mock()

    def schedule(self, name: str, interval: int, func: Callable):
        """
        Register a task to run every `interval` seconds.
        """
        self.tasks.append({"name": name, "interval": interval, "func": func, "last_run": 0})
        self.logger.info(f"Scheduled task '{name}' every {interval}s")

@pytest.fixture
def scheduler():
    return Scheduler()

def test_happy_path(scheduler):
    def dummy_func():
        pass

    scheduler.schedule("test_task", 10, dummy_func)
    assert len(scheduler.tasks) == 1
    assert scheduler.tasks[0]["name"] == "test_task"
    assert scheduler.tasks[0]["interval"] == 10
    assert callable(scheduler.tasks[0]["func"])
    assert scheduler.tasks[0]["last_run"] == 0

def test_edge_cases_empty_name(scheduler):
    def dummy_func():
        pass

    with pytest.raises(ValueError) as excinfo:
        scheduler.schedule("", 10, dummy_func)
    assert "name cannot be empty" in str(excinfo.value)

def test_edge_cases_none_name(scheduler):
    def dummy_func():
        pass

    with pytest.raises(ValueError) as excinfo:
        scheduler.schedule(None, 10, dummy_func)
    assert "name cannot be None" in str(excinfo.value)

def test_edge_cases_zero_interval(scheduler):
    def dummy_func():
        pass

    with pytest.raises(ValueError) as excinfo:
        scheduler.schedule("test_task", 0, dummy_func)
    assert "interval must be greater than 0" in str(excinfo.value)

def test_edge_cases_negative_interval(scheduler):
    def dummy_func():
        pass

    with pytest.raises(ValueError) as excinfo:
        scheduler.schedule("test_task", -10, dummy_func)
    assert "interval must be greater than 0" in str(excinfo.value)

def test_async_behavior(mocker):
    scheduler = Scheduler()
    mock_logger_info = mocker.patch.object(scheduler.logger, 'info')

    def async_dummy_func():
        pass

    scheduler.schedule("async_task", 10, async_dummy_func)
    assert len(scheduler.tasks) == 1
    mock_logger_info.assert_called_once_with(f"Scheduled task 'async_task' every 10s")