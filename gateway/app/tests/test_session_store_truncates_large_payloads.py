
from gateway.app.core.session_store import MAX_TEXT_SIZE, SessionStore


class TestSessionTruncation:
    def test_session_store_truncates_large_payloads(self, tmp_path):
        store = SessionStore(base_dir=str(tmp_path))
        session = store.create_session()

        huge_text = "A" * (MAX_TEXT_SIZE + 1000)
        store.add_task(session.session_id, huge_text, "res", "execute")

        reloaded = store.get_session(session.session_id)
        saved_task = reloaded.tasks[0]

        assert len(saved_task.input_summary) == MAX_TEXT_SIZE
        assert len(saved_task.input_summary) < len(huge_text)
