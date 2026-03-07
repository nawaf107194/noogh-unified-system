import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

class MockEventStream:
    def get_recent_events(self, limit):
        return [
            {"timestamp": "2023-04-01T12:00:00", "data": "event1"},
            {"timestamp": "2023-04-01T12:05:00", "data": "event2"}
        ]

class SelfAwarenessAdapter:
    def __init__(self, stream):
        self.stream = stream

    def observe(self, window_seconds: int = 300) -> Dict[str, Any]:
        try:
            all_events = self.stream.get_recent_events(limit=1000)
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            
            filtered_events = []
            for event in all_events:
                event_time = datetime.fromisoformat(event['timestamp'])
                if event_time >= cutoff_time:
                    filtered_events.append(event)
            
            observation = {
                "window_seconds": window_seconds,
                "total_events": len(filtered_events),
                "events": filtered_events,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📊 Observed {len(filtered_events)} events in {window_seconds}s window")
            return observation
            
        except Exception as e:
            logger.error(f"❌ Observation failed: {e}")
            return {
                "window_seconds": window_seconds,
                "total_events": 0,
                "events": [],
                "error": str(e)
            }

@pytest.fixture
def adapter():
    stream = MockEventStream()
    return SelfAwarenessAdapter(stream)

def test_observe_happy_path(adapter):
    result = adapter.observe(window_seconds=300)
    assert len(result["events"]) == 2
    assert result["total_events"] == 2
    assert "window_seconds" in result

def test_observe_with_empty_window(adapter, monkeypatch):
    monkeypatch.setattr('datetime.datetime.now', MagicMock(return_value=datetime(2023, 4, 1, 12, 0)))
    adapter.stream.get_recent_events.return_value = [
        {"timestamp": "2023-04-01T11:59:50", "data": "event1"}
    ]
    result = adapter.observe(window_seconds=60)
    assert len(result["events"]) == 0
    assert result["total_events"] == 0

def test_observe_with_none_stream(adapter):
    adapter.stream = None
    result = adapter.observe(window_seconds=300)
    assert "error" in result
    assert result["total_events"] == 0
    assert result["events"] == []

# Error case tests are not applicable as the code does not explicitly raise exceptions for input validation.