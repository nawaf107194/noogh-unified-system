# gateway/app/analytics/alert_manager.py
from __future__ import annotations

import time
import threading
from typing import Any, Dict, List, Optional


class AlertManager:
    """
    Simple alert rules:
    - store rules
    - evaluate against KPIs
    - keep alert history
    """

    def __init__(self, max_alerts: int = 1000):
        self._lock = threading.Lock()
        self._rules: Dict[str, Dict[str, Any]] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._max_alerts = max_alerts

        # default rules (safe)
        self.add_rule("low_success_rate", "warning", "success_rate < 90", "معدل نجاح التنفيذ أقل من 90%")
        self.add_rule("over_blocking", "warning", "approval_rate < 20", "السياسة تحظر بشكل زائد (Approval < 20%)")
        self.add_rule("over_executing", "warning", "approval_rate > 95", "تنفيذ زائد (Approval > 95%)")
        self.add_rule("confidence_drift", "warning", "avg_confidence < 0.6", "انخفاض متوسط الثقة (< 0.6)")
        self.add_rule("low_health", "critical", "health_score < 50", "صحة النظام منخفضة (Health < 50)")

    def add_rule(self, rule_id: str, level: str, expr: str, message: str) -> None:
        with self._lock:
            self._rules[rule_id] = {
                "id": rule_id,
                "level": level,
                "expr": expr,
                "message": message,
                "enabled": True,
                "created_at": time.time(),
            }

    def remove_rule(self, rule_id: str) -> bool:
        with self._lock:
            return self._rules.pop(rule_id, None) is not None

    def list_rules(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._rules.values())

    def list_alerts(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._lock:
            return self._alerts[-limit:]

    def clear_alerts(self) -> None:
        with self._lock:
            self._alerts.clear()

    def evaluate(self, kpis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate all enabled rules against kpis dict.
        expr format examples:
          "success_rate < 90"
          "approval_rate > 95"
        """
        fired: List[Dict[str, Any]] = []

        with self._lock:
            rules = list(self._rules.values())

        for r in rules:
            if not r.get("enabled"):
                continue
            expr = str(r.get("expr") or "").strip()
            ok = self._eval_expr(expr, kpis)
            if ok:
                alert = {
                    "id": f"alert_{r['id']}_{time.time_ns()}",
                    "rule_id": r["id"],
                    "level": r["level"],
                    "message": r["message"],
                    "expr": expr,
                    "ts": time.time(),
                    "snapshot": {
                        "approval_rate": kpis.get("approval_rate"),
                        "success_rate": kpis.get("success_rate"),
                        "avg_confidence": kpis.get("avg_confidence"),
                        "health_score": kpis.get("health_score"),
                        "events_per_minute": kpis.get("events_per_minute"),
                    }
                }
                fired.append(alert)

        if fired:
            with self._lock:
                self._alerts.extend(fired)
                if len(self._alerts) > self._max_alerts:
                    self._alerts = self._alerts[-self._max_alerts:]

        return fired

    def _eval_expr(self, expr: str, kpis: Dict[str, Any]) -> bool:
        # tiny safe evaluator: "<metric> <op> <number>"
        parts = expr.split()
        if len(parts) != 3:
            return False

        key, op, raw = parts
        try:
            threshold = float(raw)
        except Exception:
            return False

        val = kpis.get(key)
        if val is None:
            return False

        try:
            v = float(val)
        except Exception:
            return False

        if op == "<":
            return v < threshold
        if op == "<=":
            return v <= threshold
        if op == ">":
            return v > threshold
        if op == ">=":
            return v >= threshold
        if op == "==":
            return v == threshold
        return False


_mgr: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    global _mgr
    if _mgr is None:
        _mgr = AlertManager()
    return _mgr
