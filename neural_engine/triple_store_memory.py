"""
Triple-Store Memory Manager for NOOGH Neural Engine.
Separates facts, dreams, and hypotheses into distinct collections.
"""

import hashlib
import logging
import time
from typing import Any, Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class TripleStoreMemory:
    """Triple-store memory architecture: facts / dreams / hypotheses."""

    def __init__(self, base_dir: str):
        self.client = chromadb.PersistentClient(path=base_dir)

        # Three separate collections
        self.facts = self.client.get_or_create_collection(
            "facts", metadata={"description": "Ground truth: user inputs, logs, metrics"}
        )
        self.dreams = self.client.get_or_create_collection(
            "dreams", metadata={"description": "Hallucinated insights from autonomous processing"}
        )
        self.hypotheses = self.client.get_or_create_collection(
            "hypotheses", metadata={"description": "Unverified inferences and annotations"}
        )

        # Embedding model
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("MemoryManager initialized with triple-store architecture")

    def _embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        return self.embed_model.encode(text, convert_to_numpy=True).tolist()

    def _gen_id(self, content: str) -> str:
        """Generate unique ID for memory."""
        return hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()

    def store_fact(self, content: str, source: str, metadata: Optional[dict] = None):
        """Store factual observation (user inputs, logs, system events)."""
        import datetime
        timestamp = time.time()
        id = self._gen_id(content)
        meta = metadata or {}
        meta.update({"source": source, "type": "fact", "timestamp": timestamp})

        self.facts.add(
            embeddings=[self._embed(content)], documents=[content], metadatas=[meta], ids=[id]
        )
        logger.debug(f"Stored fact: {content[:50]}...")
        
        # Return a structure compatible with the API response
        from dataclasses import dataclass
        @dataclass
        class StoredMemory:
            id: str
            content: str
            timestamp: Any # datetime object
        
        return StoredMemory(id=id, content=content, timestamp=datetime.datetime.fromtimestamp(timestamp))

    def store_dream(self, content: str, confidence: float, metadata: Optional[dict] = None):
        """Store dream insight (hallucination from pattern discovery)."""
        meta = metadata or {}
        meta.update({"confidence": confidence, "type": "dream", "timestamp": time.time()})

        self.dreams.add(
            embeddings=[self._embed(content)], documents=[content], metadatas=[meta], ids=[self._gen_id(content)]
        )
        logger.debug(f"Stored dream insight: {content[:50]}...")

    def store_hypothesis(self, content: str, confidence: float, metadata: Optional[dict] = None):
        """Store hypothesis (unverified inference)."""
        meta = metadata or {}
        meta.update({"confidence": confidence, "type": "hypothesis", "timestamp": time.time()})

        self.hypotheses.add(
            embeddings=[self._embed(content)], documents=[content], metadatas=[meta], ids=[self._gen_id(content)]
        )
        logger.debug(f"Stored hypothesis: {content[:50]}...")

    def recall_facts(self, query: str, n: int = 5) -> List[Dict[str, Any]]:
        """Recall facts only (operational mode - no hallucinations)."""
        if self.facts.count() == 0:
            return []

        results = self.facts.query(query_embeddings=[self._embed(query)], n_results=min(n, self.facts.count()))

        memories = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                memories.append(
                    {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "similarity": 1.0 - results["distances"][0][i],
                    }
                )
        return memories

    def recall_with_dreams(self, query: str, n_facts: int = 5, n_dreams: int = 2) -> Dict[str, Any]:
        """Explicit dream inclusion (research/analysis mode only)."""
        facts = self.recall_facts(query, n_facts)

        dreams = []
        if self.dreams.count() > 0:
            dream_results = self.dreams.query(
                query_embeddings=[self._embed(query)], n_results=min(n_dreams, self.dreams.count())
            )
            if dream_results and dream_results["ids"] and len(dream_results["ids"][0]) > 0:
                for i in range(len(dream_results["ids"][0])):
                    dreams.append(
                        {
                            "id": dream_results["ids"][0][i],
                            "content": dream_results["documents"][0][i],
                            "metadata": dream_results["metadatas"][0][i],
                            "distance": dream_results["distances"][0][i],
                        }
                    )

        return {"facts": facts, "dreams": dreams, "mixed": True}  # Explicitly flag that dreams are included

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics on memory collections."""
        return {
            "facts": self.facts.count(),
            "dreams": self.dreams.count(),
            "hypotheses": self.hypotheses.count(),
            "total": self.facts.count() + self.dreams.count() + self.hypotheses.count(),
        }

    # Legacy compatibility methods (delegate to facts)
    def store(self, content: str, metadata: Optional[dict] = None):
        """Legacy store method - stores as fact by default."""
        return self.store_fact(content, source="legacy", metadata=metadata)

    def recall(self, query: str, n: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Legacy recall method - returns facts only for safety."""
        return self.recall_facts(query, n)

    # DreamProcessor Compatibility Methods
    def recall_recent(self, n: int = 10) -> List[Dict[str, Any]]:
            """
            Retrieve recent context.
            Since we don't have a time-ordered index in simplified Chroma usage,
            we use a generic 'current context' semantic query.
            """
            if not isinstance(n, int):
                self.logger.error("The parameter 'n' must be an integer.")
                raise TypeError("The parameter 'n' must be an integer.")
            if n <= 0:
                self.logger.error("The parameter 'n' must be a positive integer.")
                raise ValueError("The parameter 'n' must be a positive integer.")

            try:
                result = self.recall_facts("current state context", n)
                if not result:
                    self.logger.warning("No results found for the recent context query.")
                return result
            except TypeError as te:
                self.logger.error(f"Type error occurred while fetching recent context: {te}")
                raise
            except ValueError as ve:
                self.logger.error(f"Value error occurred while fetching recent context: {ve}")
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error occurred while fetching recent context: {e}")
                raise

    def recall_by_type(self, type_str: str, n: int = 5) -> List[Dict[str, Any]]:
            """
            Recall by semantic type.
            Maps 'system_error' -> semantic search for 'system error'.
            """
            if not isinstance(type_str, str):
                raise TypeError("type_str must be a string")
            if not isinstance(n, int) or n <= 0:
                raise ValueError("n must be a positive integer")

            # Replace underscores with spaces for better semantic embedding
            query = type_str.replace("_", " ")
            try:
                return self.recall_facts(query, n)
            except Exception as e:
                self.logger.error(f"Error occurred during recall_facts: {e}")
                raise
