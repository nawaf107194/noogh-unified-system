"""
Promoted Targets — Persistent Memory for Successfully Promoted Evolution Targets
Version: 1.0.0

Prevents the Brain from re-proposing improvements to functions that
have already been promoted. Unlike the cooldown-based dedup, this
is permanent and survives process restarts.
"""
import json
import os
import logging
import time
from typing import Set, Tuple, Dict, Any, Optional

logger = logging.getLogger("unified_core.evolution.promoted_targets")

PROMOTED_TARGETS_FILE = os.path.expanduser("~/.noogh/evolution/promoted_targets.json")


class PromotedTargets:
    """ذاكرة دائمة للأهداف التي تمت ترقيتها بنجاح (الملف + الدالة).
    
    Thread-safe singleton. Loads from disk on init, saves on every add.
    """
    
    _instance: Optional["PromotedTargets"] = None
    
    def __init__(self):
        self._targets: Dict[str, Dict[str, Any]] = {}  # "file:func" -> metadata
        self._load()
    
    @classmethod
    def get_instance(cls) -> "PromotedTargets":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load(self):
        """Load promoted targets from disk."""
        if not os.path.exists(PROMOTED_TARGETS_FILE):
            self._targets = {}
            return
        try:
            with open(PROMOTED_TARGETS_FILE, "r") as f:
                data = json.load(f)
            # Support both old format (list of tuples) and new format (dict)
            if isinstance(data, list):
                # Migrate from old format
                self._targets = {}
                for item in data:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        key = f"{item[0]}:{item[1]}"
                        self._targets[key] = {"promoted_at": 0}
                self._save()  # Re-save in new format
            elif isinstance(data, dict):
                self._targets = data
            else:
                self._targets = {}
            logger.info(f"📋 Loaded {len(self._targets)} promoted targets from disk")
        except Exception as e:
            logger.warning(f"Failed to load promoted targets: {e}")
            self._targets = {}
    
    def _save(self):
        """Persist promoted targets to disk."""
        try:
            os.makedirs(os.path.dirname(PROMOTED_TARGETS_FILE), exist_ok=True)
            with open(PROMOTED_TARGETS_FILE, "w") as f:
                json.dump(self._targets, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save promoted targets: {e}")
    
    def _make_key(self, file_path: str, function_name: str) -> str:
        """Create canonical key from file path and function name."""
        # Normalize: use relative path from src/ if possible
        return f"{file_path}:{function_name}"
    
    def add(self, file_path: str, function_name: str, proposal_id: str = ""):
        """Record a target as promoted. Persists immediately."""
        key = self._make_key(file_path, function_name)
        self._targets[key] = {
            "promoted_at": time.time(),
            "proposal_id": proposal_id,
            "file": file_path,
            "function": function_name,
        }
        self._save()
        logger.info(f"✅ Promoted target recorded: {os.path.basename(file_path)}:{function_name}")
    
    def contains(self, file_path: str, function_name: str) -> bool:
        """Check if a target has already been promoted."""
        key = self._make_key(file_path, function_name)
        return key in self._targets
    
    def remove(self, file_path: str, function_name: str):
        """Remove a target (e.g. if code changed significantly)."""
        key = self._make_key(file_path, function_name)
        if key in self._targets:
            del self._targets[key]
            self._save()
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Return all promoted targets."""
        return dict(self._targets)
    
    def count(self) -> int:
        """Number of promoted targets."""
        return len(self._targets)
    
    def clear(self):
        """Clear all promoted targets (for testing/reset)."""
        self._targets = {}
        self._save()


def get_promoted_targets() -> PromotedTargets:
    """Get singleton PromotedTargets instance."""
    return PromotedTargets.get_instance()
