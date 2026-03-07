import pytest
from datetime import datetime, timedelta
from neural_engine.autonomy.decision_engine import DecisionEngine, Observation, Rule

@pytest.fixture
def decision_engine():
    engine = DecisionEngine()
    rule1 = Rule(id=1, enabled=True, metric='temp', cooldown_seconds=0, condition=lambda x: x > 30)
    rule2 = Rule(id=2, enabled=False, metric='temp', cooldown_seconds=0, condition=lambda x: x < 10)
    engine.rules = {rule1.id: rule1, rule2.id: rule2}
    return engine

def test_happy_path(decision_engine):
    observation = Observation(metric='temp', value=35)
    decision = decision_engine.evaluate(observation)
    assert decision is not None
    assert decision.rule_id == 1
    assert decision.observation.value == 35
    assert decision.action_type == rule1.action_type
    assert decision.severity == rule1.severity
    assert decision.message.startswith('temp: 35')
    assert decision.command == rule1.command

def test_disabled_rule(decision_engine):
    observation = Observation(metric='temp', value=20)
    decision = decision_engine.evaluate(observation)
    assert decision is None

def test_cooldown_triggering(decision_engine):
    rule1.last_triggered = datetime.now() - timedelta(seconds=5)
    observation = Observation(metric='temp', value=35)
    decision = decision_engine.evaluate(observation)
    assert decision is not None
    assert rule1.last_triggered == datetime.now()

def test_cooldown_not_triggering(decision_engine):
    rule1.last_triggered = datetime.now() - timedelta(seconds=4)
    observation = Observation(metric='temp', value=35)
    decision = decision_engine.evaluate(observation)
    assert decision is None

def test_invalid_observation_metric(decision_engine):
    observation = Observation(metric='pressure', value=35)
    decision = decision_engine.evaluate(observation)
    assert decision is None

def test_empty_rule_set(decision_engine):
    decision_engine.rules = {}
    observation = Observation(metric='temp', value=35)
    decision = decision_engine.evaluate(observation)
    assert decision is None

async def test_async_behavior(decision_engine, async_loop):
    rule1.condition = lambda x: x > 30
    observation = Observation(metric='temp', value=35)
    
    async def async_condition(value):
        await asyncio.sleep(1)  # Simulate an async operation
        return value > 30
    
    rule1.condition = async_condition
    decision = await async_loop.run_in_executor(None, decision_engine.evaluate, observation)
    assert decision is not None