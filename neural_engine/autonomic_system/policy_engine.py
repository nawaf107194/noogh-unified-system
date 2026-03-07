"""
Policy Engine - Determines what actions can be auto-executed
Simple rule-based system for now, will evolve to policy.yaml
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Policy engine for action approval
    """
    
    def __init__(self):
        """Initialize policy engine"""
        # Blocked actions (require manual approval)
        self.blocked_actions = [
            "suggest_restart",
            "suggest_cleanup",
            "execute_command",
            "delete_file",
            "modify_config"
        ]
        
        # Always allowed actions (safe)
        self.safe_actions = [
            "log_warning",
            "log_info",
            "log_error",
            "send_notification",
            "record_metric"
        ]
        
        logger.info("✅ PolicyEngine initialized")
    
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
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get current policy configuration"""
        return {
            "blocked_actions": self.blocked_actions,
            "safe_actions": self.safe_actions,
            "confidence_threshold": 0.8
        }


# Singleton instance
_policy_engine_instance = None


def get_policy_engine() -> PolicyEngine:
    """Get singleton policy engine"""
    global _policy_engine_instance
    if _policy_engine_instance is None:
        _policy_engine_instance = PolicyEngine()
    return _policy_engine_instance
