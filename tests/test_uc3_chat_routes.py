import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from gateway.app.console.routes import router, ChatReq
from gateway.app.console import routes

# Setup simple app for testing the router
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)

client = TestClient(app)

@pytest.fixture
def mock_settings():
    with patch("gateway.app.console.routes.settings") as mock:
        mock.UC3_TOKEN = None  # Disable auth for tests
        mock.GATEWAY_LOG = "/tmp/gateway.log"
        mock.NEURAL_LOG = "/tmp/neural.log"
        yield mock

@pytest.fixture
def mock_llm():
    with patch("gateway.app.console.routes.llm") as mock:
        # Default behavior: generic intent
        mock.classify_intent = AsyncMock(return_value={
            "mode": "OBSERVE", 
            "confidence": 0.9, 
            "summary": "test", 
            "requested_actions": [],
            "safety_notes": "none"
        })
        mock.reason = AsyncMock(return_value={
            "conclusion": "Reasoning complete",
            "confidence": 0.8,
            "reasoning_trace": ["step1", "step2"],
            "suggested_actions": []
        })
        yield mock

@pytest.fixture
def mock_context():
    with patch("gateway.app.console.routes.build_context", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "metrics": {
                "cpu_util": 10.5,
                "mem_used_gb": 4.2,
                "gpu_util": 25.0,
                "gpu_vram_mb": 8192
            },
            "gateway_log_tail": "log_line_1\nlog_line_2",
            "neural_log_tail": "neural_line_1"
        }
        yield mock

@pytest.fixture
def mock_dispatch_execute():
    with patch("gateway.app.console.routes.dispatch_execute", new_callable=AsyncMock) as mock:
        mock.return_value = {"message": "Action executed", "status": "success"}
        yield mock

@pytest.fixture
def mock_policy():
    with patch("gateway.app.console.routes.evaluate") as mock:
        decision = MagicMock()
        decision.allowed = True
        decision.mode = "OBSERVE"
        decision.sanitized_actions = []
        mock.return_value = decision
        yield mock

@pytest.fixture
def mock_audit():
    with patch("gateway.app.console.routes.audit_event") as mock:
        mock.return_value = "audit_123"
        yield mock

def test_observe_does_not_call_llm_reason(mock_llm, mock_context, mock_policy, mock_settings, mock_audit):
    # Setup intent to OBSERVE
    mock_llm.classify_intent.return_value = {"mode": "OBSERVE", "confidence": 1.0, "requested_actions": []}
    mock_policy.return_value.mode = "OBSERVE"
    
    resp = client.post("/uc3/chat", json={"text": "system status"})
    
    assert resp.status_code == 200
    data = resp.json()
    
    # Contract checks
    assert data["ok"] is True
    assert data["mode"] == "OBSERVE"
    assert data["executed"] is False
    assert data["confirmation_required"] is False
    assert "metrics_preview" in data
    
    # Verify content comes from context, not LLM
    assert "MODE: OBSERVE" in data["message"]
    assert "System Status" in data["message"]
    assert "CPU: 10.5%" in data["message"]
    
    # Ensure reason() was NOT called
    mock_llm.reason.assert_not_called()

def test_observe_handles_missing_metrics(mock_llm, mock_context, mock_policy, mock_settings, mock_audit):
    # Setup intent to OBSERVE but context missing metrics
    mock_llm.classify_intent.return_value = {"mode": "OBSERVE", "confidence": 1.0, "requested_actions": []}
    mock_policy.return_value.mode = "OBSERVE"
    mock_context.return_value = {"metrics": {}} # Empty metrics
    
    resp = client.post("/uc3/chat", json={"text": "system status"})
    data = resp.json()
    
    assert "UNAVAILABLE" in data["message"]
    assert "System metrics not returned" in data["message"]

def test_analyze_calls_llm_reason(mock_llm, mock_context, mock_policy, mock_settings, mock_audit):
    # Setup intent to ANALYZE
    mock_llm.classify_intent.return_value = {"mode": "ANALYZE", "confidence": 1.0, "requested_actions": []}
    mock_policy.return_value.mode = "ANALYZE"
    
    resp = client.post("/uc3/chat", json={"text": "why is cpu high?"})
    
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["mode"] == "ANALYZE"
    assert data["message"] == "Reasoning complete"
    
    # Ensure reason() WAS called
    mock_llm.reason.assert_called_once()

def test_analyze_fails_on_bad_llm_output(mock_llm, mock_context, mock_policy, mock_settings, mock_audit):
    # Setup intent to ANALYZE with bad output
    mock_llm.classify_intent.return_value = {"mode": "ANALYZE", "confidence": 1.0, "requested_actions": []}
    mock_policy.return_value.mode = "ANALYZE"
    mock_llm.reason.return_value = {"conclusion": "Processing complete"} # Forbidden phrase
    
    resp = client.post("/uc3/chat", json={"text": "bad analysis"})
    data = resp.json()
    
    assert "FAILURE" in data["message"]

def test_execute_requires_confirmation(mock_llm, mock_context, mock_policy, mock_dispatch_execute, mock_settings, mock_audit):
    # Setup intent to EXECUTE, but NO confirm flag
    mock_llm.classify_intent.return_value = {"mode": "EXECUTE", "confidence": 1.0}
    mock_policy.return_value.mode = "EXECUTE"
    mock_policy.return_value.sanitized_actions = [{"action": "dream.start", "args": {}}]
    
    resp = client.post("/uc3/chat", json={"text": "start dream"})
    
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["mode"] == "EXECUTE"
    assert data["executed"] is False
    assert data["confirmation_required"] is True
    # Verify strict message format
    assert "Risk:" in data["message"]
    # We now expect attribution like "via Registry" or "via Heuristic"
    assert "via" in data["message"]
    assert "CONFIRMATION REQUIRED" in data["message"]
    
    mock_dispatch_execute.assert_not_called()

def test_execute_runs_with_confirmation(mock_llm, mock_context, mock_policy, mock_dispatch_execute, mock_settings, mock_audit):
    # Setup intent to EXECUTE, WITH confirm flag
    mock_llm.classify_intent.return_value = {"mode": "EXECUTE", "confidence": 1.0}
    mock_policy.return_value.mode = "EXECUTE"
    mock_policy.return_value.sanitized_actions = [{"action": "dream.start", "args": {}}]
    
    # Send confirm=True
    resp = client.post("/uc3/chat", json={"text": "start dream", "confirm": True})
    
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["mode"] == "EXECUTE"
    assert data["executed"] is True
    assert data["confirmation_required"] is False
    assert "EXECUTE COMPLETE" in data["message"]
    
    mock_dispatch_execute.assert_called_once()
