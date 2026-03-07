import pytest
from unittest.mock import patch
from shared.event_bus import EventBus
import queue
import threading
import time

def test_event_bus_init_happy_path():
    """Test EventBus initialization with default values"""
    bus = EventBus()
    
    # Verify internal state
    assert isinstance(bus._event_queue, queue.Queue)
    assert isinstance(bus._listeners, dict)
    assert isinstance(bus._thread, threading.Thread)
    assert bus._thread.is_alive()
    assert bus._thread.daemon

def test_event_bus_init_edge_cases():
    """Test EventBus initialization with edge cases"""
    # Test with no arguments (should work)
    bus = EventBus()
    
    # Test with unexpected arguments (should fail)
    with pytest.raises(TypeError):
        EventBus(None)
    
    # Verify thread starts and runs
    assert bus._thread.is_alive()
    time.sleep(0.1)  # Give thread a chance to start
    assert bus._thread.is_alive()