import pytest
from shared.event_bus import EventBus
import threading
import queue

def test_init_happy_path():
    # Arrange
    event_bus = EventBus()

    # Act & Assert
    assert isinstance(event_bus._event_queue, queue.Queue)
    assert isinstance(event_bus._listeners, dict)
    assert isinstance(event_bus._thread, threading.Thread)
    assert event_bus._thread.is_alive() is True

def test_init_edge_case_no_exception():
    # Arrange
    event_bus = EventBus()

    # Act & Assert
    assert isinstance(event_bus._event_queue, queue.Queue)
    assert isinstance(event_bus._listeners, dict)
    assert isinstance(event_bus._thread, threading.Thread)
    assert event_bus._thread.is_alive() is True

def test_init_edge_case_empty_values():
    # Arrange
    with pytest.raises(Exception):
        EventBus(None, None)

def test_init_error_case_invalid_input():
    # Arrange & Act & Assert
    with pytest.raises(TypeError):
        EventBus(123)

def test_init_async_behavior():
    # Arrange
    event_bus = EventBus()

    # Act
    def check_thread_alive():
        assert event_bus._thread.is_alive() is True

    # Run the check in a separate thread to simulate async behavior
    check_thread = threading.Thread(target=check_thread_alive)
    check_thread.start()
    check_thread.join(timeout=1)  # Wait for 1 second to ensure the check runs

if __name__ == "__main__":
    pytest.main()