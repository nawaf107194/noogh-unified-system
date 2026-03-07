import pytest

def test_eval_expr_happy_path():
    am = AlertManager()
    kpis = {'cpu_usage': '95'}
    assert am._eval_expr('cpu_usage < 100', kpis) == True
    assert am._eval_expr('cpu_usage <= 95', kpis) == True
    assert am._eval_expr('cpu_usage > 80', kpis) == True
    assert am._eval_expr('cpu_usage >= 95', kpis) == True
    assert am._eval_expr('cpu_usage == 95', kpis) == True

def test_eval_expr_edge_cases():
    am = AlertManager()
    kpis = {'memory_usage': '1024'}
    assert am._eval_expr('', kpis) == False
    assert am._eval_expr(None, kpis) == False
    assert am._eval_expr('disk_space <', kpis) == False
    assert am._eval_expr('disk_space <= 500', kpis) == False
    assert am._eval_expr('disk_space > 1024', kpis) == False
    assert am._eval_expr('disk_space >= ', kpis) == False
    assert am._eval_expr('disk_space == 1024', kpis) == False

def test_eval_expr_error_cases():
    am = AlertManager()
    kpis = {'network_latency': '5'}
    # Invalid operator
    assert am._eval_expr('network_latency <> 3', kpis) == False
    # Non-numeric value
    assert am._eval_expr('network_latency < abc', kpis) == False
    # Key not found
    assert am._eval_expr('disk_usage > 500', kpis) == False

def test_eval_expr_async_behavior():
    # This function is synchronous, so no async behavior to test
    pass