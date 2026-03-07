import pytest
from unified_core.governance.events import _audit_logger, GovernanceEvent

class TestAuditLogger:

    @pytest.fixture
    def valid_event(self):
        return GovernanceEvent(
            event_type="LOGIN",
            component="AUTH",
            user_id="user123",
            metadata={"ip": "192.168.1.1"}
        )

    @pytest.fixture
    def empty_metadata_event(self):
        return GovernanceEvent(
            event_type="LOGOUT",
            component="AUTH",
            user_id="user123",
            metadata={}
        )

    @pytest.fixture
    def null_event(self):
        return None

    @pytest.fixture
    def invalid_event_type(self):
        return GovernanceEvent(
            event_type=None,
            component="AUTH",
            user_id="user123",
            metadata={"ip": "192.168.1.1"}
        )

    @pytest.fixture
    def invalid_component(self):
        return GovernanceEvent(
            event_type="LOGIN",
            component=None,
            user_id="user123",
            metadata={"ip": "192.168.1.1"}
        )

    @pytest.fixture
    def invalid_user_id(self):
        return GovernanceEvent(
            event_type="LOGIN",
            component="AUTH",
            user_id=None,
            metadata={"ip": "192.168.1.1"}
        )

    def test_happy_path(self, valid_event, caplog):
        _audit_logger(valid_event)
        assert "GOVERNANCE] LOGIN | component=AUTH | user=user123 | metadata={'ip': '192.168.1.1'}" in caplog.text

    def test_empty_metadata(self, empty_metadata_event, caplog):
        _audit_logger(empty_metadata_event)
        assert "GOVERNANCE] LOGOUT | component=AUTH | user=user123 | metadata={'ip': None}" in caplog.text

    def test_null_input(self, null_event, caplog):
        _audit_logger(null_event)
        assert len(caplog.records) == 0

    def test_invalid_event_type(self, invalid_event_type, caplog):
        _audit_logger(invalid_event_type)
        assert len(caplog.records) == 0

    def test_invalid_component(self, invalid_component, caplog):
        _audit_logger(invalid_component)
        assert len(caplog.records) == 0

    def test_invalid_user_id(self, invalid_user_id, caplog):
        _audit_logger(invalid_user_id)
        assert "GOVERNANCE] LOGIN | component=AUTH | user=None | metadata={'ip': '192.168.1.1'}" in caplog.text