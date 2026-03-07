"""
Policy Store for Autonomic System.
Manages policy configuration with validation and persistence.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from typing import Any, Dict

DEFAULT_POLICY = {
    "version": 1,
    "thresholds": {
        "min_confidence": 0.85,
        "max_auto_execute_per_min": 120,
        "min_success_rate": 0.90,
        "over_blocking_rate": 0.80,
        "over_executing_rate": 0.95
    },
    "allow_actions": [
        "log_info",
        "log_warning"
    ],
    "block_actions": [
        "suggest_cleanup",
        "suggest_restart"
    ],
    "action_rules": []
}

@dataclass
class PolicySnapshot:
    data: Dict[str, Any]

class PolicyStore:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._policy: Dict[str, Any] = {}
        self.load()

    def load(self) -> PolicySnapshot:
        with self._lock:
            if not os.path.exists(self.path):
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                self._policy = DEFAULT_POLICY
                self._write_nolock(self._policy)
                return PolicySnapshot(self._policy)

            with open(self.path, "r", encoding="utf-8") as f:
                self._policy = json.load(f)
            self._policy = self._merge_defaults(self._policy)
            return PolicySnapshot(self._policy)

    def get(self) -> PolicySnapshot:
        with self._lock:
            return PolicySnapshot(json.loads(json.dumps(self._policy)))

    def update(self, new_policy: Dict[str, Any]) -> PolicySnapshot:
        self._validate(new_policy)
        with self._lock:
            self._policy = self._merge_defaults(new_policy)
            self._write_nolock(self._policy)
            return PolicySnapshot(self._policy)

    def patch(self, patch: Dict[str, Any]) -> PolicySnapshot:
        with self._lock:
            merged = self._deep_merge(dict(self._policy), patch)
        return self.update(merged)

    def _write_nolock(self, data: Dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _merge_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._deep_merge(dict(DEFAULT_POLICY), data)

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k] = self._deep_merge(base[k], v)
            else:
                base[k] = v
        return base

    def _validate(self, p: Dict[str, Any]) -> None:
        if "thresholds" in p:
            t = p["thresholds"]
            if "min_confidence" in t:
                mc = float(t["min_confidence"])
                if not (0.0 <= mc <= 1.0):
                    raise ValueError("thresholds.min_confidence must be between 0 and 1")
        if "allow_actions" in p and not isinstance(p["allow_actions"], list):
            raise ValueError("allow_actions must be list")
        if "block_actions" in p and not isinstance(p["block_actions"], list):
            raise ValueError("block_actions must be list")


_policy_store = None

def get_policy_store() -> PolicyStore:
    global _policy_store
    if _policy_store is None:
        path = os.getenv("NOOGH_POLICY_FILE", "/home/noogh/projects/noogh_unified_system/runtime/policy.json")
        _policy_store = PolicyStore(path)
    return _policy_store
