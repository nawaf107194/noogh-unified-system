import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


logger = logging.getLogger("memory")


@dataclass
class MemoryEntry:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)


class WorkingMemory:
    """
    Short-term context for the Agent's current task.
    Stored in RAM, cleared between tasks.
    """

    def __init__(self, max_entries: int = 50):
        self.entries: List[MemoryEntry] = []
        self.max_entries = max_entries

    def add(self, role: str, content: str):
        self.entries.append(MemoryEntry(role=role, content=content))
        # Enforce max entries by trimming oldest
        if len(self.entries) > getattr(self, "max_entries", 50):
            excess = len(self.entries) - self.max_entries
            if excess > 0:
                self.entries = self.entries[excess:]

    def clear(self):
        self.entries = []

    def to_context(self) -> str:
        """Format memory as a string for the LLM."""
        lines = []
        for entry in self.entries:
            # Title-case the role for human-friendly formatting (tests expect 'User', 'Agent')
            lines.append(f"{entry.role.title()}: {entry.content}")
        return "\n".join(lines)

    def get_recent(self, n: int) -> List[MemoryEntry]:
        """Return the most recent `n` memory entries."""
        if n <= 0:
            return []
        return list(self.entries[-n:])

    def get_by_role(self, role: str) -> List[MemoryEntry]:
        """Return entries matching a given role (case-insensitive)."""
        role_lower = role.lower()
        return [e for e in self.entries if e.role.lower() == role_lower]

    def __len__(self):
        return len(self.entries)


# Note: PersistentSemanticMemory removed to decouple Gateway from Neural package.
# Gateway now uses SemanticMemory with a NeuralClient to communicate via API.


class SemanticMemory:
    """
    Long-term semantic memory for storing and recalling embeddings.
    Communicates with the Neural Engine via NeuralClient.
    """

    def __init__(self, neural_client: Any = None):
        if not neural_client:
            logger.warning("SemanticMemory initialized without NeuralClient! Long-term memory will be unavailable.")
        self.client = neural_client

    async def add(self, content: str, metadata: Dict = None):
        """Add a memory via Neural Engine API.
        
        SECURITY: Content is sanitized before storage to prevent prompt injection.
        """
        if not self.client:
            logger.error("Cannot store memory: No NeuralClient configured.")
            return

        try:
            # SECURITY FIX (P1-2): Sanitize content before storage
            sanitized_content = self._sanitize_memory(content)
            await self.client.store_memory(sanitized_content, metadata)
        except Exception as e:
            logger.error(f"Failed to store remote memory: {e}")
            raise  # Re-raise to alert the caller
    
    def _sanitize_memory(self, content: str) -> str:
        """
        Sanitizes content before storage in VectorDB.
        Removes prompt injection vectors and role-spoofing tags.
        
        SECURITY (P1-2 Fix): Prevents agents from overriding system prompts.
        """
        # Block Common Injection Patterns (case-insensitive)
        blocklist = [
            # Role spoofing 
            "[SYSTEM]", "SYSTEM:", "[INST]", "[/INST]",
            # Override attempts
            "IGNORE ALL PREVIOUS", "Ignore previous instructions",
            "forget your instructions", "disregard above",
            "new instructions:", "override:",
        ]
        
        clean_content = content
        for pattern in blocklist:
            # Redact the pattern case-insensitively
            clean_content = re.sub(
                re.escape(pattern), 
                "[REDACTED]", 
                clean_content, 
                flags=re.IGNORECASE
            )
        
        # Log if we sanitized anything
        if clean_content != content:
            logger.warning("SECURITY: Memory content sanitized - injection patterns removed")
        
        return clean_content

    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for relevant memories via Neural Engine API."""
        if not self.client:
            logger.warning("Cannot search memory: No NeuralClient configured.")
            return []

        try:
            response = await self.client.recall_memory(query, n_results=limit)
            if response.success:
                return response.data.get("memories", [])
            return []
        except Exception as e:
            logger.error(f"Failed to search remote memory: {e}")
            return []
