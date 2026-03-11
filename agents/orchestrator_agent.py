"""
NOOGH Orchestrator Agent
المنسق المركزي لجميع الـ agents — يشغّلها، يراقبها، ويعيد تشغيلها عند الفشل.
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import signal
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from agents.base_agent import BaseAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("OrchestratorAgent")


@dataclass
class AgentEntry:
    name: str
    module_path: str  # e.g. "agents.self_dev_agent"
    class_name: str   # e.g. "SelfDevAgent"
    enabled: bool = True
    restart_on_failure: bool = True
    max_restarts: int = 3
    _restarts: int = field(default=0, init=False, repr=False)
    _instance: Optional[BaseAgent] = field(default=None, init=False, repr=False)
    _task: Optional[asyncio.Task] = field(default=None, init=False, repr=False)


class OrchestratorAgent(BaseAgent):
    """
    يدير دورة حياة جميع الـ sub-agents:
    - تحميل ديناميكي
    - تشغيل متوازي async
    - إعادة تشغيل تلقائي عند الفشل
    - إيقاف نظيف عند SIGTERM/SIGINT
    """

    AGENTS: List[AgentEntry] = [
        AgentEntry(
            name="SelfDevAgent",
            module_path="agents.self_dev_agent",
            class_name="SelfDevAgent",
        ),
        AgentEntry(
            name="HealthMonitor",
            module_path="agents.health_monitor_agent",
            class_name="HealthMonitorAgent",
        ),
        AgentEntry(
            name="VolatilityGuard",
            module_path="agents.volatility_guard",
            class_name="VolatilityGuard",
        ),
        AgentEntry(
            name="AutonomousTrader",
            module_path="agents.autonomous_trading_agent",
            class_name="AutonomousTradingAgent",
        ),
        AgentEntry(
            name="SelfHealer",
            module_path="agents.self_healer",
            class_name="SelfHealer",
        ),
    ]

    def __init__(self) -> None:
        super().__init__(name="OrchestratorAgent")
        self._shutdown_event = asyncio.Event()
        self._registry: Dict[str, AgentEntry] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """نقطة الدخول الرئيسية."""
        self._register_signals()
        logger.info("🚀 OrchestratorAgent بدأ — %d agent(s) مُسجَّل", len(self.AGENTS))

        tasks = []
        for entry in self.AGENTS:
            if not entry.enabled:
                logger.info("⏭  %s معطَّل — تخطي", entry.name)
                continue
            self._registry[entry.name] = entry
            tasks.append(self._run_with_restart(entry))

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("✅ OrchestratorAgent انتهى بشكل نظيف")

    async def stop(self) -> None:
        self._shutdown_event.set()
        for entry in self._registry.values():
            if entry._task and not entry._task.done():
                entry._task.cancel()
                try:
                    await entry._task
                except (asyncio.CancelledError, Exception):
                    pass
        logger.info("🛑 جميع الـ agents أُوقفت")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_with_restart(self, entry: AgentEntry) -> None:
        """يشغّل الـ agent ويعيد تشغيله عند الفشل."""
        while not self._shutdown_event.is_set():
            try:
                instance = self._load_agent(entry)
                entry._instance = instance
                logger.info("▶  تشغيل %s", entry.name)
                entry._task = asyncio.current_task()
                if hasattr(instance, "start"):
                    await instance.start()
                elif hasattr(instance, "run"):
                    await asyncio.to_thread(instance.run)
                else:
                    logger.warning("⚠  %s لا يحتوي على start() أو run()", entry.name)
                    break
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self._error_count += 1
                entry._restarts += 1
                logger.error(
                    "❌ %s فشل (محاولة %d/%d): %s",
                    entry.name, entry._restarts, entry.max_restarts, exc,
                )
                if not entry.restart_on_failure or entry._restarts >= entry.max_restarts:
                    logger.critical("🚫 %s تجاوز الحد الأقصى للإعادة — إيقاف", entry.name)
                    break
                await asyncio.sleep(min(5 * entry._restarts, 30))

    def _load_agent(self, entry: AgentEntry) -> BaseAgent:
        """يحمّل الـ class ديناميكياً ويُنشئ instance جديد."""
        module = importlib.import_module(entry.module_path)
        cls = getattr(module, entry.class_name)
        return cls()

    def _register_signals(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.stop()),
            )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> Dict:
        return {
            "uptime": self.uptime(),
            "agents": {
                name: {
                    "restarts": e._restarts,
                    "running": e._task is not None and not e._task.done(),
                }
                for name, e in self._registry.items()
            },
            "total_errors": self._error_count,
        }


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main() -> None:
    orchestrator = OrchestratorAgent()
    try:
        asyncio.run(orchestrator.start())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
