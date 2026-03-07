"""
Vector Database Manager - Semantic Memory & Embeddings
Milvus/Pinecone interface for scenario storage and similarity search
"""
import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger("unified_core.db.vector")


@dataclass
class VectorSearchResult:
    id: str
    score: float
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None


@dataclass
class VectorQueryResult:
    success: bool
    results: List[VectorSearchResult] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class DistanceMetric(Enum):
    L2 = "L2"
    IP = "IP"  # Inner Product
    COSINE = "COSINE"


class VectorDBManager:
    """
    Vector database manager for semantic memory and embedding storage.
    Supports Milvus as primary backend with fallback to in-memory.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        collection_name: str = "unified_memory",
        dimension: int = 1536,  # OpenAI ada-002 / text-embedding-3
        metric_type: DistanceMetric = DistanceMetric.COSINE,
        use_memory_fallback: bool = True
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.dimension = dimension
        self.metric_type = metric_type
        self.use_memory_fallback = use_memory_fallback
        
        self._client = None
        self._collection = None
        self._initialized = False
        self._using_memory = False
        
        # In-memory fallback storage
        self._memory_vectors: Dict[str, Tuple[List[float], Dict]] = {}
        self._memory_index = None
    
    async def initialize(self) -> bool:
        """Initialize Milvus connection or fallback to memory."""
        if self._initialized:
            return True
        
        try:
            from pymilvus import (
                connections, Collection, FieldSchema,
                CollectionSchema, DataType, utility
            )
            
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                timeout=10
            )
            
            # Create collection if not exists
            if not utility.has_collection(self.collection_name):
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
                    FieldSchema(name="timestamp", dtype=DataType.INT64),
                ]
                schema = CollectionSchema(fields, description="Unified semantic memory")
                self._collection = Collection(self.collection_name, schema)
                
                # Create index
                index_params = {
                    "metric_type": self.metric_type.value,
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024}
                }
                self._collection.create_index("vector", index_params)
            else:
                self._collection = Collection(self.collection_name)
            
            self._collection.load()
            self._initialized = True
            logger.info(f"Milvus initialized: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Milvus unavailable: {e}, using memory fallback")
            if self.use_memory_fallback:
                self._using_memory = True
                self._initialized = True
                return True
            return False
    
    async def insert(
        self,
        id: str,
        vector: List[float],
        content: str,
        category: str = "general",
        metadata: Optional[Dict] = None
    ) -> bool:
        """Insert vector with metadata."""
        import time
        
        if not self._initialized:
            await self.initialize()
        
        try:
            if self._using_memory:
                self._memory_vectors[id] = (
                    vector,
                    {"content": content, "category": category, **(metadata or {})}
                )
                return True
            
            # Milvus insert
            import time as t
            entities = [
                [id],
                [vector],
                [content],
                [category],
                [int(t.time() * 1000)]
            ]
            self._collection.insert(entities)
            return True
            
        except Exception as e:
            logger.error(f"Vector insert failed: {e}")
            return False
    
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        category: Optional[str] = None,
        min_score: float = 0.0
    ) -> VectorQueryResult:
        """Semantic similarity search."""
        import time
        start = time.perf_counter()
        
        if not self._initialized:
            await self.initialize()
        
        try:
            if self._using_memory:
                return await self._memory_search(query_vector, top_k, category, min_score, start)
            
            # Milvus search
            search_params = {"metric_type": self.metric_type.value, "params": {"nprobe": 16}}
            
            # SECURITY FIX: Sanitize category to prevent expression injection
            expr = None
            if category:
                # Only allow alphanumeric and underscore in category
                import re
                if not re.match(r'^[A-Za-z0-9_]+$', category):
                    return VectorQueryResult(
                        success=False,
                        error=f"Invalid category: {category}",
                        execution_time_ms=(time.perf_counter() - start) * 1000
                    )
                expr = f'category == "{category}"'
            
            results = self._collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["content", "category"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    if hit.score >= min_score:
                        search_results.append(VectorSearchResult(
                            id=hit.id,
                            score=hit.score,
                            metadata={"content": hit.entity.get("content"), "category": hit.entity.get("category")}
                        ))
            
            return VectorQueryResult(
                success=True,
                results=search_results,
                total=len(search_results),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return VectorQueryResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
    
    async def _memory_search(
        self,
        query_vector: List[float],
        top_k: int,
        category: Optional[str],
        min_score: float,
        start: float
    ) -> VectorQueryResult:
        """In-memory vector similarity search using numpy."""
        import time
        
        if not self._memory_vectors:
            return VectorQueryResult(
                success=True,
                results=[],
                total=0,
                execution_time_ms=(time.perf_counter() - start) * 1000
            )
        
        query = np.array(query_vector)
        results = []
        
        for id, (vec, meta) in self._memory_vectors.items():
            if category and meta.get("category") != category:
                continue
            
            # Cosine similarity
            vec_np = np.array(vec)
            similarity = np.dot(query, vec_np) / (np.linalg.norm(query) * np.linalg.norm(vec_np))
            
            if similarity >= min_score:
                results.append(VectorSearchResult(
                    id=id,
                    score=float(similarity),
                    metadata=meta
                ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:top_k]
        
        return VectorQueryResult(
            success=True,
            results=results,
            total=len(results),
            execution_time_ms=(time.perf_counter() - start) * 1000
        )
    
    async def delete(self, ids: List[str]) -> bool:
        """Delete vectors by ID."""
        if not self._initialized:
            return False
        
        try:
            if self._using_memory:
                for id in ids:
                    self._memory_vectors.pop(id, None)
                return True
            
            expr = f'id in {ids}'
            self._collection.delete(expr)
            return True
        except Exception as e:
            logger.error(f"Vector delete failed: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if self._using_memory:
            return {
                "backend": "memory",
                "count": len(self._memory_vectors),
                "dimension": self.dimension
            }
        
        try:
            return {
                "backend": "milvus",
                "count": self._collection.num_entities,
                "dimension": self.dimension,
                "collection": self.collection_name
            }
        except Exception:
            return {"error": "Unable to get stats"}
    
    # Semantic memory specialized methods
    async def store_scenario(
        self,
        scenario_id: str,
        embedding: List[float],
        description: str,
        outcome: str,
        tags: List[str]
    ) -> bool:
        """Store scenario with semantic embedding for future retrieval."""
        return await self.insert(
            id=scenario_id,
            vector=embedding,
            content=f"{description}\n---\n{outcome}",
            category="scenario",
            metadata={"tags": tags, "outcome": outcome}
        )
    
    async def recall_similar_scenarios(
        self,
        situation_embedding: List[float],
        top_k: int = 5
    ) -> VectorQueryResult:
        """Recall similar scenarios for decision support."""
        return await self.search(
            query_vector=situation_embedding,
            top_k=top_k,
            category="scenario",
            min_score=0.7
        )
    
    async def store_memory(
        self,
        memory_id: str,
        embedding: List[float],
        content: str,
        memory_type: str = "episodic"
    ) -> bool:
        """Store semantic memory (episodic/semantic/procedural)."""
        return await self.insert(
            id=memory_id,
            vector=embedding,
            content=content,
            category=f"memory_{memory_type}"
        )
