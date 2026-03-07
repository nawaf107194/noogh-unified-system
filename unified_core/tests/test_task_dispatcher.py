import pytest

class MockLogger:
    def info(self, message):
        pass

@pytest.fixture
def task_dispatcher():
    from unified_core.task_dispatcher import TaskDispatcher
    dispatcher = TaskDispatcher()
    dispatcher.logger = MockLogger()  # Replace logger with a mock for testing
    return dispatcher

def test_register_specialist_happy_path(task_dispatcher):
    """Test the happy path where we register a specialist."""
    name = "test_specialist"
    specialist = "mock_specialist_instance"
    
    result = task_dispatcher.register_specialist(name, specialist)
    
    assert result is None  # Assuming register_specialist returns None
    assert name in task_dispatcher.specialist_registry
    assert task_dispatcher.specialist_registry[name] == specialist

def test_register_specialist_empty_name(task_dispatcher):
    """Test registering with an empty name."""
    name = ""
    specialist = "mock_specialist_instance"
    
    result = task_dispatcher.register_specialist(name, specialist)
    
    assert result is None  # Assuming register_specialist returns None
    assert len(task_dispatcher.specialist_registry) == 0

def test_register_specialist_none_name(task_dispatcher):
    """Test registering with None as the name."""
    name = None
    specialist = "mock_specialist_instance"
    
    result = task_dispatcher.register_specialist(name, specialist)
    
    assert result is None  # Assuming register_specialist returns None
    assert len(task_dispatcher.specialist_registry) == 0

def test_register_specialist_empty_specialist(task_dispatcher):
    """Test registering with an empty specialist."""
    name = "test_specialist"
    specialist = ""
    
    result = task_dispatcher.register_specialist(name, specialist)
    
    assert result is None  # Assuming register_specialist returns None
    assert len(task_dispatcher.specialist_registry) == 0

def test_register_specialist_none_specialist(task_dispatcher):
    """Test registering with None as the specialist."""
    name = "test_specialist"
    specialist = None
    
    result = task_dispatcher.register_specialist(name, specialist)
    
    assert result is None  # Assuming register_specialist returns None
    assert len(task_dispatcher.specialist_registry) == 0

def test_register_specialist_invalid_name_type(task_dispatcher):
    """Test registering with an invalid name type."""
    name = 123
    specialist = "mock_specialist_instance"
    
    result = task_dispatcher.register_specialist(name, specialist)
    
    assert result is None  # Assuming register_specialist returns None
    assert len(task_dispatcher.specialist_registry) == 0

def test_register_specialist_invalid_specialist_type(task_dispatcher):
    """Test registering with an invalid specialist type."""
    name = "test_specialist"
    specialist = 123
    
    result = task_dispatcher.register_specialist(name, specialist)
    
    assert result is None  # Assuming register_specialist returns None
    assert len(task_dispatcher.specialist_registry) == 0