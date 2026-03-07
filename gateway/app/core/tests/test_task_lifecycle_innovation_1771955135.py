import pytest
from gateway.app.core.task_lifecycle import TaskState, task_lifecycle  # Assuming task_lifecycle is the class name

def test_task_lifecycle_happy_path():
    task_id = "12345"
    session_id = "session123"
    input_text = "Hello, world!"
    data_dir = "/tmp/noogh_memory"

    instance = task_lifecycle(task_id, session_id, input_text, data_dir)

    assert instance.task_id == task_id
    assert instance.session_id == session_id
    assert instance.input_text == input_text
    assert instance.state == TaskState.RECEIVED
    assert instance.events == [TaskState.RECEIVED.value]
    assert instance.data_dir == data_dir
    assert instance.task_dir == os.path.join(data_dir, ".noogh_memory", "tasks", task_id)
    assert os.path.exists(instance.task_dir)
    assert instance.created_at is not None

def test_task_lifecycle_empty_session_id():
    task_id = "12345"
    input_text = "Hello, world!"
    data_dir = "/tmp/noogh_memory"

    instance = task_lifecycle(task_id, "", input_text, data_dir)

    assert instance.session_id is None
    assert instance.state == TaskState.RECEIVED
    assert instance.events == [TaskState.RECEIVED.value]
    assert os.path.exists(instance.task_dir)

def test_task_lifecycle_none_session_id():
    task_id = "12345"
    input_text = "Hello, world!"
    data_dir = "/tmp/noogh_memory"

    instance = task_lifecycle(task_id, None, input_text, data_dir)

    assert instance.session_id is None
    assert instance.state == TaskState.RECEIVED
    assert instance.events == [TaskState.RECEIVED.value]
    assert os.path.exists(instance.task_dir)

def test_task_lifecycle_empty_data_dir():
    task_id = "12345"
    session_id = "session123"
    input_text = "Hello, world!"
    data_dir = ""

    instance = task_lifecycle(task_id, session_id, input_text, data_dir)

    assert instance.data_dir == "."
    assert instance.task_dir == os.path.join(".", ".noogh_memory", "tasks", task_id)
    assert os.path.exists(instance.task_dir)

def test_task_lifecycle_none_data_dir():
    task_id = "12345"
    session_id = "session123"
    input_text = "Hello, world!"

    instance = task_lifecycle(task_id, session_id, input_text, None)

    assert instance.data_dir == "."
    assert instance.task_dir == os.path.join(".", ".noogh_memory", "tasks", task_id)
    assert os.path.exists(instance.task_dir)

def test_task_lifecycle_invalid_task_id():
    with pytest.raises(ValueError):
        task_lifecycle("invalid taskId", "session123", "Hello, world!", "/tmp/noogh_memory")