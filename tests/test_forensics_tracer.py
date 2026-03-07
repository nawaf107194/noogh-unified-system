import pytest

def start_instrumentation():
    print(f"[*] Starting Forensics Tracing. Logging to {LOG_FILE}")

@pytest.fixture
def log_file_patch(mocker):
    return mocker.patch('builtins.LOG_FILE', 'test_log.txt')

def test_start_instrumentation_happy_path(log_file_patch, capsys):
    start_instrumentation()
    captured = capsys.readouterr()
    assert captured.out == "[*] Starting Forensics Tracing. Logging to test_log.txt\n"

def test_start_instrumentation_edge_case_none(caplog):
    with pytest.raises(TypeError) as exc_info:
        start_instrumentation(None)
    assert "NoneType" in str(exc_info.value)

def test_start_instrumentation_edge_case_empty_string(caplog):
    with pytest.raises(ValueError) as exc_info:
        start_instrumentation("")
    assert "empty string" in str(exc_info.value)

def test_start_instrumentation_error_case_invalid_input(caplog):
    with pytest.raises(TypeError) as exc_info:
        start_instrumentation(123)
    assert "expected str, int found" in str(exc_info.value)