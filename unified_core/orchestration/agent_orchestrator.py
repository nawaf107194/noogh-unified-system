"""
Agent Orchestrator — Wires agents to the CoreLoop via MessageBus

v1.0: Schedules periodic tasks, auto-wires new agents, provides Brain gateway
      and inter-agent communication.

Architecture:
  CoreLoop → AgentOrchestrator.tick(cycle)
           → Checks schedule → Dispatches tasks via MessageBus
           → Agents handle tasks → Results logged

  Brain Gateway:  topic "brain:query"  → any agent can ask the Brain
  Inter-Agent:    request_agent(role, capability, args) → MessageBus.request_reply
"""

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .messages import MessageEnvelope, MessageType, RiskLevel
from .message_bus import get_message_bus

logger = logging.getLogger("unified_core.orchestration.agent_orchestrator")


# ── Schedule Config ─────────────────────────────────────
# role → (interval_cycles, capabilities_to_run, task_args_builder)
DEFAULT_SCHEDULES = {
    "health_monitor": {
        "interval": 50,       # ~100s at 2s cycle
        "capability": "MONITOR_HEALTH",
        "args": {},
    },
    "log_analyzer": {
        "interval": 100,      # ~200s
        "capability": "ANALYZE_LOGS",
        "args": {"log_path": "/var/log/syslog", "lines": 200},
    },
    "test_runner": {
        "interval": 100,
        "capability": "RUN_TESTS",
        "args": {"test_dir": ""},  # filled dynamically
    },
    "performance_profiler": {
        "interval": 150,
        "capability": "PROFILE_CODE",
        "args": {},
    },
    "backup_agent": {
        "interval": 200,      # ~400s (~7 min)
        "capability": "CREATE_BACKUP",
        "args": {},  # filled dynamically
    },
    "dependency_auditor": {
        "interval": 300,      # ~600s (~10 min)
        "capability": "AUDIT_DEPS",
        "args": {},
    },
}

SRC_ROOT = Path(__file__).parent.parent.parent  # .../src


