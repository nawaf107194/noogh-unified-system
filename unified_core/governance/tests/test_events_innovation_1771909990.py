import pytest
from unified_core.governance.events import create, GovernanceEventType

class TestCreateEvent:

    def test_happy_path(self):
        """Test creating an event with normal inputs."""
        event = create(event_type=GovernanceEventType.USER_LOGIN, component="auth", user_id="user123")
        assert event.event_type == GovernanceEventType.USER_LOGIN
        assert event.component == "auth"
        assert event.user_id == "user123"
        assert isinstance(event.timestamp, float)
        assert event.metadata is None

    def test_edge_case_empty_user_id(self):
        """Test creating an event with an empty user ID."""
        event = create(event_type=GovernanceEventType.USER_LOGIN, component="auth", user_id="")
        assert event.event_type == GovernanceEventType.USER_LOGIN
        assert event.component == "auth"
        assert event.user_id == ""
        assert isinstance(event.timestamp, float)
        assert event.metadata is None

    def test_edge_case_none_user_id(self):
        """Test creating an event with a None user ID."""
        event = create(event_type=GovernanceEventType.USER_LOGIN, component="auth", user_id=None)
        assert event.event_type == GovernanceEventType.USER_LOGIN
        assert event.component == "auth"
        assert event.user_id is None
        assert isinstance(event.timestamp, float)
        assert event.metadata is None

    def test_edge_case_default_metadata(self):
        """Test creating an event with default metadata."""
        event = create(event_type=GovernanceEventType.USER_LOGIN, component="auth")
        assert event.event_type == GovernanceEventType.USER_LOGIN
        assert event.component == "auth"
        assert event.user_id is None
        assert isinstance(event.timestamp, float)
        assert event.metadata is None

    def test_error_case_invalid_event_type(self):
        """Test creating an event with an invalid event type."""
        with pytest.raises(ValueError) as exc_info:
            create(event_type="INVALID_TYPE", component="auth")
        assert str(exc_info.value) == "Invalid GovernanceEventType: INVALID_TYPE"

    def test_error_case_invalid_metadata_type(self):
        """Test creating an event with invalid metadata type."""
        with pytest.raises(TypeError) as exc_info:
            create(event_type=GovernanceEventType.USER_LOGIN, component="auth", metadata={"key": 123})
        assert str(exc_info.value) == "Invalid metadata type: <class 'int'>"