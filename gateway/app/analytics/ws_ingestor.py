# gateway/app/analytics/ws_ingestor.py
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, Optional, Set

import httpx

from gateway.app.analytics.kpi_calculator import get_kpi_calculator
from gateway.app.analytics.event_store import get_event_store
from gateway.app.analytics.alert_manager import get_alert_manager
from config.ports import PORTS

logger = logging.getLogger(__name__)


class AnalyticsIngestor:
    def __init__(self, poll_interval: float = 2.0):
        self.poll_interval = poll_interval
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._seen: Set[str] = set()
        self._seen_max = 2000

        # Autonomic events live on the LOCAL Neural Engine, not the remote vLLM teacher
        # NEURAL_ENGINE_URL may point to RunPod (vLLM) which doesn't serve events
        local_neural = os.getenv("NEURAL_SERVICE_URL", f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}")
        self.neural_events_url = local_neural + "/api/v1/autonomic/events"

    def configure(self, neural_base: str):
        # This method now overrides the initial setup if called.
        # It assumes neural_base will be a full URL including scheme and host/port.
        self.neural_events_url = f"{neural_base.rstrip('/')}/api/v1/autonomic/events"

    async def start(self):
        if self.running:
            return
        self.running = True
        logger.info(f"✅ AnalyticsIngestor starting (poll={self.poll_interval}s) url={self.neural_events_url}")
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    async def _poll_loop(self):
        kpi = get_kpi_calculator()
        store = get_event_store()
        alerts = get_alert_manager()

        last_kpi_eval = 0.0

        async with httpx.AsyncClient(timeout=10.0) as client:
            while self.running:
                try:
                    resp = await client.get(self.neural_events_url, params={"limit": 200})
                    if resp.status_code < 200 or resp.status_code >= 300:
                        logger.warning(f"⚠️ Ingestor bad status: {resp.status_code}")
                        await asyncio.sleep(self.poll_interval)
                        continue

                    data = resp.json()
                    events = data.get("events") or []
                    added = 0

                    for e in events:
                        eid = str(e.get("id") or "")
                        if not eid:
                            # derive stable-ish id
                            eid = f"evt_{e.get('type','x')}_{e.get('timestamp','')}_{hash(json.dumps(e.get('payload',{}), sort_keys=True))}"
                            e["id"] = eid

                        if eid in self._seen:
                            continue

                        # ensure timestamp numeric for bucketing
                        ts = e.get("timestamp")
                        if isinstance(ts, str):
                            # cannot parse ISO reliably here; keep original
                            pass
                        elif ts is None:
                            e["timestamp"] = time.time()

                        kpi.add_event(e)
                        store.add_event(e)
                        self._seen.add(eid)
                        added += 1

                    # seen bound
                    if len(self._seen) > self._seen_max:
                        self._seen = set(list(self._seen)[-self._seen_max:])

                    # evaluate alerts every 5 seconds (cheap)
                    now = time.time()
                    if now - last_kpi_eval >= 5.0:
                        try:
                            snap = kpi.calculate_all(window_seconds=300)  # fast window for alerting
                            kpis = snap.get("kpis", snap)  # depending on your calculator output
                            alerts.evaluate(kpis)
                        except Exception as ee:
                            logger.exception(f"Alert evaluation error: {ee}")
                        last_kpi_eval = now

                    if added:
                        logger.info(f"📥 Ingested events: +{added} (seen={len(self._seen)})")
                except Exception as e:
                    logger.warning(f"⚠️ Ingestor poll error: {e}")

                await asyncio.sleep(self.poll_interval)


_ing: Optional[AnalyticsIngestor] = None


def get_ingestor() -> AnalyticsIngestor:
    global _ing
    if _ing is None:
        _ing = AnalyticsIngestor(poll_interval=2.0)
    return _ing
