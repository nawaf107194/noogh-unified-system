import pytest

# Assuming the function is part of a class, let's assume the class name is UnifiedSystem
from noogh_unified_system.src.start_full_system import UnifiedSystem

@pytest.mark.parametrize("msg", [
    ("This is a normal message"),
    ("Another normal message with more text to ensure boundary testing")
])
def test_info_happy_path(caplog, msg):
    system = UnifiedSystem()
    system.info(msg)
    assert caplog.record_tuples == [("UnifiedSystem", 20, "ℹ️ This is a normal message")], \
           f"Expected log message 'ℹ️ {msg}', but got {caplog.record_tuples}"

def test_info_edge_case_empty_msg(caplog):
    system = UnifiedSystem()
    system.info("")
    assert caplog.record_tuples == [("UnifiedSystem", 20, "ℹ️ ")], \
           "Expected log message 'ℹ️ ', but got an empty string"

def test_info_edge_case_none_msg(caplog):
    system = UnifiedSystem()
    system.info(None)
    assert caplog.record_tuples == [], \
           "Expected no log message when None is passed"

def test_info_async_behavior(caplog, event_loop):
    async def test_coroutine(system):
        await system.info("This is an async message")
    
    system = UnifiedSystem()
    result = event_loop.run_until_complete(test_coroutine(system))
    assert caplog.record_tuples == [("UnifiedSystem", 20, "ℹ️ This is an async message")], \
           f"Expected log message 'ℹ️ This is an async message', but got {caplog.record_tuples}"