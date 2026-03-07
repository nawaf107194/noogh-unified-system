import pytest

from unified_core.dreamer import Dreamer

@pytest.fixture
def dreamer():
    return Dreamer()

@pytest.mark.parametrize("state, history, expected_actions", [
    (
        {"snapshot": {"average_risk": 45.0, "success_rate": 60.0}},
        [{"metric": "uptime", "value": 75.0}],
        ["SET_GOAL_OPTIMIZE_UPTIME"]
    ),
    (
        {"snapshot": {"average_risk": 45.0, "success_rate": 60.0}},
        [{"metric": "failures", "value": 25.0}],
        []
    ),
    (
        {"snapshot": {}},
        [{"metric": "new_metric", "value": 75.0}],
        ["SET_GOAL_OPTIMIZE_NEW_METRIC"]
    ),
    (
        None,
        None,
        []
    ),
    (
        {},
        [],
        []
    )
])
def test_discover_new_goals(dreamer, state, history, expected_actions):
    dreamer._meta_agent = MockMetaAgent()
    dreamer._discover_new_goals(state, history)
    assert dreamer._meta_agent.register_action.call_args_list == [call(action) for action in expected_actions]

class MockMetaAgent:
    def __init__(self):
        self._actions = {}

    @property
    def actions(self):
        return self._actions

    def register_action(self, action_name):
        if action_name not in self._actions.values():
            self._actions[action_name] = action_name