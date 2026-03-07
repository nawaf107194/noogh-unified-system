"""
Memory consolidation system for Noug Neural OS.
Processes Short-Term Memory (STM) and moves important items to Long-Term Memory (LTM).
Handles vectorization and storage operations using ChromaDB.
Enhanced with GPU-accelerated embeddings.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
import torch
from pydantic import (  # Kept this as it's used later and not explicitly removed by the instruction's snippet
    BaseModel,
    Field,
)
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class MemoryUnit(BaseModel):
    """Represents a single atomic unit of memory."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    embedding: Optional[List[float]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance: float = 0.5

    # Links to other memories (Graph structure)
    related_memory_ids: List[str] = Field(default_factory=list)


class MemoryConsolidator:
    """
    Enhanced memory consolidator with GPU-accelerated embeddings.
    Stores memories in ChromaDB with semantic embeddings.
    """

    def __init__(self, base_dir: str, collection_name: str = "memories", use_gpu: bool = True):
        """
        Initialize memory consolidator with GPU support.

        Args:
            base_dir: Base data directory (injected)
            collection_name: Name of the ChromaDB collection
            use_gpu: Whether to use GPU for embeddings
        """
        import os

        if not base_dir:
            raise RuntimeError("base_dir is REQUIRED for MemoryConsolidator")

        self.vector_db_path = os.path.join(base_dir, "chroma")

        self.collection_name = collection_name

        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = "cuda" if self.use_gpu else "cpu"

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=self.vector_db_path)

        # Initialize embedding model on the determined device
        logger.info(f"Loading embedding model on {self.device}...")
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

        if self.use_gpu:
            self.embed_model = self.embed_model.to(self.device)
            logger.info("✅ Embedding model loaded on GPU")
            logger.info(f"   Device: {self.device}")
            # Note: Memory usage is approximate and depends on model size and other factors
            logger.info("   Estimated GPU Memory: ~500 MB")
        else:
            logger.info("Embedding model loaded on CPU")

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"description": "Long-term memory storage for Noug Neural OS"}
        )

        logger.info(f"MemoryConsolidator initialized at {self.vector_db_path}")
        logger.info(f"Collection '{collection_name}' ready with {self.collection.count()} existing memories")

    def _generate_embedding(self, content: str) -> List[float]:
        """Generate vector embedding for content."""
        try:
            embedding = self.embed_model.encode(content, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    def store_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_scope: str = "default",
    ) -> str:
        """
        Store a memory with GPU-accelerated embeddings and session isolation.

        Args:
            content: The memory content to store
            metadata: Optional metadata dictionary
            session_id: Session identifier for isolation (default: "global")
            user_scope: User scope (admin/service/readonly/default)

        Returns:
            Memory ID
        """
        if metadata is None:
            metadata = {}

        # Inject session context for isolation
        metadata["session_id"] = session_id or "global"
        metadata["user_scope"] = user_scope
        metadata["stored_at"] = datetime.utcnow().isoformat()

        try:
            # Generate embedding on GPU
            embedding = self.embed_model.encode(  # Changed from self.embedding_model to self.embed_model
                content, convert_to_tensor=True, device=self.device
            )

            # Convert to list for ChromaDB
            if self.use_gpu:
                embedding = embedding.cpu().numpy().tolist()
            else:
                embedding = embedding.tolist()

            # Generate unique ID
            import hashlib
            import time

            memory_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()

            # Store in ChromaDB
            self.collection.add(embeddings=[embedding], documents=[content], metadatas=[metadata], ids=[memory_id])

            logger.info(f"✅ Memory stored (ID: {memory_id[:8]}...) on {self.device}")
            return memory_id

        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            raise

        # The original code had a return memory here, but memory is not defined.
        # Given the return type is str (memory_id), this line should be removed or unreachable.
        # Removing it as it's likely a copy-paste error from a different context.
        # return memory

    async def batch_store(self, items: List[str]) -> List[MemoryUnit]:
        """Store multiple items efficiently."""
        memories = []
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for item in items:
            memory = MemoryUnit(content=item)
            memory.embedding = self._generate_embedding(item)

            memories.append(memory)
            ids.append(memory.id)
            embeddings.append(memory.embedding)
            documents.append(item)
            metadatas.append(
                {"timestamp": memory.timestamp.isoformat(), "importance": memory.importance, "type": "batch"}
            )

        # Batch add to ChromaDB
        try:
            self.collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
            logger.info(f"Batch stored {len(items)} memories")
        except Exception as e:
            logger.error(f"Error in batch store: {e}")
            raise

        return memories

    def get_stats(self) -> Dict[str, Any]:
            """Get memory statistics with improved validation and logging."""
            try:
                if not hasattr(self, 'collection') or not hasattr(self, 'collection_name') or not hasattr(self, 'vector_db_path'):
                    raise AttributeError("Missing required attributes: collection, collection_name, vector_db_path")
            
                total_memories = self.collection.count()
                if not isinstance(total_memories, int):
                    raise TypeError("Expected 'total_memories' to be an integer.")
            
                if not isinstance(self.collection_name, str):
                    raise TypeError("Expected 'collection_name' to be a string.")
            
                if not isinstance(self.vector_db_path, str):
                    raise TypeError("Expected 'vector_db_path' to be a string.")
            
                return {
                    "total_memories": total_memories,
                    "collection_name": self.collection_name,
                    "db_path": self.vector_db_path,
                }
            except Exception as e:
                logging.error(f"Error in get_stats: {e}")
                raise

    async def store(self, content: str, metadata: dict = None, session_id: str = None, user_scope: str = "default"):
        """Alias for store_memory for backward compatibility"""
        return self.store_memory(content, metadata or {}, session_id=session_id, user_scope=user_scope)

    async def recall_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Recall the most recent n memories.

        Args:
            n: Number of memories to recall

        Returns:
            List of memory dictionaries
        """
        try:
            # Simple peek/query to get recent items
            # ChromaDB's peek often returns first n items.
            # Ideally we sort by timestamp in metadata, but for now we take what we can.
            results = self.collection.peek(limit=n)

            memories = []
            if results and results["ids"]:
                for i in range(len(results["ids"])):
                    memories.append(
                        {
                            "id": results["ids"][i],
                            "content": results["documents"][i],
                            "metadata": results["metadatas"][i] if results["metadatas"] else {},
                        }
                    )
            return memories
        except Exception as e:
            logger.error(f"Error recalling recent memories: {e}")
            return []

    async def recall_by_type(self, type_filter: str, n: int = 10) -> List[Dict[str, Any]]:
        """
        Recall memories filtered by a specific metadata type.

        Args:
            type_filter: The concept_type or 'type' to filter by (e.g. 'system_error')
            n: Number of memories to recall

        Returns:
            List of memory dictionaries
        """
        try:
            # First try matching 'type' field in metadata
            results = self.collection.get(where={"type": type_filter}, limit=n)

            # If no results, try 'concept_type' (for the classifier job results)
            if not results["ids"]:
                results = self.collection.get(where={"concept_type": type_filter}, limit=n)

            memories = []
            if results and results["ids"]:
                for i in range(len(results["ids"])):
                    memories.append(
                        {
                            "id": results["ids"][i],
                            "content": results["documents"][i],
                            "metadata": results["metadatas"][i] if results["metadatas"] else {},
                        }
                    )
            return memories
        except Exception as e:
            logger.error(f"Error recalling by type '{type_filter}': {e}")
            return []

    async def recall(
        self, query: str, n_results: int = 5, session_id: Optional[str] = None, user_scope: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Recall memories with session isolation and semantic search.

        Args:
            query: Search query
            n_results: Number of results to return
            session_id: Session to filter by (None for current session, "global" for all)
            user_scope: User scope for access control

        Returns:
            List of relevant memories
        """
        try:
            # Build where filter for session isolation
            where_filter = {}

            if session_id is not None:
                where_filter["session_id"] = session_id

            # Admin scope can see all, others only their scope
            if user_scope != "admin":
                where_filter["user_scope"] = user_scope

            # Generate query embedding
            query_embedding = self.embed_model.encode(query, convert_to_tensor=True, device=self.device)

            if self.use_gpu:
                query_embedding = query_embedding.cpu().numpy().tolist()
            else:
                query_embedding = query_embedding.tolist()

            # Query with filters
            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=n_results, where=where_filter if where_filter else None
            )

            memories = []
            if results and results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    memories.append(
                        {
                            "id": results["ids"][0][i],
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                            "distance": results["distances"][0][i] if "distances" in results else None,
                        }
                    )

            logger.info(f"Recalled {len(memories)} memories for session={session_id}, scope={user_scope}")
            return memories

        except Exception as e:
            logger.error(f"Error recalling memories: {e}")
            return []

    def update_metadata(self, memory_id: str, metadata: Dict[str, Any]):
        """Update metadata for an existing memory."""
        try:
            self.collection.update(ids=[memory_id], metadatas=[metadata])
            logger.info(f"Updated metadata for memory {memory_id}")
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
