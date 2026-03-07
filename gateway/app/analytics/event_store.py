# gateway/app/analytics/event_store.py
from __future__ import annotations

import time
import json
import csv
import io
import threading
from collections import deque
from typing import Any, Dict, List, Optional, Tuple


class EventStore:
    """
    Thread-safe in-memory event store for analytics/dashboard.
    - bounded memory
    - dedup
    - query by time window
    - export CSV/JSON
    """

    def __init__(self, max_events: int = 5000):
        self._lock = threading.Lock()
        self._events = deque(maxlen=max_events)  # newest appended to right
        self._seen_ids = set()
        self._seen_max = 8000

    def add_event(self, event: Dict[str, Any]) -> bool:
        eid = str(event.get("id") or "")
        if not eid:
            # fabricate id if missing
            eid = f"evt_{time.time_ns()}"
            event["id"] = eid

        with self._lock:
            if eid in self._seen_ids:
                return False

            self._events.append(event)
            self._seen_ids.add(eid)

            # prevent leak
            if len(self._seen_ids) > self._seen_max:
                # rebuild from current deque ids
                self._seen_ids = {str(e.get("id")) for e in self._events if e.get("id")}

        return True

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_events": len(self._events),
                "max_events": self._events.maxlen,
                "seen_ids": len(self._seen_ids),
            }

    def query(
        self,
        window_seconds: int = 3600,
        event_type: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        now = time.time()
        start_ts = now - float(window_seconds)

        with self._lock:
            # iterate from newest to oldest
            out: List[Dict[str, Any]] = []
            for e in reversed(self._events):
                ts = e.get("timestamp")
                # accept iso or epoch
                if isinstance(ts, str):
                    # if ISO string exists, keep event, but cannot filter reliably by epoch
                    # fallback: include
                    ts_epoch = None
                else:
                    ts_epoch = float(ts) if ts is not None else None

                if ts_epoch is not None and ts_epoch < start_ts:
                    break

                if event_type and e.get("type") != event_type:
                    continue

                out.append(e)
                if len(out) >= limit:
                    break

            return out

    def export_json(self, window_seconds: int = 3600) -> str:
        events = self.query(window_seconds=window_seconds, limit=100000)
        return json.dumps({"window_seconds": window_seconds, "count": len(events), "events": events}, ensure_ascii=False, indent=2)

    def export_csv(self, window_seconds: int = 3600) -> str:
        events = self.query(window_seconds=window_seconds, limit=100000)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "type", "timestamp", "payload"])

        for e in events:
            writer.writerow([
                e.get("id", ""),
                e.get("type", ""),
                e.get("timestamp", ""),
                json.dumps(e.get("payload", {}), ensure_ascii=False),
            ])

        return buf.getvalue()

    def bucketize_counts(
        self,
        window_seconds: int = 3600,
        buckets: int = 12
    ) -> Dict[str, Any]:
        """
        Returns buckets with event counts per time slice.
        """
        now = time.time()
        start = now - float(window_seconds)
        buckets = max(1, int(buckets))
        step = float(window_seconds) / float(buckets)

        counts = [0] * buckets
        bucket_ts = [start + i * step for i in range(buckets)]

        with self._lock:
            for e in self._events:
                ts = e.get("timestamp")
                if not isinstance(ts, (int, float)):
                    continue
                tsf = float(ts)
                if tsf < start or tsf > now:
                    continue
                idx = int((tsf - start) / step)
                if idx >= buckets:
                    idx = buckets - 1
                if idx < 0:
                    idx = 0
                counts[idx] += 1

        return {
            "window_seconds": window_seconds,
            "buckets": [
                {"timestamp": bucket_ts[i], "events_count": counts[i]}
                for i in range(buckets)
            ],
        }


_store: Optional[EventStore] = None


def get_event_store() -> EventStore:
    global _store
    if _store is None:
        _store = EventStore(max_events=5000)
    return _store