class AgentOrchestrator:
    """
    Wires idle agents to the system by scheduling periodic tasks
    and providing Brain/inter-agent communication.
    """

    def __init__(self):
        self.bus = get_message_bus()
        self._schedules: Dict[str, Dict] = {}
        self._last_run: Dict[str, int] = {}
        self._brain_client = None
        self._results_log: List[Dict] = []

        # Load schedules from defaults
        for role, config in DEFAULT_SCHEDULES.items():
            self.register_schedule(role, config)

        # Auto-wire: read registry and add any unknown roles
        self._auto_wire_from_registry()

        # Setup Brain Gateway listener
        self._setup_brain_gateway()

        logger.info(
            f"🔌 AgentOrchestrator initialized: "
            f"{len(self._schedules)} agents scheduled"
        )

    def register_schedule(self, role: str, config: Dict):
        """Register a periodic schedule for an agent role."""
        self._schedules[role] = config
        self._last_run[role] = 0

    def _auto_wire_from_registry(self):
        """Read agent_registry.json and schedule any agents not in defaults."""
        registry_path = SRC_ROOT / "agents" / "agent_registry.json"
        if not registry_path.exists():
            return

        try:
            with open(registry_path) as f:
                registry = json.load(f)
        except Exception:
            return

        for entry in registry:
            role = entry.get("role", "")
            if role and role not in self._schedules:
                caps = entry.get("capabilities", [])
                if caps:
                    self.register_schedule(role, {
                        "interval": 200,  # default: every 200 cycles
                        "capability": caps[0],
                        "args": {},
                    })
                    logger.info(f"🔌 Auto-wired new agent: {role} → {caps[0]}")

    def _setup_brain_gateway(self):
        """Subscribe to brain:query topic so agents can ask the Brain."""
        async def _handle_brain_query(message: MessageEnvelope):
            try:
                question = message.payload.get("question", "")
                if not question:
                    return

                client = await self._get_brain_client()
                if not client:
                    return

                result = await client.complete(
                    messages=[
                        {"role": "system", "content": "You are NOOGH, an autonomous AI system. Answer concisely."},
                        {"role": "user", "content": question}
                    ],
                    max_tokens=500
                )

                response_text = ""
                if result and result.get("success"):
                    response_text = result.get("content", "")

                # Send reply
                reply = message.create_reply(
                    type=MessageType.RESULT,
                    payload={"answer": response_text, "success": bool(response_text)}
                )
                await self.bus.publish(reply)
                logger.info(f"🧠 Brain answered query from {message.sender} ({len(response_text)} chars)")

            except Exception as e:
                logger.error(f"Brain gateway error: {e}")

        self.bus.subscribe("brain:query", _handle_brain_query)
        logger.info("🧠 Brain Gateway active on topic: brain:query")

        # Subscribe to own topic to prevent DLQ warnings for task replies
        async def _handle_orchestrator_messages(message: MessageEnvelope):
            pass # Currently handled as request_reply, this just keeps the topic alive
            
        self.bus.subscribe("agent:orchestrator", _handle_orchestrator_messages)
    async def _get_brain_client(self):
        """Lazy-init Brain client."""
        if self._brain_client is None:
            try:
                from unified_core.neural_bridge import NeuralEngineClient
                teacher_url = os.getenv("NOOGH_TEACHER_URL", os.getenv("NEURAL_ENGINE_URL"))
                teacher_mode = os.getenv("NOOGH_TEACHER_MODE", os.getenv("NEURAL_ENGINE_MODE", "local"))
                self._brain_client = NeuralEngineClient(base_url=teacher_url, mode=teacher_mode)
            except Exception:
                pass
        return self._brain_client

    # ── Public API for inter-agent requests ──────────────

    async def request_agent(
        self, role: str, capability: str,
        arguments: Dict[str, Any] = None,
        timeout_ms: int = 10000
    ) -> Optional[Dict]:
        """
        Send a task to an agent and wait for reply.

        Usage (from any component):
            orchestrator = components.get("agent_orchestrator")
            result = await orchestrator.request_agent(
                "test_runner", "RUN_TESTS", {"test_dir": "/src/tests"}
            )
        """
        trace_id = str(uuid.uuid4())[:8]
        task_id = f"req_{role}_{int(time.time())}"

        message = MessageEnvelope(
            trace_id=trace_id,
            task_id=task_id,
            sender="agent:orchestrator",
            receiver=f"agent:{role}",
            type=MessageType.REQUEST,
            risk_level=RiskLevel.RESTRICTED,
            payload={
                "task": {
                    "task_id": task_id,
                    "title": f"Request {capability}",
                    "agent_role": role,
                    "capabilities": [capability],
                    "arguments": arguments or {},
                    "risk_level": "RESTRICTED",
                    "isolation": "none",
                }
            }
        )

        reply = await self.bus.request_reply(message, timeout_ms=timeout_ms)
        if reply:
            return reply.payload
        return None

    # ── Core tick — called from CoreLoop ─────────────────

    async def tick(self, cycle: int):
        """
        Called every CoreLoop cycle. Checks schedules and dispatches tasks.
        """
        for role, config in self._schedules.items():
            interval = config.get("interval", 100)

            # Check if it's time to run
            if cycle - self._last_run.get(role, 0) < interval:
                continue

            # Don't run on cycle 0 (startup)
            if cycle == 0:
                self._last_run[role] = 0
                continue

            self._last_run[role] = cycle

            # Build task arguments
            args = dict(config.get("args", {}))
            capability = config.get("capability", "")

            # Dynamic args for specific agents
            if role == "backup_agent":
                args["source_dir"] = str(SRC_ROOT)
                args["dest_dir"] = str(Path.home() / ".noogh" / "backups" / f"auto_{int(time.time())}")
            elif role == "test_runner":
                args["test_dir"] = str(SRC_ROOT)

            # Dispatch via MessageBus (fire-and-forget)
            asyncio.create_task(
                self._dispatch_task(role, capability, args, cycle)
            )

    async def _dispatch_task(
        self, role: str, capability: str,
        arguments: Dict, cycle: int
    ):
        """Send a task to an agent via MessageBus."""
        trace_id = f"sched_{cycle}_{role}"
        task_id = f"auto_{role}_{int(time.time())}"

        message = MessageEnvelope(
            trace_id=trace_id,
            task_id=task_id,
            sender="agent:orchestrator",
            receiver=f"agent:{role}",
            type=MessageType.REQUEST,
            risk_level=RiskLevel.RESTRICTED,
            payload={
                "task": {
                    "task_id": task_id,
                    "title": f"Scheduled {capability}",
                    "agent_role": role,
                    "capabilities": [capability],
                    "arguments": arguments,
                    "risk_level": "RESTRICTED",
                    "isolation": "none",
                }
            },
            ttl_ms=60000,  # 60s TTL
        )

        try:
            delivered = await self.bus.publish(message)

            if delivered:
                logger.info(f"📋 Dispatched {capability} → {role} (cycle {cycle})")
            else:
                logger.warning(f"📋 No subscriber for {role} — task dropped")

            self._results_log.append({
                "cycle": cycle,
                "role": role,
                "capability": capability,
                "delivered": delivered,
                "timestamp": time.time(),
            })
            # Keep last 100 results
            if len(self._results_log) > 100:
                self._results_log = self._results_log[-100:]

        except Exception as e:
            logger.error(f"📋 Dispatch to {role} failed: {e}")

    # ── Stats ────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "scheduled_agents": list(self._schedules.keys()),
            "total_dispatches": len(self._results_log),
            "recent_results": self._results_log[-5:],
            "bus_stats": self.bus.get_stats(),
        }


# ── Singleton ────────────────────────────────────────────

_orchestrator_instance: Optional[AgentOrchestrator] = None


def get_agent_orchestrator() -> AgentOrchestrator:
    """Get or create global AgentOrchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator()
    return _orchestrator_instance
