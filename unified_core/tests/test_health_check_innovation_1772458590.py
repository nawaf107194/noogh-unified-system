import pytest
from unified_core.health_check import HealthCheck

def test_update_metric_happy_path():
    health_check = HealthCheck()
    component = "component1"
    status = "active"
    
    # Call the function with happy path inputs
    result = health_check.update_metric(component, status)
    
    assert result is None  # No return value expected
    
    # Verify the metric was updated correctly
    assert component in health_check.metrics
    assert health_check.metrics[component]['status'] == status
    assert isinstance(health_check.metrics[component]['last_update'], float)

def test_update_metric_edge_case_empty_component():
    health_check = HealthCheck()
    component = ""
    status = "active"
    
    # Call the function with an empty component name
    with pytest.raises(ValueError) as exc_info:
        health_check.update_metric(component, status)
    
    assert str(exc_info.value) == "Component '' not found."

def test_update_metric_edge_case_none_component():
    health_check = HealthCheck()
    component = None
    status = "active"
    
    # Call the function with a None component name
    with pytest.raises(ValueError) as exc_info:
        health_check.update_metric(component, status)
    
    assert str(exc_info.value) == "Component 'None' not found."

def test_update_metric_error_case_invalid_status():
    # This test is more about ensuring the function handles unexpected inputs gracefully,
    # but since the function doesn't raise specific exceptions for invalid statuses,
    # we don't need to explicitly test that here.
    
    health_check = HealthCheck()
    component = "component1"
    status = "invalid"  # Assuming "invalid" is not a valid status
    
    # Call the function with an invalid status
    result = health_check.update_metric(component, status)
    
    assert result is None  # No return value expected
    
    # Verify the metric was updated correctly even with an invalid status
    assert component in health_check.metrics
    assert health_check.metrics[component]['status'] == status
    assert isinstance(health_check.metrics[component]['last_update'], float)

# Note: Async behavior is not applicable for this synchronous function, so no additional tests are needed.