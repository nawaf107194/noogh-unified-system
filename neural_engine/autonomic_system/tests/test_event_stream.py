import pytest

from neural_engine.autonomic_system.event_stream import get_event_stream, AutonomicEventStream, _stream_instance

class TestGetEventStream:

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        global _stream_instance
        _stream_instance = None
        yield
        _stream_instance = None

    def test_happy_path(self):
        event_stream1 = get_event_stream()
        event_stream2 = get_event_stream()
        assert event_stream1 is not None
        assert event_stream1 == event_stream2

    def test_edge_cases(self):
        event_stream = get_event_stream(max_events=0)
        assert event_stream is not None

        event_stream = get_event_stream(max_events=None)
        assert event_stream is not None

    def test_async_behavior(self, monkeypatch):
        import asyncio

        async def mock_autonomic_event_stream(*args, **kwargs):
            return AutonomicEventStream()

        monkeypatch.setattr('neural_engine.autonomic_system.event_stream.AutonomicEventStream', mock_autonomic_event_stream)
        event_stream = asyncio.run(get_event_stream())
        assert event_stream is not None

    def test_invalid_inputs(self):
        with pytest.raises(TypeError):
            get_event_stream("1000")

        with pytest.raises(ValueError):
            get_event_stream(max_events=-1)

# Run the tests
if __name__ == "__main__":
    pytest.main()