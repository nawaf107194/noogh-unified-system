import pytest

from unified_core.system.memory_summarizer import MemorySummarizer

@pytest.fixture
def memory_summarizer():
    return MemorySummarizer()

def test_setup_happy_path(memory_summarizer):
    cursor = memory_summarizer.cursor
    conn = memory_summarizer.conn

    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="memory_summary";')
    table_exists = cursor.fetchone()

    assert table_exists is not None, "Table 'memory_summary' does not exist."
    assert table_exists[0] == 'memory_summary', "Table name is incorrect."

def test_setup_no_exception_on_existing_table(memory_summarizer):
    # Ensure the table exists before running setup
    cursor = memory_summarizer.cursor
    conn = memory_summarizer.conn

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_summary (
            id INTEGER PRIMARY KEY,
            summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Run the setup method again, which should not raise an exception
    try:
        memory_summarizer.setup()
    except Exception as e:
        pytest.fail(f"Unexpected exception raised: {e}")

def test_setup_no_connection(memory_summarizer):
    memory_summarizer.conn = None

    with pytest.raises(TypeError) as exc_info:
        memory_summarizer.setup()

    assert str(exc_info.value) == "Cannot execute query on a closed connection."

def test_setup_no_cursor(memory_summarizer):
    memory_summarizer.cursor = None

    with pytest.raises(AttributeError) as exc_info:
        memory_summarizer.setup()

    assert str(exc_info.value) == "'NoneType' object has no attribute 'execute'"