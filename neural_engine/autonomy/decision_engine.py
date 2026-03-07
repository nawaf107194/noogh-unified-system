"""
NOOGH Decision Engine
======================
The brain of autonomous operations.
Observes system state → Evaluates rules → Decides actions → Executes safely.

Philosophy:
- LLM = Advisor (يفسّر، يقترح، يشرح)
- Decision Engine = Executor (ينفذ، يراقب، يقرر)
"""

import asyncio
import logging
import subprocess
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ActionSeverity(Enum):
    """Severity levels for actions."""
    INFO = "info"           # Just log
    WARNING = "warning"     # Log + notify
    CRITICAL = "critical"   # Log + notify + may need intervention
    EMERGENCY = "emergency" # Immediate action required


class ActionType(Enum):
    """Types of autonomous actions."""
    ALERT = "alert"                 # Send notification
    LOG = "log"                     # Log message
    SUGGEST = "suggest"             # Suggest action (no execution)
    EXECUTE = "execute"             # Execute command
    SELF_HEAL = "self_heal"         # Attempt to fix issue
    ESCALATE = "escalate"           # Escalate to human


@dataclass
class Observation:
    """Represents a system observation."""
    metric: str
    value: Any
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        return f"{self.metric}: {self.value}{self.unit}"


@dataclass
class Decision:
    """Represents a decision made by the engine."""
    rule_id: str
    observation: Observation
    action_type: ActionType
    severity: ActionSeverity
    message: str
    command: Optional[str] = None
    executed: bool = False
    result: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Rule:
    """A decision rule: IF condition THEN action."""
    id: str
    name: str
    description: str
    metric: str
    condition: Callable[[Any], bool]
    action_type: ActionType
    severity: ActionSeverity
    message_template: str
    command: Optional[str] = None
    cooldown_seconds: int = 300  # Don't trigger same rule twice in 5 minutes
    enabled: bool = True
    last_triggered: Optional[datetime] = None


