import logging
from typing import Any, Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class RecallEngine:
    """
    Retrieves relevant memories from Long-Term Memory using semantic search.
    """

    def __init__(self, vector_db_path: str = "./data/chroma", collection_name: str = "memories"):
        self.vector_db_path = vector_db_path
        self.collection_name = collection_name

        # Initialize ChromaDB client (new API)
        try:
            self.client = chromadb.PersistentClient(path=vector_db_path)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ChromaDB client with path '{vector_db_path}': {e}")

        # Get collection (must exist from MemoryConsolidator)
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(
                f"RecallEngine connected to collection '{collection_name}' with {self.collection.count()} memories"
            )
        except Exception as e:
            logger.warning(f"Collection '{collection_name}' not found, creating new one: {e}")
            try:
                self.collection = self.client.create_collection(
                    name=collection_name, metadata={"description": "Long-term memory storage for Noug Neural OS"}
                )
                logger.info(f"Created new collection '{collection_name}'")
            except Exception as create_err:
                raise RuntimeError(f"Failed to create collection '{collection_name}': {create_err}")

        # Initialize embedding model (same as MemoryConsolidator)
        try:
            self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize embedding model: {e}")

    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        try:
            embedding = self.embed_model.encode(query, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            return []

    async def recall(
        self, query: str, n_results: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search to recall relevant memories.

        Args:
            query: Search query text
            n_results: Number of results to return
            filters: Optional metadata filters (e.g., {"type": "input"})

        Returns:
            List of memory dictionaries with content, metadata, and similarity scores
        """
        if not query.strip():
            logger.warning("Empty query provided to recall")
            return []

        # Generate query embedding
        query_embedding = self._generate_query_embedding(query)

        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        # Check if collection is empty to avoid Chroma error
        count = self.collection.count()
        if count == 0:
            logger.info("Collection is empty, returning no memories")
            return []

        try:
            # Perform vector search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, count),
                where=filters if filters else None,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            memories = []
            if results and results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    memory = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                    }
                    memories.append(memory)

            logger.info(f"Recalled {len(memories)} memories for query: '{query[:50]}...'")
            return memories

        except Exception as e:
            logger.error(f"Error during recall: {e}")
            return []

    async def recall_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID."""
        try:
            result = self.collection.get(ids=[memory_id], include=["documents", "metadatas"])

            if result and result["ids"]:
                return {"id": result["ids"][0], "content": result["documents"][0], "metadata": result["metadatas"][0]}
            return None

        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {e}")
            return None

    async def recall_recent(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """Recall most recent memories (by timestamp)."""
        try:
            # Get all memories and sort by timestamp
            all_results = self.collection.get(
                include=["documents", "metadatas"],
                limit=n_results * 2,  # Get more to ensure we have enough after sorting
            )

            if not all_results or not all_results["ids"]:
                return []

            # Combine and sort by timestamp
            memories = []
            for i in range(len(all_results["ids"])):
                memory = {
                    "id": all_results["ids"][i],
                    "content": all_results["documents"][i],
                    "metadata": all_results["metadatas"][i],
                    "timestamp": all_results["metadatas"][i].get("timestamp", ""),
                }
                memories.append(memory)

            # Sort by timestamp descending
            memories.sort(key=lambda x: x["timestamp"], reverse=True)

            return memories[:n_results]

        except Exception as e:
            logger.error(f"Error recalling recent memories: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory collection."""
        try:
            total_memories = self.collection.count()
            return {
                "total_memories": total_memories,
                "collection_name": self.collection_name,
                "db_path": self.vector_db_path,
            }
        except Exception as e:
            logger.error(f"Error in get_collection_stats: {e}")
            return {}


# ============================================================================
# SINGLETON PATTERN - Unified Memory Instance
# ============================================================================

_recall_engine_instance: Optional[RecallEngine] = None

def get_recall_engine(
    vector_db_path: Optional[str] = None,
    collection_name: str = "memories"
) -> RecallEngine:
    """
    Get or create the global RecallEngine singleton.
    
    This ensures all components share the same memory instance,
    preventing the fragmentation issues identified in the GPT audit.
    
    Args:
        vector_db_path: Path to ChromaDB (uses NOOGH_DATA_DIR if not specified)
        collection_name: Name of the memory collection
        
    Returns:
        Shared RecallEngine instance
    """
    global _recall_engine_instance
    
    if _recall_engine_instance is None:
        import os
        if vector_db_path is None:
            data_dir = os.getenv("NOOGH_DATA_DIR", "./data")
            vector_db_path = os.path.join(data_dir, "chroma")
        
        _recall_engine_instance = RecallEngine(
            vector_db_path=vector_db_path,
            collection_name=collection_name
        )
        logger.info(f"🧠 RecallEngine singleton initialized at {vector_db_path}")
    
    return _recall_engine_instance


def reset_recall_engine():
    """
    Reset the singleton (for testing or reinitialization).
    """
    global _recall_engine_instance
    _recall_engine_instance = None
    logger.info("🧠 RecallEngine singleton reset")
