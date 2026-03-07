from datetime import datetime, timedelta
from unittest.mock import Mock

from neural_engine.autonomy.decision_engine import DecisionEngine, Observation, Rule, Decision

@pytest.fixture
def decision_engine():
    engine = DecisionEngine()
    engine.rules = {
        'rule1': Rule(id='rule1', enabled=True, metric='temperature', cooldown_seconds=30, condition=lambda x: x > 30, action_type='alert', severity='high', message_template='Temperature is too high: {value}', command='alarm on'),
        'rule2': Rule(id='rule2', enabled=False, metric='pressure', cooldown_seconds=60, condition=lambda x: x < 10, action_type='shutdown', severity='critical', message_template='Pressure is too low: {value}', command='system shutdown')
    }
    return engine

def test_happy_path(decision_engine):
    observation = Observation(metric='temperature', value=35)
    decision = decision_engine.evaluate(observation)
    assert decision
    assert decision.rule_id == 'rule1'
    assert decision.observation.value == 35
    assert decision.severity == 'high'

def test_enabled_rule_with_no_condition_match(decision_engine):
    observation = Observation(metric='temperature', value=20)
    decision = decision_engine.evaluate(observation)
    assert not decision

def test_disabled_rule(decision_engine):
    observation = Observation(metric='pressure', value=5)
    decision = decision_engine.evaluate(observation)
    assert not decision

def test_empty_rules(decision_engine):
    decision_engine.rules = {}
    observation = Observation(metric='temperature', value=35)
    decision = decision_engine.evaluate(observation)
    assert not decision

def test_none_observation(decision_engine):
    decision = decision_engine.evaluate(None)
    assert not decision

def test_invalid_metric_observation(decision_engine):
    observation = Observation(metric='humidity', value=50)
    decision = decision_engine.evaluate(observation)
    assert not decision

def test_rule_with_exception_in_condition(decision_engine, caplog):
    rule = Rule(id='rule3', enabled=True, metric='temperature', cooldown_seconds=30, condition=lambda x: 1 / 0, action_type='alert', severity='high', message_template='Temperature is too high: {value}', command='alarm on')
    observation = Observation(metric='temperature', value=35)
    decision_engine.rules['rule3'] = rule
    decision = decision_engine.evaluate(observation)
    assert not decision
    assert 'Error evaluating rule' in caplog.text

def test_rule_with_cooldown(observation):
    engine = DecisionEngine()
    rule = Rule(id='rule4', enabled=True, metric='temperature', cooldown_seconds=30, condition=lambda x: True, action_type='alert', severity='high', message_template='Temperature is too high: {value}', command='alarm on')
    observation = Observation(metric='temperature', value=35)
    decision_engine.rules = {'rule4': rule}
    
    # First execution
    decision = decision_engine.evaluate(observation)
    assert decision
    
    # Reset last_triggered to simulate cooldown period
    rule.last_triggered = datetime.now() - timedelta(seconds=29)
    
    # Second execution within cooldown period
    decision = decision_engine.evaluate(observation)
    assert not decision
    
    # Third execution after cooldown period
    rule.last_triggered = datetime.now() - timedelta(seconds=31)
    decision = decision_engine.evaluate(observation)
    assert decision