pytest
from gateway.app.ml.scheduler import Scheduler

@pytest.fixture
def scheduler():
    return Scheduler()

def test_add_topic_happy_path(scheduler):
    queue_position = scheduler.add_topic("mathematics")
    assert queue_position == 1
    assert scheduler.queue[0]["topic"] == "mathematics"
    assert scheduler.queue[0]["priority"] == "high"

def test_add_topic_with_priority(scheduler):
    queue_position = scheduler.add_topic("history", priority="low")
    assert queue_position == 1
    assert scheduler.queue[0]["topic"] == "history"
    assert scheduler.queue[0]["priority"] == "low"

def test_add_topic_empty_string(scheduler, caplog):
    queue_position = scheduler.add_topic("")
    assert queue_position == 1
    assert scheduler.queue[0]["topic"] == ""
    assert scheduler.queue[0]["priority"] == "high"
    assert "Scheduler: Added '' to queue (Priority: high). Total items: 1" in caplog.text

def test_add_topic_none(scheduler, caplog):
    queue_position = scheduler.add_topic(None)
    assert queue_position == 1
    assert scheduler.queue[0]["topic"] is None
    assert scheduler.queue[0]["priority"] == "high"
    assert "Scheduler: Added 'None' to queue (Priority: high). Total items: 1" in caplog.text

def test_add_topic_boundary_conditions(scheduler):
    import string
    long_string = ''.join(string.ascii_letters)
    queue_position = scheduler.add_topic(long_string)
    assert queue_position == 1
    assert scheduler.queue[0]["topic"] == long_string
    assert scheduler.queue[0]["priority"] == "high"

def test_add_topic_invalid_priority(scheduler, caplog):
    queue_position = scheduler.add_topic("geography", priority="medium")
    assert queue_position == 1
    assert scheduler.queue[0]["topic"] == "geography"
    assert scheduler.queue[0]["priority"] == "high"  # Priority defaults to 'high' if invalid
    assert "Scheduler: Added 'geography' to queue (Priority: high). Total items: 1" in caplog.text