import pytest
from unittest.mock import patch, MagicMock, call

PROCS = [MagicMock(), MagicMock()]

@pytest.fixture
def shutdown_func():
    with patch('time.sleep') as mock_sleep, \
         patch('sys.exit') as mock_exit:
        yield lambda: shutdown()

def test_shutdown_happy_path(shutdown_func):
    shutdown_func()
    assert PROCS[0].terminate.call_count == 1
    assert PROCS[1].terminate.call_count == 1
    assert PROCS[0].kill.call_count == 1
    assert PROCS[1].kill.call_count == 1
    mock_exit.assert_called_once_with(0)

@patch('time.sleep')
@patch('sys.exit')
def test_shutdown_empty_procs(shutdown_func, mock_exit):
    global PROCS
    PROCS = []
    shutdown_func()
    assert not PROCS[0].terminate.called
    assert not PROCS[1].terminate.called
    assert not PROCS[0].kill.called
    assert not PROCS[1].kill.called
    mock_exit.assert_called_once_with(0)

@patch('time.sleep')
@patch('sys.exit')
def test_shutdown_all_fail(shutdown_func, mock_exit):
    global PROCS
    PROCS = [MagicMock(side_effect=Exception), MagicMock(side_effect=Exception)]
    shutdown_func()
    assert PROCS[0].terminate.call_count == 1
    assert PROCS[1].terminate.call_count == 1
    assert PROCS[0].kill.call_count == 2
    assert PROCS[1].kill.call_count == 2
    mock_exit.assert_called_once_with(0)

@patch('time.sleep')
@patch('sys.exit')
def test_shutdown_async_behavior(shutdown_func, mock_sleep):
    global PROCS
    def side_effect():
        raise Exception("Async error")
    PROCS = [MagicMock(side_effect=side_effect), MagicMock()]
    with pytest.raises(SystemExit) as exc_info:
        shutdown_func()
    assert exc_info.value.code == 0
    assert PROCS[0].terminate.call_count == 1
    assert PROCS[1].terminate.call_count == 1
    assert PROCS[0].kill.call_count == 2
    assert PROCS[1].kill.call_count == 2