import pytest

class MockPolicyEngine:
    def __init__(self):
        self.blocked_actions = {"block_action"}
        self.safe_actions = {"safe_action"}

    def should_execute(self, proposal: Dict[str, Any]) -> bool:
        """
        Determine if action should be auto-executed
        
        Args:
            proposal: Action proposal from adapter
            
        Returns:
            True if action can be auto-executed
        """
        action = proposal.get("action", "")
        auto_execute = proposal.get("auto_execute", False)
        confidence = proposal.get("confidence", 0.0)
        
        # Rule 1: Blocked actions never execute
        if action in self.blocked_actions:
            logger.warning(f"🔒 Policy blocked: {action}")
            return False
        
        # Rule 2: Safe actions always execute
        if action in self.safe_actions:
            logger.debug(f"✅ Policy approved (safe): {action}")
            return True
        
        # Rule 3: Must have auto_execute flag
        if not auto_execute:
            logger.info(f"⏸️  Manual approval required: {action}")
            return False
        
        # Rule 4: Confidence threshold (0.8)
        if confidence < 0.8:
            logger.warning(f"⚠️  Low confidence ({confidence}): {action}")
            return False
        
        # Passed all checks
        logger.info(f"✅ Policy approved: {action} (confidence={confidence})")
        return True

@pytest.fixture
def policy_engine():
    return MockPolicyEngine()

def test_happy_path(policy_engine):
    proposal = {
        "action": "safe_action",
        "auto_execute": True,
        "confidence": 0.9
    }
    assert policy_engine.should_execute(proposal) == True

def test_edge_case_empty_proposal(policy_engine):
    proposal = {}
    assert policy_engine.should_execute(proposal) == False

def test_edge_case_none_proposal(policy_engine):
    proposal = None
    result = policy_engine.should_execute(proposal)
    assert result == False, f"Expected False, got {result}"

def test_edge_case_boundary_confidence(policy_engine):
    proposal = {
        "action": "safe_action",
        "auto_execute": True,
        "confidence": 0.8
    }
    assert policy_engine.should_execute(proposal) == True

def test_error_case_invalid_input_type_policy_engine():
    with pytest.raises(TypeError):
        proposal = {"action": "block_action", "auto_execute": False, "confidence": 0.7}
        policy_engine = MockPolicyEngine()
        policy_engine.blocked_actions = None
        policy_engine.should_execute(proposal)

def test_error_case_invalid_input_type_proposal():
    with pytest.raises(TypeError):
        proposal = None
        policy_engine = MockPolicyEngine()
        policy_engine.should_execute(proposal)