"""
Validation and Safety Layer for Noug Neural OS
Validates and simulates actions before execution
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for actions"""

    SAFE = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class ActionCategory(Enum):
    """Categories of actions"""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    NETWORK = "network"
    SYSTEM = "system"


@dataclass
class ValidationResult:
    """Result of validation check"""

    is_valid: bool
    risk_level: RiskLevel
    category: ActionCategory
    issues: List[str]
    warnings: List[str]
    requires_permission: bool
    simulation_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "risk_level": self.risk_level.name,
            "category": self.category.value,
            "issues": self.issues,
            "warnings": self.warnings,
            "requires_permission": self.requires_permission,
            "simulation_result": self.simulation_result,
        }


class SafetyChecker:
    """Checks safety of actions"""

    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"dd\s+if=.*of=/dev/",
        r"mkfs\.",
        r":\(\)\{\s*:\|:&\s*\};:",  # Fork bomb
        r"chmod\s+-R\s+777",
        r"chown\s+-R",
        r"sudo\s+su",
        r"curl.*\|\s*bash",
        r"wget.*\|\s*sh",
    ]

    # Sensitive paths
    SENSITIVE_PATHS = [
        "/etc/passwd",
        "/etc/shadow",
        "/boot",
        "/sys",
        "/proc",
        "/dev",
    ]

    @staticmethod
    def check_command_safety(command: str) -> Tuple[bool, List[str]]:
        """Check if command is safe to execute"""
        issues = []

        # Check for dangerous patterns
        for pattern in SafetyChecker.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                issues.append(f"Dangerous pattern detected: {pattern}")

        # Check for sensitive paths
        for path in SafetyChecker.SENSITIVE_PATHS:
            if path in command:
                issues.append(f"Access to sensitive path: {path}")

        return len(issues) == 0, issues

    @staticmethod
    def check_file_operation_safety(operation: str, path: str, content: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Check if file operation is safe"""
        issues = []

        # Check sensitive paths
        for sensitive in SafetyChecker.SENSITIVE_PATHS:
            if path.startswith(sensitive):
                issues.append(f"Operation on sensitive path: {path}")

        # Check delete operations
        if operation == "delete":
            if path == "/" or path == "/home":
                issues.append(f"Cannot delete critical path: {path}")

        return len(issues) == 0, issues

    @staticmethod
    def check_network_safety(url: str, method: str) -> Tuple[bool, List[str]]:
        """Check if network operation is safe"""
        issues = []
        warnings = []

        # Check for localhost/internal IPs
        if "localhost" in url or "127.0.0.1" in url:
            warnings.append("Accessing localhost")

        # Check for suspicious TLDs
        suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq"]
        if any(tld in url for tld in suspicious_tlds):
            issues.append(f"Suspicious TLD in URL: {url}")

        return len(issues) == 0, issues


class EthicalValidator:
    """Validates actions against ethical guidelines"""

    ETHICAL_RULES = {
        "privacy": [
            "Do not access personal data without permission",
            "Do not share sensitive information",
            "Respect user privacy",
        ],
        "safety": [
            "Do not perform destructive actions without confirmation",
            "Prioritize system stability",
            "Avoid actions that could harm the system",
        ],
        "transparency": [
            "Be transparent about actions taken",
            "Explain reasoning for decisions",
            "Inform user of risks",
        ],
    }

    @staticmethod
    def validate_action(action: str, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate action against ethical guidelines"""
        issues = []

        # Check for privacy violations
        if "password" in action.lower() or "secret" in action.lower():
            if not context.get("user_permission", False):
                issues.append("Action involves sensitive data without permission")

        # Check for destructive actions
        destructive_keywords = ["delete", "remove", "destroy", "wipe"]
        if any(kw in action.lower() for kw in destructive_keywords):
            if not context.get("user_confirmation", False):
                issues.append("Destructive action requires user confirmation")

        return len(issues) == 0, issues


class ActionSimulator:
    """Simulates actions before execution"""

    @staticmethod
    async def simulate_command(command: str) -> Dict[str, Any]:
        """Simulate command execution"""
        return {
            "command": command,
            "simulated": True,
            "predicted_output": "Simulation successful",
            "predicted_changes": [],
            "estimated_duration": 0.1,
            "resource_usage": {"cpu": "low", "memory": "low", "disk": "none"},
        }

    @staticmethod
    async def simulate_file_operation(operation: str, path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Simulate file operation"""
        return {
            "operation": operation,
            "path": path,
            "simulated": True,
            "predicted_result": "success",
            "changes": [f"{operation} on {path}"],
            "reversible": operation != "delete",
        }

    @staticmethod
    async def simulate_network_request(url: str, method: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Simulate network request"""
        return {
            "url": url,
            "method": method,
            "simulated": True,
            "predicted_status": 200,
            "predicted_response": "Simulated response",
            "data_sent": bool(data),
        }


class ValidationLayer:
    """
    Main validation layer that coordinates all validation checks
    """

    def __init__(self):
        self.safety_checker = SafetyChecker()
        self.ethical_validator = EthicalValidator()
        self.simulator = ActionSimulator()
        logger.info("ValidationLayer initialized")

    async def validate_action(
        self, action_type: str, action_data: Dict[str, Any], context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate any action before execution

        Args:
            action_type: Type of action (command, file_op, network, etc.)
            action_data: Action details
            context: Execution context

        Returns:
            ValidationResult with validation details
        """
        issues = []
        warnings = []
        risk_level = RiskLevel.SAFE
        category = ActionCategory.READ
        requires_permission = False
        simulation_result = None

        try:
            if action_type == "command":
                category = ActionCategory.EXECUTE
                command = action_data.get("command", "")

                # Safety check
                is_safe, safety_issues = self.safety_checker.check_command_safety(command)
                issues.extend(safety_issues)

                # Ethical check
                is_ethical, ethical_issues = self.ethical_validator.validate_action(command, context)
                issues.extend(ethical_issues)

                # Simulate
                simulation_result = await self.simulator.simulate_command(command)

                # Determine risk level
                if not is_safe:
                    risk_level = RiskLevel.CRITICAL
                    requires_permission = True
                elif not is_ethical:
                    risk_level = RiskLevel.HIGH
                    requires_permission = True
                else:
                    risk_level = RiskLevel.LOW

            elif action_type == "file_operation":
                operation = action_data.get("operation", "read")
                path = action_data.get("path", "")
                content = action_data.get("content")

                # Determine category
                if operation == "read":
                    category = ActionCategory.READ
                elif operation == "write":
                    category = ActionCategory.WRITE
                elif operation == "delete":
                    category = ActionCategory.DELETE

                # Safety check
                is_safe, safety_issues = self.safety_checker.check_file_operation_safety(operation, path, content)
                issues.extend(safety_issues)

                # Simulate
                simulation_result = await self.simulator.simulate_file_operation(operation, path, content)

                # Determine risk level
                if operation == "delete":
                    risk_level = RiskLevel.HIGH
                    requires_permission = True
                elif not is_safe:
                    risk_level = RiskLevel.CRITICAL
                    requires_permission = True
                else:
                    risk_level = RiskLevel.LOW

            elif action_type == "network":
                category = ActionCategory.NETWORK
                url = action_data.get("url", "")
                method = action_data.get("method", "GET")
                data = action_data.get("data")

                # Safety check
                is_safe, safety_issues = self.safety_checker.check_network_safety(url, method)
                issues.extend(safety_issues)

                # Simulate
                simulation_result = await self.simulator.simulate_network_request(url, method, data)

                # Determine risk level
                if not is_safe:
                    risk_level = RiskLevel.HIGH
                else:
                    risk_level = RiskLevel.LOW

            # Final validation
            is_valid = len(issues) == 0

            return ValidationResult(
                is_valid=is_valid,
                risk_level=risk_level,
                category=category,
                issues=issues,
                warnings=warnings,
                requires_permission=requires_permission,
                simulation_result=simulation_result,
            )

        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return ValidationResult(
                is_valid=False,
                risk_level=RiskLevel.CRITICAL,
                category=ActionCategory.SYSTEM,
                issues=[f"Validation error: {str(e)}"],
                warnings=[],
                requires_permission=True,
            )

    async def batch_validate(self, actions: List[Dict[str, Any]], context: Dict[str, Any]) -> List[ValidationResult]:
        """Validate multiple actions"""
        results = []
        for action in actions:
            result = await self.validate_action(action["type"], action["data"], context)
            results.append(result)
        return results
