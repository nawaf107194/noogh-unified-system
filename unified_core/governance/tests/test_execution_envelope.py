import pytest
from unittest.mock import Mock

from unified_core.governance.execution_envelope import ExecutionEnvelope

def test_happy_path():
    auth_context = "auth_token"
    component = "component_name"
    impact = "impact_type"
    params = {"key": "value"}
    timeout = 60.0

    envelope = ExecutionEnvelope(
        auth_context=auth_context,
        component=component,
        impact=impact,
        params=params,
        timeout=timeout
    )

    assert envelope.auth_context == auth_context
    assert envelope.component == component
    assert envelope.impact == impact
    assert envelope.params == params
    assert envelope.timeout == timeout
    assert envelope.start_time is None
    assert isinstance(envelope.governor, Mock)

def test_empty_auth_context():
    component = "component_name"
    timeout = 60.0

    envelope = ExecutionEnvelope(
        auth_context=None,
        component=component,
        timeout=timeout
    )

    assert envelope.auth_context is None
    assert envelope.component == component
    assert envelope.params == {}
    assert envelope.timeout == timeout
    assert envelope.start_time is None
    assert isinstance(envelope.governor, Mock)

def test_none_params():
    auth_context = "auth_token"
    component = "component_name"
    impact = "impact_type"
    timeout = 60.0

    envelope = ExecutionEnvelope(
        auth_context=auth_context,
        component=component,
        impact=impact,
        params=None,
        timeout=timeout
    )

    assert envelope.auth_context == auth_context
    assert envelope.component == component
    assert envelope.impact == impact
    assert envelope.params == {}
    assert envelope.timeout == timeout
    assert envelope.start_time is None
    assert isinstance(envelope.governor, Mock)

def test_boundary_timeout():
    auth_context = "auth_token"
    component = "component_name"
    impact = "impact_type"

    envelope = ExecutionEnvelope(
        auth_context=auth_context,
        component=component,
        impact=impact,
        timeout=0.5
    )

    assert envelope.auth_context == auth_context
    assert envelope.component == component
    assert envelope.impact == impact
    assert envelope.params == {}
    assert envelope.timeout == 0.5
    assert envelope.start_time is None
    assert isinstance(envelope.governor, Mock)

def test_invalid_params():
    auth_context = "auth_token"
    component = "component_name"
    timeout = 60.0

    with pytest.raises(TypeError):
        ExecutionEnvelope(
            auth_context=auth_context,
            component=component,
            impact="impact_type",
            params="not a dict",
            timeout=timeout
        )