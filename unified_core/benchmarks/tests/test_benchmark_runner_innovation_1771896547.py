import signal
from unittest.mock import patch
import logging

def test_setup_kill_switch_happy_path(monkeypatch):
    runner = BenchmarkRunner()
    
    with patch.object(runner, '_shutdown_requested', False), \
         patch.object(runner, '_adapter', None), \
         patch.object(logging, 'warning') as mock_warning:
        
        runner._setup_kill_switch()
        
        assert signal.getsignal(signal.SIGINT) == runner.handle_signal
        assert signal.getsignal(signal.SIGTERM) == runner.handle_signal
        mock_warning.assert_not_called()

def test_setup_kill_switch_adapter_shutdown(monkeypatch):
    adapter = MockAdapter()
    
    runner = BenchmarkRunner()
    runner._adapter = adapter
    
    with patch.object(runner, '_shutdown_requested', False), \
         patch.object(logging, 'warning') as mock_warning:
        
        runner._setup_kill_switch()
        
        assert signal.getsignal(signal.SIGINT) == runner.handle_signal
        assert signal.getsignal(signal.SIGTERM) == runner.handle_signal
        mock_warning.assert_not_called()

def test_setup_kill_switch_shutdown_requested_true(monkeypatch):
    runner = BenchmarkRunner()
    runner._shutdown_requested = True
    
    with patch.object(runner, '_adapter', None), \
         patch.object(logging, 'warning') as mock_warning:
        
        runner._setup_kill_switch()
        
        assert signal.getsignal(signal.SIGINT) == runner.handle_signal
        assert signal.getsignal(signal.SIGTERM) == runner.handle_signal
        mock_warning.assert_not_called()

def test_setup_kill_switch_invalid_input(monkeypatch):
    runner = BenchmarkRunner()
    
    with pytest.raises(TypeError, match="kill switch should be a callable"):
        monkeypatch.setattr(runner, '_shutdown_requested', False)
        monkeypatch.setattr(runner, '_adapter', None)
        
        def invalid_handler(signum, frame):
            raise ValueError("Invalid signal handler")
        
        runner._setup_kill_switch(invalid_handler)

class BenchmarkRunner:
    def __init__(self):
        self._shutdown_requested = False
        self._adapter = None

    def _setup_kill_switch(self):
        def handle_signal(signum, frame):
            logger.warning(f"Kill switch activated (signal {signum})")
            self._shutdown_requested = True
            if self._adapter:
                self._adapter.shutdown()
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

class MockAdapter:
    def shutdown(self):
        pass