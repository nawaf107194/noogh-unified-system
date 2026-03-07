"""
Cognitive Journal — Persistent Memory for Agent Daemon
Version: 1.0.0

Inspired by:
- Windsurf: Proactive memory creation (store important context immediately)
- Augment Code: Incremental tasklist (investigate → plan → execute → verify)
- Kiro: Steering files (contextual rules that persist across sessions)

This module gives the daemon persistent memory across restarts.
It records decisions, discoveries, failed experiments, and successful improvements.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("unified_core.cognitive_journal")

# Journal location
JOURNAL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "cognitive_journal"
)


@dataclass
class JournalEntry:
    """A single memory entry in the cognitive journal."""
    entry_type: str           # decision, discovery, failure, success, observation
    content: str              # What happened
    context: Dict[str, Any] = field(default_factory=dict)  # Additional data
    confidence: float = 0.5   # How confident the daemon is about this
    cycle: int = 0            # Which cycle this was recorded in
    timestamp: float = field(default_factory=time.time)
    entry_id: str = field(default_factory=lambda: f"j_{int(time.time())}_{os.getpid()}")
    tags: List[str] = field(default_factory=list)


class CognitiveJournal:
    """
    Persistent memory for daemon evolution.
    
    Patterns applied:
    - Windsurf: Record important info immediately, don't wait
    - Augment: Incremental — start with one entry, refine later
    - Kiro: Steering context — build up project knowledge over time
    
    Records: decisions, discoveries, failed experiments,
    successful improvements — all persisted to disk across restarts.
    """
    
    def __init__(self, journal_dir: str = None):
        self._dir = journal_dir or JOURNAL_DIR
        self._entries: List[JournalEntry] = []
        self._max_memory = 1000  # Keep last 1000 entries in memory
        
        # Ensure directory exists
        os.makedirs(self._dir, exist_ok=True)
        
        # Load existing entries
        self._load()
        
        logger.info(f"📓 CognitiveJournal initialized | {len(self._entries)} entries loaded from {self._dir}")
    
    def record(self, entry_type: str, content: str, 
               context: Dict[str, Any] = None, confidence: float = 0.5,
               cycle: int = 0, tags: List[str] = None) -> JournalEntry:
        """
        Record a cognitive event (Windsurf pattern: proactive, immediate).
        
        Types:
        - decision: A choice the daemon made
        - discovery: Something new learned about the system
        - failure: An experiment or action that failed
        - success: An improvement that worked
        - observation: A system state observation
        """
        entry = JournalEntry(
            entry_type=entry_type,
            content=content,
            context=context or {},
            confidence=confidence,
            cycle=cycle,
            tags=tags or []
        )
        
        self._entries.append(entry)
        
        # Auto-trim memory
        if len(self._entries) > self._max_memory:
            self._entries = self._entries[-self._max_memory:]
        
        # Persist immediately
        self._save_entry(entry)
        
        logger.debug(f"📓 Recorded [{entry_type}]: {content[:80]}")
        return entry
    
    def recall(self, topic: str = None, entry_type: str = None, 
               limit: int = 5, min_confidence: float = 0.0) -> List[JournalEntry]:
        """
        Retrieve relevant past entries (Augment pattern: targeted recall).
        
        Filters by topic (substring match), type, and confidence.
        Returns most recent matching entries.
        """
        results = self._entries
        
        if entry_type:
            results = [e for e in results if e.entry_type == entry_type]
        
        if min_confidence > 0:
            results = [e for e in results if e.confidence >= min_confidence]
        
        if topic:
            topic_lower = topic.lower()
            results = [
                e for e in results 
                if topic_lower in e.content.lower() 
                or topic_lower in str(e.context).lower()
                or any(topic_lower in t.lower() for t in e.tags)
            ]
        
        return results[-limit:]
    
    def get_evolution_context(self, max_entries: int = 10) -> str:
        """
        Build context for brain consultation (Kiro steering pattern).
        
        Returns a formatted summary of recent decisions, discoveries,
        and failures to guide the evolution cycle.
        """
        recent = self._entries[-max_entries:] if self._entries else []
        
        if not recent:
            return "لا يوجد سجل معرفي سابق. هذه أول دورة."
        
        lines = ["# السجل المعرفي الأخير"]
        for e in recent:
            type_emoji = {
                "decision": "🎯",
                "discovery": "💡", 
                "failure": "❌",
                "success": "✅",
                "observation": "👁️"
            }.get(e.entry_type, "📝")
            
            lines.append(f"- {type_emoji} [{e.entry_type}] {e.content}")
            if e.context:
                for k, v in e.context.items():
                    if isinstance(v, (str, int, float, bool)):
                        lines.append(f"  → {k}: {v}")
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get journal statistics."""
        type_counts = {}
        for e in self._entries:
            type_counts[e.entry_type] = type_counts.get(e.entry_type, 0) + 1
        
        return {
            "total_entries": len(self._entries),
            "by_type": type_counts,
            "oldest": self._entries[0].timestamp if self._entries else None,
            "newest": self._entries[-1].timestamp if self._entries else None,
            "avg_confidence": (
                sum(e.confidence for e in self._entries) / len(self._entries)
                if self._entries else 0
            )
        }
    
    def _save_entry(self, entry: JournalEntry):
        """Save a single entry to disk."""
        try:
            # Daily file rotation
            day_str = time.strftime("%Y-%m-%d", time.localtime(entry.timestamp))
            filepath = os.path.join(self._dir, f"journal_{day_str}.jsonl")
            
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"📓 Failed to save entry: {e}")
    
    def _load(self):
        """Load entries from disk."""
        try:
            if not os.path.exists(self._dir):
                return
            
            files = sorted(f for f in os.listdir(self._dir) if f.endswith(".jsonl"))
            
            # Load only recent files (last 7 days)
            for filepath in files[-7:]:
                full_path = os.path.join(self._dir, filepath)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            if line:
                                try:
                                    data = json.loads(line)
                                    entry = JournalEntry(**data)
                                    self._entries.append(entry)
                                except json.JSONDecodeError as decode_err:
                                    logger.debug(f"📓 Skipped corrupted line {line_num} in {filepath}: {decode_err}")
                                except Exception as e:
                                    logger.debug(f"📓 Error parsing line {line_num} in {filepath}: {e}")
                except Exception as e:
                    logger.warning(f"📓 Failed to open/read file {filepath}: {e}")
            
            # Sort by timestamp
            self._entries.sort(key=lambda e: e.timestamp)
            
            # Trim to max
            if len(self._entries) > self._max_memory:
                self._entries = self._entries[-self._max_memory:]
                
        except Exception as e:
            logger.error(f"📓 Failed to load journal: {e}")


# Singleton
_journal_instance: Optional[CognitiveJournal] = None


def get_cognitive_journal() -> CognitiveJournal:
    """Get or create the global CognitiveJournal instance."""
    global _journal_instance
    if _journal_instance is None:
        _journal_instance = CognitiveJournal()
    return _journal_instance
