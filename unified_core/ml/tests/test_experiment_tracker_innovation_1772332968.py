import pytest

class ExperimentTracker:
    def __enter__(self):
        return self

def test_enter_happy_path():
    tracker = ExperimentTracker()
    with tracker as result:
        assert result is tracker

def test_enter_edge_case_none():
    class MockNoneTracker:
        def __enter__(self):
            return None
    tracker = MockNoneTracker()
    with tracker as result:
        assert result is None

def test_enter_async_behavior():
    async def async_enter():
        return ExperimentTracker()

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(async_enter())
        with result as res:
            assert res is result
    finally:
        asyncio.set_event_loop(None)
        loop.close()