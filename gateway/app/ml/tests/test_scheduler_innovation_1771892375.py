import pytest
from gateway.app.ml.scheduler import Scheduler

@pytest.fixture
def scheduler():
    return Scheduler()

def test_peek_queue_happy_path(scheduler):
    # Arrange
    sample_queue = [{'item': 'task1'}, {'item': 'task2'}]
    scheduler.queue = sample_queue
    
    # Act
    result = scheduler.peek_queue()
    
    # Assert
    assert result == sample_queue

def test_peek_queue_empty_queue(scheduler):
    # Arrange
    scheduler.queue = []
    
    # Act
    result = scheduler.peek_queue()
    
    # Assert
    assert result == []

def test_peek_queue_none_queue(scheduler):
    # Arrange
    scheduler.queue = None
    
    # Act
    result = scheduler.peek_queue()
    
    # Assert
    assert result is None

def test_peek_queue_boundary_condition(scheduler):
    # Arrange
    scheduler.queue = [{'item': 'task1'}]
    
    # Act
    result = scheduler.peek_queue()
    
    # Assert
    assert result == [{'item': 'task1'}]

# This case doesn't apply here as the function does not raise errors based on input validation
# def test_peek_queue_error_case(scheduler):
#     # Arrange
#     pass
    
#     # Act & Assert
#     with pytest.raises(YourExpectedException):
#         scheduler.peek_queue()