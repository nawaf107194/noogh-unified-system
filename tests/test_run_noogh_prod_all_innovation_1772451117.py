import pytest
from run_noogh_prod_all import shutdown, PROCS

@pytest.fixture
def mock_procs():
    class MockProc:
        def terminate(self):
            pass

        def kill(self):
            pass

    PROCS[:] = [MockProc(), MockProc()]

def test_shutdown_happy_path(mock_procs, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda x: None)
    shutdown()
    assert len(PROCS) == 0

def test_shutdown_empty_procs(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda x: None)
    PROCS.clear()
    shutdown()
    assert len(PROCS) == 0

def test_shutdown_async_behavior(mock_procs, event_loop, monkeypatch):
    async def mock_terminate(self):
        await self.sleep(0.1)

    async def mock_kill(self):
        await self.sleep(0.2)

    monkeypatch.setattr("run_noogh_prod_all.Proc.terminate", mock_terminate)
    monkeypatch.setattr("run_noogh_prod_all.Proc.kill", mock_kill)
    monkeypatch.setattr("time.sleep", lambda x: None)
    shutdown()
    assert len(PROCS) == 0

def test_shutdown_invalid_input_type(monkeypatch):
    PROCS.append(None)
    monkeypatch.setattr("time.sleep", lambda x: None)
    shutdown()
    assert len(PROCS) == 1