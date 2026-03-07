import pytest

from unified_core.db.router import RoutingDecision

class TestDBRouter:

    @pytest.fixture
    def db_router(self):
        from unified_core.db.router import DBRouter
        return DBRouter()

    def test_happy_path(self, db_router):
        # Define a simple custom rule
        def custom_rule(table_name: str) -> Optional[RoutingDecision]:
            if table_name == 'users':
                return RoutingDecision('primary')
            return None
        
        # Add the custom rule
        db_router.add_custom_rule(custom_rule)
        
        # Check if the rule was added successfully
        assert len(db_router._custom_rules) == 1
        assert db_router._custom_rules[0] is custom_rule

    def test_edge_case_empty(self, db_router):
        # Test adding an empty function
        def empty_rule(table_name: str) -> Optional[RoutingDecision]:
            pass
        
        db_router.add_custom_rule(empty_rule)
        assert len(db_router._custom_rules) == 1
        assert db_router._custom_rules[0] is empty_rule

    def test_edge_case_none(self, db_router):
        # Test adding None as a rule (should raise TypeError)
        with pytest.raises(TypeError):
            db_router.add_custom_rule(None)

    def test_error_case_invalid_input(self, db_router):
        # Test adding a non-callable object as a rule
        with pytest.raises(TypeError):
            db_router.add_custom_rule("not a callable")

    def test_async_behavior(self, db_router):
        # Define an async custom rule
        async def async_custom_rule(table_name: str) -> Optional[RoutingDecision]:
            if table_name == 'users':
                return RoutingDecision('primary')
            return None
        
        # Add the async custom rule
        db_router.add_custom_rule(async_custom_rule)
        
        # Check if the async rule was added successfully
        assert len(db_router._custom_rules) == 1
        assert db_router._custom_rules[0] is async_custom_rule