import pytest

def start_instrumentation():
    print(f"[*] Starting Forensics Tracing. Logging to {LOG_FILE}")

@pytest.fixture
def mock_log_file(monkeypatch):
    monkeypatch.setattr('logging.LOG_FILE', 'test_log.txt')

def test_start_instrumentation_happy_path(mock_log_file, capsys):
    start_instrumentation()
    captured = capsys.readouterr()
    assert "Starting Forensics Tracing. Logging to test_log.txt" in captured.out

def test_start_instrumentation_edge_case_none(capsys):
    with pytest.raises(TypeError) as excinfo:
        start_instrumentation(None)
    assert str(excinfo.value) == "start_instrumentation() takes 0 positional arguments but 1 was given"

def test_start_instrumentation_edge_case_empty_string(capsys):
    with pytest.raises(ValueError) as excinfo:
        start_instrumentation("")
    assert str(excinfo.value) == "LOG_FILE cannot be an empty string"

def test_start_instrumentation_error_case_invalid_input(capsys):
    with pytest.raises(TypeError) as excinfo:
        start_instrumentation(123)
    assert str(excinfo.value) == "start_instrumentation() takes 0 positional arguments but 1 was given"