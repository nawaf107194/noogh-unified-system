import pytest

class TestGovernanceEvents:

    @pytest.fixture
    def events_instance(self):
        from unified_core.governance.events import GovernanceEvents
        return GovernanceEvents()

    def test_subscribe_happy_path_all_events(self, events_instance):
        handler = lambda event: None
        events_instance.subscribe(None, handler)
        assert len(events_instance._global_subscribers) == 1
        assert handler in events_instance._global_subscribers

    def test_subscribe_happy_path_specific_event(self, events_instance):
        event_type = "user_created"
        handler = lambda event: None
        events_instance.subscribe(event_type, handler)
        assert event_type in events_instance._subscribers
        assert len(events_instance._subscribers[event_type]) == 1
        assert handler in events_instance._subscribers[event_type]

    def test_subscribe_edge_case_none_event_type(self, events_instance):
        handler = lambda event: None
        events_instance.subscribe(None, handler)
        assert len(events_instance._global_subscribers) == 1
        assert handler in events_instance._global_subscribers

    def test_subscribe_edge_case_empty_event_type(self, events_instance):
        with pytest.raises(KeyError):
            events_instance.subscribe("", lambda event: None)

    def test_subscribe_error_case_invalid_handler(self, events_instance):
        with pytest.raises(TypeError):
            events_instance.subscribe(None, "not a callable")