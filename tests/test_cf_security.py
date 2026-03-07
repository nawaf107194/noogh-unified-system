import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from gateway.app.main import app
from gateway.app.core.auth import AuthContext
from gateway.app.core.agent_controller import AgentController
from gateway.app.core.capabilities import CapabilityRequirement, Capability

client = TestClient(app)

# Mock Auth to bypass Token check issues in Test Environment
from gateway.app.core.auth import AuthContext

async def mock_require_bearer():
    return AuthContext(
        user_id="test-user",
        scopes={"*"}, # Admin
        token="test-token"
    )

# Need to import require_bearer to override it
from gateway.app.core.auth import require_bearer
app.dependency_overrides[require_bearer] = mock_require_bearer

def test_read_without_mfa_allowed():
    """Analysis tasks (non-exec) should pass without MFA headers."""
    # We mock controller to avoid running actual LLM
    with patch("noogh.app.api.routes.get_controller") as mock_get_ctrl:
        mock_ctrl = MagicMock()
        mock_get_ctrl.return_value = mock_ctrl
        
        # Controller returns success for a read-only task
        mock_res = MagicMock()
        mock_res.success = True
        mock_res.answer = "Analysis complete."
        mock_res.steps = 1
        mock_ctrl.process_task.return_value = mock_res

        headers = {"Authorization": "Bearer test-token"} # Basic Auth still needed? Yes, require_bearer
        # NO CF Headers
        
        res = client.post("/task", json={"task": "analyze this"}, headers=headers)
        
        # Verify controller was called with mfa_verified=False
        args, kwargs = mock_ctrl.process_task.call_args
        assert kwargs['mfa_verified'] == False
        
        assert res.status_code == 200
        data = res.json()
        assert data["security_level"] == "read"
        assert data["mfa_verified"] == False

def test_admin_requires_mfa_and_token():
    """Admin route requires Cloudflare Headers + Token."""
    
    # 1. Missing Headers -> 403
    res = client.get("/plugins", headers={"Authorization": "Bearer test-token"})
    assert res.status_code == 403
    assert "Cloudflare Access MFA Required" in res.json()["detail"]

    # 2. Present Headers + Correct Token -> 200 (Success)
    # We strip actual plugin logic dependency by mocking
    with patch("noogh.app.plugins.loader.PluginLoader.load_all", return_value={"status": "loaded"}):
        headers = {
            "Authorization": "Bearer test-token",
            "CF-Access-JWT-Assertion": "jwt-fake",
            "CF-Access-Authenticated-User-Email": "admin@noogh.com"
        }
        # /plugins/refresh is POST
        res = client.post("/plugins/refresh", headers=headers)
        assert res.status_code == 200

def test_controller_logic_rejects_exec_without_mfa():
    """Directly test AgentController logic."""
    from gateway.app.core.agent_controller import AgentController
    from gateway.app.core.agent_kernel import AgentResult
    
    kernel = MagicMock()
    ctrl = AgentController(kernel)
    
    # Mock Policy check to return EXECUTE requirement
    cap_req = CapabilityRequirement(
        required={Capability.CODE_EXEC},
        forbidden=set(),
        mode="EXECUTE",
        reason="Computation needed"
    )
    
    with patch("noogh.app.core.policy_engine.PolicyEngine.decide", return_value=cap_req):
        # Case 1: No MFA -> Fail
        res = ctrl.process_task("calc 5", auth=MagicMock(), mfa_verified=False, session_id="123")
        assert res.success == False
        assert "Security Policy Violation" in res.answer
        assert res.error == "MFA_REQUIRED"

        # Case 2: MFA -> Pass (Mock Kernel execution)
        kernel.process.return_value = AgentResult(success=True, answer="25", steps=1)
        res = ctrl.process_task("calc 5", auth=MagicMock(), mfa_verified=True, session_id="123")
        assert res.success == True
        assert res.answer == "25"