class DecisionEngine:
    """
    🧠 The Decision Engine
    
    Evaluates rules against observations and executes appropriate actions.
    """
    
    def __init__(self):
        self.rules: Dict[str, Rule] = {}
        self.decisions: List[Decision] = []
        self.observations: List[Observation] = []
        self.max_history = 100
        
        # Register default rules
        self._register_default_rules()
        
        logger.info("🧠 Decision Engine initialized")
    
    def _register_default_rules(self):
        """Register default monitoring rules."""
        
        # === MEMORY RULES ===
        self.register_rule(Rule(
            id="mem_critical",
            name="Memory Critical",
            description="Memory usage above 90%",
            metric="memory_percent",
            condition=lambda x: x > 90,
            action_type=ActionType.ALERT,
            severity=ActionSeverity.CRITICAL,
            message_template="🚨 ذاكرة حرجة! الاستخدام: {value}%",
            cooldown_seconds=300
        ))
        
        self.register_rule(Rule(
            id="mem_warning",
            name="Memory Warning",
            description="Memory usage above 80%",
            metric="memory_percent",
            condition=lambda x: 80 < x <= 90,
            action_type=ActionType.ALERT,
            severity=ActionSeverity.WARNING,
            message_template="⚠️ ذاكرة عالية! الاستخدام: {value}%",
            cooldown_seconds=600
        ))
        
        self.register_rule(Rule(
            id="mem_low_available",
            name="Low Available Memory",
            description="Less than 2GB available",
            metric="memory_available_gb",
            condition=lambda x: x < 2,
            action_type=ActionType.SUGGEST,
            severity=ActionSeverity.WARNING,
            message_template="💡 الذاكرة المتاحة قليلة ({value}GB). يُنصح بإغلاق بعض البرامج.",
            cooldown_seconds=600
        ))
        
        # === DISK RULES ===
        self.register_rule(Rule(
            id="disk_critical",
            name="Disk Critical",
            description="Disk usage above 95%",
            metric="disk_percent",
            condition=lambda x: x > 95,
            action_type=ActionType.ALERT,
            severity=ActionSeverity.EMERGENCY,
            message_template="🚨 القرص ممتلئ تقريباً! الاستخدام: {value}%",
            cooldown_seconds=60
        ))
        
        self.register_rule(Rule(
            id="disk_warning",
            name="Disk Warning", 
            description="Disk usage above 85%",
            metric="disk_percent",
            condition=lambda x: 85 < x <= 95,
            action_type=ActionType.SUGGEST,
            severity=ActionSeverity.WARNING,
            message_template="⚠️ مساحة القرص محدودة ({value}%). يُنصح بتنظيف الملفات غير الضرورية.",
            cooldown_seconds=1800
        ))
        
        # === CPU RULES ===
        self.register_rule(Rule(
            id="cpu_high",
            name="CPU High",
            description="CPU usage above 90% for extended period",
            metric="cpu_percent",
            condition=lambda x: x > 90,
            action_type=ActionType.LOG,
            severity=ActionSeverity.WARNING,
            message_template="⚡ المعالج تحت ضغط عالي: {value}%",
            cooldown_seconds=120
        ))
        
        # === SERVICE RULES ===
        self.register_rule(Rule(
            id="service_down",
            name="Service Down",
            description="Neural service not running",
            metric="neural_service_active",
            condition=lambda x: not x,
            action_type=ActionType.SELF_HEAL,
            severity=ActionSeverity.CRITICAL,
            message_template="🔴 خدمة Neural متوقفة! محاولة إعادة التشغيل...",
            command="systemctl restart noogh-neural",
            cooldown_seconds=300
        ))
        
        # === GPU RULES ===
        self.register_rule(Rule(
            id="gpu_hot",
            name="GPU Temperature High",
            description="GPU temperature above 80°C",
            metric="gpu_temp",
            condition=lambda x: x > 80,
            action_type=ActionType.ALERT,
            severity=ActionSeverity.WARNING,
            message_template="🌡️ GPU ساخن! درجة الحرارة: {value}°C",
            cooldown_seconds=300
        ))
        
        logger.info(f"📋 Registered {len(self.rules)} default rules")
    
    def register_rule(self, rule: Rule):
        """Register a new decision rule."""
        self.rules[rule.id] = rule
        logger.debug(f"Registered rule: {rule.id}")
    
    def observe(self, metric: str, value: Any, unit: str = "") -> Observation:
        """Record an observation."""
        obs = Observation(metric=metric, value=value, unit=unit)
        self.observations.append(obs)
        
        # Trim history
        if len(self.observations) > self.max_history:
            self.observations = self.observations[-self.max_history:]
        
        return obs
    
    def evaluate(self, observation: Observation) -> Optional[Decision]:
        """Evaluate rules against an observation."""
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            if rule.metric != observation.metric:
                continue
            
            # Check cooldown
            if rule.last_triggered:
                elapsed = (datetime.now() - rule.last_triggered).total_seconds()
                if elapsed < rule.cooldown_seconds:
                    continue
            
            # Check condition
            try:
                if rule.condition(observation.value):
                    # Rule triggered!
                    decision = Decision(
                        rule_id=rule.id,
                        observation=observation,
                        action_type=rule.action_type,
                        severity=rule.severity,
                        message=rule.message_template.format(value=observation.value),
                        command=rule.command
                    )
                    
                    rule.last_triggered = datetime.now()
                    self.decisions.append(decision)
                    
                    return decision
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_id}: {e}")
        
        return None
    
    async def execute_decision(self, decision: Decision) -> str:
        """Execute a decision's action."""
        result = ""
        
        if decision.action_type == ActionType.LOG:
            logger.info(f"📝 {decision.message}")
            result = "Logged"
            
        elif decision.action_type == ActionType.ALERT:
            logger.warning(f"🔔 ALERT: {decision.message}")
            # Here you could add: send to Discord, Telegram, email, etc.
            result = "Alert sent"
            
        elif decision.action_type == ActionType.SUGGEST:
            logger.info(f"💡 SUGGESTION: {decision.message}")
            result = "Suggestion logged"
            
        elif decision.action_type == ActionType.EXECUTE:
            if decision.command:
                result = await self._safe_execute(decision.command)
            else:
                result = "No command specified"
                
        elif decision.action_type == ActionType.SELF_HEAL:
            if decision.command:
                logger.warning(f"🔧 SELF-HEAL: Attempting {decision.command}")
                result = await self._safe_execute(decision.command)
            else:
                result = "No heal command specified"
                
        elif decision.action_type == ActionType.ESCALATE:
            logger.critical(f"🚨 ESCALATE: {decision.message}")
            result = "Escalated to human"
        
        decision.executed = True
        decision.result = result
        
        return result
    
    async def _safe_execute(self, command: str) -> str:
        """Safely execute a command with timeout and safety checks."""
        # Safety checks
        dangerous_patterns = ["rm -rf /", "mkfs", "dd if=", ":(){", "chmod 777 /"]
        for pattern in dangerous_patterns:
            if pattern in command:
                return f"❌ Blocked dangerous command: {pattern}"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip() or result.stderr.strip() or "Executed successfully"
        except subprocess.TimeoutExpired:
            return "Command timeout"
        except Exception as e:
            return f"Execution error: {e}"
    
    def get_recent_decisions(self, n: int = 10) -> List[Decision]:
        """Get recent decisions."""
        return self.decisions[-n:]
    
    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return {
            "rules_count": len(self.rules),
            "rules_enabled": sum(1 for r in self.rules.values() if r.enabled),
            "observations_count": len(self.observations),
            "decisions_count": len(self.decisions),
            "recent_decisions": [
                {
                    "rule": d.rule_id,
                    "severity": d.severity.value,
                    "message": d.message[:50],
                    "executed": d.executed
                }
                for d in self.decisions[-5:]
            ]
        }


# ========== Singleton ==========

_engine: Optional[DecisionEngine] = None

def get_decision_engine() -> DecisionEngine:
    """Get or create global decision engine."""
    global _engine
    if _engine is None:
        _engine = DecisionEngine()
    return _engine


if __name__ == "__main__":
    # Test the engine
    logging.basicConfig(level=logging.INFO)
    
    engine = DecisionEngine()
    
    # Simulate observations
    obs1 = engine.observe("memory_percent", 92)
    decision1 = engine.evaluate(obs1)
    if decision1:
        print(f"Decision: {decision1.message}")
    
    obs2 = engine.observe("disk_percent", 88)
    decision2 = engine.evaluate(obs2)
    if decision2:
        print(f"Decision: {decision2.message}")
    
    print(f"\nStats: {engine.get_stats()}")
