
from gateway.app.core.session_store import SessionStore


class TestSessionPersistence:
    def test_session_store_persists_last_tasks(self, tmp_path):
        data_dir = str(tmp_path)
        store = SessionStore(base_dir=data_dir)
        session = store.create_session()

        # Add 3 tasks
        store.add_task(session.session_id, "task1", "res1", "execute")
        store.add_task(session.session_id, "task2", "res2", "plan")
        store.add_task(session.session_id, "task3", "res3", "execute")

        reloaded = store.get_session(session.session_id)
        assert len(reloaded.tasks) == 3
        assert reloaded.tasks[0].input_summary == "task1"
        assert reloaded.tasks[2].input_summary == "task3"
