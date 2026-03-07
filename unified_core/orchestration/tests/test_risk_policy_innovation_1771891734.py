import pytest

from unified_core.orchestration.risk_policy import classify_operation, RiskLevel

def test_classify_operation_happy_path():
    assert classify_operation("Deploy new server", ["deploy"]) == RiskLevel.SAFE
    assert classify_operation("Run script file", ["script"]) == RiskLevel.RESTRICTED
    assert classify_operation("Execute penetration test", ["penetration", "test"]) == RiskLevel.DANGEROUS

def test_classify_operation_empty_inputs():
    assert classify_operation("", []) == RiskLevel.SAFE
    assert classify_operation(None, None) == RiskLevel.SAFE

def test_classify_operation_boundary_conditions():
    assert classify_operation("Test boundary conditions", ["boundary"]) == RiskLevel.SAFE
    assert classify_operation("Build system", ["build"]) == RiskLevel.RESTRICTED
    assert classify_operation("Attack network", ["attack"]) == RiskLevel.DANGEROUS

def test_classify_operation_case_insensitivity():
    assert classify_operation("Download file", ["DOWNLOAD"]) == RiskLevel.SAFE
    assert classify_operation("EXECUTE code", ["execute"]) == RiskLevel.RESTRICTED
    assert classify_operation("Penetrate network", ["penETRATE"]) == RiskLevel.DANGEROUS

def test_classify_operation_no_keywords():
    assert classify_operation("Check system status", []) == RiskLevel.SAFE