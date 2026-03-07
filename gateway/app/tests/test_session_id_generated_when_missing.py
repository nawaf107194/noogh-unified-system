from unittest.mock import MagicMock


from gateway.app.core.agent_controller import AgentController
from gateway.app.core.auth import AuthContext


class TestSessionIdGenerated:
    def test_session_id_generated_when_missing(self):
        """Verify session_id is generated if not provided."""
        mock_kernel = MagicMock()
        mock_kernel.process.return_value = MagicMock(success=True, metadata={})

        controller = AgentController(mock_kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_sess_id"})
        auth = AuthContext(token="t", scopes={"*"})

        # No session_id
        result = controller.process_task("hello", auth)

        assert result.metadata["session_id"] is not None
        assert len(result.metadata["session_id"]) > 0
        assert controller.session_store.get_session(result.metadata["session_id"]) is not None
