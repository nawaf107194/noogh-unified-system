"""
Initiative Loop - Autonomous system monitoring and action
The heart of self-governance
"""

import logging
import time
import threading
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class InitiativeLoop:
    """
    Autonomous initiative loop for SYSTEM_ADMIN monitoring
    Implements: OBSERVE → ASSESS → PROPOSE → DECIDE → EXECUTE
    """
    
    def __init__(self, interval: int = 60):
        """
        Initialize initiative loop
        
        Args:
            interval: Seconds between observations (default: 60)
        """
        from neural_engine.specialized_systems.system_admin_adapter import get_system_admin_adapter
        from neural_engine.autonomic_system.policy_engine import get_policy_engine
        from neural_engine.autonomic_system.action_executor import get_action_executor
        from neural_engine.autonomic_system.event_stream import get_event_stream
        
        self.adapter = get_system_admin_adapter()
        self.policy = get_policy_engine()
        self.executor = get_action_executor()
        self.stream = get_event_stream()
        
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        self.stats = {
            "observations": 0,
            "assessments": 0,
            "proposals": 0,
            "executions": 0,
            "blocked": 0
        }
        
        logger.info(f"✅ InitiativeLoop initialized (interval={interval}s)")
    
    def start(self):
        """Start the initiative loop in background thread"""
        if self.running:
            logger.warning("⚠️  InitiativeLoop already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info("🚀 InitiativeLoop started")
    
    def stop(self):
        """Stop the initiative loop"""
        if not self.running:
            logger.warning("⚠️  InitiativeLoop not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🛑 InitiativeLoop stopped")
    
    def _loop(self):
        """Main loop iteration"""
        logger.info("🔄 Initiative loop active")
        
        while self.running:
            try:
                self._iteration()
            except Exception as e:
                logger.error(f"❌ Loop iteration failed: {e}")
            
            # Sleep for interval
            time.sleep(self.interval)
    
    def _iteration(self):
        """Single loop iteration"""
        iteration_start = datetime.now()
        
        # STEP 1: OBSERVE
        observation = self.adapter.observe()
        self.stats["observations"] += 1
        
        # Emit observation event
        self.stream.emit("observation", {
            "health_status": observation.get('health', {}).get('status', 'unknown'),
            "cpu_percent": observation.get('cpu', {}).get('cpu_usage_percent', 0),
            "memory_percent": observation.get('memory', {}).get('percent', 0)
        })
        
        logger.debug(f"📊 Observed: health={observation.get('health', {}).get('status', 'unknown')}")
        
        # STEP 2: ASSESS
        assessment = self.adapter.assess(observation)
        self.stats["assessments"] += 1
        
        priority = assessment.get("priority", "normal")
        num_risks = len(assessment.get("risks", []))
        num_warnings = len(assessment.get("warnings", []))
        
        # Emit assessment event
        self.stream.emit("assessment", {
            "priority": priority,
            "risks": num_risks,
            "warnings": num_warnings,
            "risk_details": [r.get("message", "") for r in assessment.get("risks", [])[:3]]
        })
        
        logger.info(f"🔍 Assessment: priority={priority}, risks={num_risks}, warnings={num_warnings}")
        
        # STEP 3: PROPOSE (only if priority warrants action)
        if priority in ["critical", "high", "medium"]:
            proposals = self.adapter.propose_actions(assessment)
            self.stats["proposals"] += len(proposals)
            
            # Emit proposal event
            self.stream.emit("proposal", {
                "count": len(proposals),
                "actions": [p.get("action") for p in proposals[:5]],
                "priority": priority
            })
            
            logger.info(f"💡 Proposed {len(proposals)} actions")
            
            # STEP 4: DECIDE + EXECUTE
            for proposal in proposals:
                action = proposal.get("action", "")
                auto_execute = proposal.get("auto_execute", False)
                
                # Policy check
                decision_approved = self.policy.should_execute(proposal)
                
                # Emit decision event
                self.stream.emit("decision", {
                    "action": action,
                    "approved": decision_approved,
                    "confidence": proposal.get("confidence", 0),
                    "auto_execute": auto_execute
                })
                
                if decision_approved:
                    # Execute approved action
                    result = self.executor.execute_action(proposal)
                    
                    # Emit execution event
                    self.stream.emit("execution", {
                        "action": action,
                        "success": result.get("success", False),
                        "message": result.get("message", "")[:100]
                    })
                    
                    if result.get("success"):
                        self.stats["executions"] += 1
                        logger.info(f"✅ Executed: {action}")
                    else:
                        logger.error(f"❌ Failed: {action} - {result.get('message')}")
                else:
                    # Blocked by policy
                    self.stats["blocked"] += 1
                    logger.info(f"🔒 Blocked: {action} (requires approval)")
        else:
            logger.debug(f"✨ System healthy (priority={priority})")
        
        # Log iteration completion
        duration = (datetime.now() - iteration_start).total_seconds()
        logger.debug(f"⏱️  Iteration complete ({duration:.2f}s)")
    
    def get_status(self) -> dict:
        """Get loop status"""
        return {
            "running": self.running,
            "interval": self.interval,
            "stats": self.stats.copy(),
            "adapter": self.adapter.get_status(),
            "executor_stats": self.executor.get_stats(),
            "policy": self.policy.get_policy_summary()
        }


# Singleton instance
_loop_instance: Optional[InitiativeLoop] = None


def get_initiative_loop(interval: int = 60) -> InitiativeLoop:
    """Get singleton initiative loop"""
    global _loop_instance
    if _loop_instance is None:
        _loop_instance = InitiativeLoop(interval=interval)
    return _loop_instance


def start_initiative_loop(interval: int = 60):
    """Start the initiative loop"""
    loop = get_initiative_loop(interval=interval)
    loop.start()
    return loop


def stop_initiative_loop():
    """Stop the initiative loop"""
    global _loop_instance
    if _loop_instance:
        _loop_instance.stop()
