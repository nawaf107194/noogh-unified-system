import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from gateway.app.main import app
from gateway.app.core.auth import AuthContext, require_bearer
from gateway.app.core.policy_engine import PolicyEngine
from gateway.app.core.capabilities import CapabilityRequirement, Capability, Capability
from gateway.app.core.refusal import RefusalResponse

client = TestClient(app)

# --- MOCK AUTH (To bypass Token check for Unit Tests) ---
async def mock_require_bearer():
    return AuthContext(
        scopes={"*"}, 
        token="test-token"
    )
app.dependency_overrides[require_bearer] = mock_require_bearer


# ===================================================================
# 1. TEST POLICY ENGINE LOGIC (Directly)
# ===================================================================

def test_policy_allows_simple_math():
    """Verify math requests allow EXECUTE."""
    decision = PolicyEngine.decide("calculate sum of 1 to 100")
    assert isinstance(decision, CapabilityRequirement)
    assert decision.mode == "EXECUTE"
    assert Capability.CODE_EXEC in decision.required

def test_policy_allows_read_only_analysis():
    """Verify 'explain' requests allow safe execution (no tools)."""
    decision = PolicyEngine.decide("explain how photosynthesis works")
    assert isinstance(decision, CapabilityRequirement)
    assert decision.mode == "EXECUTE"
    assert len(decision.required) == 0 # No tools needed
    assert "Conversational" in decision.reason

def test_policy_rejects_shell():
    """Verify shell commands are rejected."""
    decision = PolicyEngine.decide("run ls -la in shell")
    assert isinstance(decision, RefusalResponse)
    assert decision.code == "ForbiddenRequest"

def test_no_mode_hint_error():
    """Verify calling decide() without mode_hint works (default)."""
    try:
        decision = PolicyEngine.decide("hi")
        assert isinstance(decision, CapabilityRequirement)
    except TypeError as e:
        pytest.fail(f"PolicyEngine signature error: {e}")

def test_policy_defaults_to_safe_chat():
    """Verify generic inputs default to safe execution, not rejection."""
    # "Who is these?" matches SAFE_TRIGGERS, but let's try something completely random
    decision = PolicyEngine.decide("The weather is nice today")
    assert isinstance(decision, CapabilityRequirement)
    assert decision.mode == "EXECUTE"
    assert len(decision.required) == 0
    assert "Defaulting to safe" in decision.reason

# ===================================================================
# 2. TEST CONTROLLER / ROUTES (Security Enforcements)
# ===================================================================

def test_read_only_works_without_2fa():
    """
    Simulate a request that resolves to 'Open Read' (Safe).
    Should succeed WITHOUT Cloudflare Headers.
    """
    # Mock Policy to return SAFE requirement
    mock_safe_dec = CapabilityRequirement(
        required=set(), # No tools
        forbidden=set(),
        mode="EXECUTE",
        reason="Conversational"
    )
    
    with patch("noogh.app.core.policy_engine.PolicyEngine.decide", return_value=mock_safe_dec):
        # Using a valid token (handled by mock_require_bearer) but NO Cloudflare Headers
        res = client.post("/task", json={"task": "hi"})
        
        # Should pass because Controller checks sensitive_caps and set() is not sensitive
        assert res.status_code == 200
        data = res.json()
        assert data["success"] == True
        assert data["security_level"] == "read"
        assert data["mfa_verified"] == False

def test_execute_requires_cloudflare_headers():
    """
    Simulate a request that resolves to 'EXECUTE' (Sensitive).
    Should FAIL WITHOUT Cloudflare Headers.
    """
    # Mock Policy to return SENSITIVE requirement
    mock_exec_dec = CapabilityRequirement(
        required={Capability.CODE_EXEC},
        forbidden=set(),
        mode="EXECUTE",
        reason="Math"
    )
    
    with patch("noogh.app.core.policy_engine.PolicyEngine.decide", return_value=mock_exec_dec):
        # 1. No Headers -> Blocked by Controller Logic
        res = client.post("/task", json={"task": "calculate 1+1"})
        
        # It should return 200 OK (HTTP) but with success=False in body 
        # because the Controller logic catches it and returns an 'UNSUPPORTED' result.
        # Wait, user requirement says "3) ... -> 403 Forbidden" for ROUTES.
        # But for /task (AgentController), it usually returns a refusal result.
        # Let's check agent_controller implementation.
        # It returns AgentResult(success=False, error="MFA_REQUIRED").
        
        assert res.status_code == 200
        data = res.json()
        assert data["success"] == False
        assert data["error"] == "MFA_REQUIRED"
        assert "Security Policy Violation" in data["answer"]

        # 2. With Headers -> Allowed
        headers = {
            "CF-Access-JWT-Assertion": "jwt123",
            "CF-Access-Authenticated-User-Email": "test@noogh.com",
            "Authorization": "Bearer test-token"
        }
        
        # We need to mock the actual execution too otherwise kernel crashes in mock env
        with patch("noogh.app.core.agent_controller.AgentController._execute_execution_mode") as mock_exec:
             mock_exec.return_value = MagicMock(success=True, answer="2", steps=1, error=None)
             
             res = client.post("/task", json={"task": "calculate 1+1"}, headers=headers)
             
             assert res.status_code == 200
             data = res.json()
             assert data["success"] == True
             assert data["security_level"] == "secure"
             assert data["mfa_verified"] == True

def test_admin_route_hard_block():
    """Admin routes MUST block if no headers (Middleware level)."""
    # This logic is in routes.py check, raising HTTPException 403
    
    # 1. No Headers
    res = client.get("/plugins", headers={"Authorization": "Bearer test-token"})
    assert res.status_code == 403
    assert "Cloudflare Access MFA Required" in res.json()["detail"]
    
    # 2. With Headers
    with patch("noogh.app.plugins.loader.PluginLoader.load_all", return_value={}):
        headers = {
            "CF-Access-JWT-Assertion": "jwt123",
            "CF-Access-Authenticated-User-Email": "admin@noogh.com",
            # Authorization header handled by test client
            "Authorization": "Bearer test-token"
        }
        # Assuming /plugins requires admin -> 200
        # Actually /plugins calls require_admin which calls is_mfa_verified
        # And we mocked require_bearer but not require_admin? 
        # require_admin depends on require_bearer. 
        # But require_admin ALSO checks headers explicitly.
        
        # Use POST /plugins/refresh for test
        res = client.post("/plugins/refresh", headers=headers)
        assert res.status_code == 200
