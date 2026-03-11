#!/usr/bin/env python3
"""
LearningBridge — جسر الربط بين LearningEngine و AutonomousTradingAgent

يقوم بـ:
  1. استخلاص المعرفة المكتسبة (أعلى utility) وحقنها كـ insights في ذاكرة NOOGH
  2. تحديث استراتيجيات التداول بناءً على ما تعلمه النظام
  3. تغذية برومبت Brain بالسياق التعليمي لتحسين القرار
  4. مزامنة دورات التعلم مع دورات التداول (بشكل غير متزامن)
"""
from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from .learning_engine import LearningEngine, LearningDomain, KnowledgeItem

if TYPE_CHECKING:
    from agents.autonomous_trading_agent import AutonomousTradingAgent

logger = logging.getLogger("LearningBridge")


class LearningBridge:
    """
    يُربط بين محرك التعلم ووكيل التداول.

    الاستخدام:
        bridge = LearningBridge(trading_agent)
        await bridge.start()          # تشغيل مستقل في background
        context = bridge.get_context_for_trade(symbol)
    """

    SYNC_INTERVAL = 900   # inject كل 15 دقيقة
    LEARN_INTERVAL = 1800 # learn  كل 30 دقيقة

    def __init__(
        self,
        trading_agent: Optional["AutonomousTradingAgent"] = None,
        db_path: Optional[Path] = None,
    ):
        self.trading_agent = trading_agent
        root = Path(__file__).resolve().parent.parent.parent
        self.db_path = db_path or (root / "data" / "shared_memory.sqlite")

        self.engine = LearningEngine(db_path=self.db_path)
        self._running = False
        self._last_sync = 0.0
        self._context_cache: Dict[str, str] = {}  # symbol → learning context string
        logger.info("🌉 LearningBridge جاهز")

    # ------------------------------------------------------------------
    # Background tasks
    # ------------------------------------------------------------------

    async def start(self):
        """تشغيل التعلم + sync في background tasks"""
        self._running = True
        await asyncio.gather(
            self._learning_loop(),
            self._sync_loop(),
        )

    def stop(self):
        self._running = False
        self.engine.stop()

    async def _learning_loop(self):
        """LearningEngine كل 30 دقيقة"""
        try:
            while self._running:
                await self.engine.run_cycle()
                await asyncio.sleep(self.LEARN_INTERVAL)
        except asyncio.CancelledError:
            pass

    async def _sync_loop(self):
        """حقن المعرفة في ذاكرة التداول كل 15 دقيقة"""
        try:
            while self._running:
                await asyncio.sleep(self.SYNC_INTERVAL)
                self._inject_into_trading_agent()
        except asyncio.CancelledError:
            pass

    # ------------------------------------------------------------------
    # Injection: Learning → Trading Agent
    # ------------------------------------------------------------------

    def _inject_into_trading_agent(self):
        """
        يحقن أعلى 10 معارف متعلقة بالتداول كـ insights في SQLite beliefs
        حتى يراها Brain عند التحليل.
        """
        top = self.engine.get_knowledge(domain=LearningDomain.TRADING, limit=10)
        top += self.engine.get_knowledge(domain=LearningDomain.AI, limit=5)
        top += self.engine.get_knowledge(domain=LearningDomain.HEURISTIC, limit=5)

        if not top:
            return

        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                for item in top:
                    key = f"bridge_inject:{item.get('key', '')}"
                    val = json.dumps({
                        "title": item.get("title", ""),
                        "content": item.get("content", "")[:300],
                        "source": item.get("source", ""),
                    }, ensure_ascii=False)
                    conn.execute(
                        "INSERT OR REPLACE INTO beliefs (key, value, utility_score, domain, updated_at) VALUES (?,?,?,?,?)",
                        (key, val, float(item.get("utility", 0.75)), "trading", time.time()),
                    )
            logger.info("💉 Bridge: حقن %d عنصر في beliefs", len(top))
        except Exception as e:
            logger.error("Bridge inject error: %s", e)

    # ------------------------------------------------------------------
    # Context builder: يعطي Brain سياق تعليمي عند كل صفقة
    # ------------------------------------------------------------------

    def get_context_for_trade(self, symbol: str = "") -> str:
        """
        يبني text context من أعلى utility items ليُدرج في prompt Brain.

        مثال الاستخدام:
            context = bridge.get_context_for_trade("BTCUSDT")
            # ثم تضيفه للـ prompt
        """
        cache_key = symbol or "__global__"
        # refresh cache كل 5 دقائق
        if cache_key in self._context_cache and time.time() - self._last_sync < 300:
            return self._context_cache[cache_key]

        items = self.engine.get_knowledge(domain=LearningDomain.TRADING, limit=5)
        items += self.engine.get_knowledge(domain=LearningDomain.HEURISTIC, limit=3)

        lines = []
        for it in items:
            title = it.get("title", "")[:60]
            content = it.get("content", "")[:120]
            lines.append(f"  • [{it.get('utility',0):.2f}] {title}: {content}")

        context = "\n".join(lines) if lines else ""
        self._context_cache[cache_key] = context
        self._last_sync = time.time()
        return context

    # ------------------------------------------------------------------
    # Feedback: Trading → Learning
    # ------------------------------------------------------------------

    def record_trade_outcome(self, symbol: str, signal: str, win: bool, pnl: float, reasons: list):
        """
        بعد كل صفقة — أخبر LearningEngine بالنتيجة
        حتى يحدّث Curriculum تلقائياً.
        """
        outcome = "WIN" if win else "LOSS"
        item = KnowledgeItem(
            source="trade_feedback",
            domain=LearningDomain.HEURISTIC,
            title=f"{symbol} {signal} {outcome} | PnL {pnl:+.2f}",
            content=f"Reasons: {', '.join(reasons[:3])} | PnL: {pnl:+.2f}",
            utility=0.90 if win else 0.70,
        )
        self.engine.store.upsert(item)
        # تحديث Curriculum
        win_rate = 0.6 if win else 0.4
        self.engine.curriculum.update_performance(win_rate, abs(pnl) / 1000)
        logger.info("💬 Bridge feedback: %s %s %s PnL=%.2f", symbol, signal, outcome, pnl)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> Dict:
        priorities = self.engine.curriculum_priorities()
        top = self.engine.get_knowledge(limit=5)
        return {
            "running": self._running,
            "total_cycles": self.engine._cycle_count,
            "curriculum": {d.value: round(w, 3) for d, w in priorities},
            "top_items": [
                {"title": i.get("title", "")[:50], "utility": i.get("utility", 0)}
                for i in top
            ],
        }
