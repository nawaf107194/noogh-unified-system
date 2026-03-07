"""
Pinecone Vector Store - Production-Scale Semantic Search

Cloud-hosted vector database for production deployments.
Replaces ChromaDB when scaling to production.
"""

from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("Pinecone not installed. pip install pinecone-client")


class PineconeToolStore:
    """Production-scale vector store using Pinecone."""
    
    def __init__(
        self,
        api_key: str,
        index_name: str = "noogh-tools",
        cloud: str = "aws",
        region: str = "us-east-1",
        dimension: int = 384,  # Default for sentence-transformers
    ):
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone not installed. pip install pinecone-client")
        
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.dimension = dimension
        
        # Create index if not exists
        if index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=cloud, region=region),
            )
            logger.info(f"Created Pinecone index: {index_name}")
        
        self.index = self.pc.Index(index_name)
        logger.info(f"Connected to Pinecone index: {index_name}")
    
    def upsert_tools(
        self,
        tools: Dict[str, Any],
        embeddings: Dict[str, List[float]],
    ) -> int:
        """
        Upsert tool embeddings to Pinecone.
        
        Args:
            tools: Dict of tool_name -> tool_definition
            embeddings: Dict of tool_name -> embedding vector
        """
        vectors = []
        for tool_name, tool_def in tools.items():
            if tool_name in embeddings:
                vectors.append({
                    "id": tool_name,
                    "values": embeddings[tool_name],
                    "metadata": {
                        "category": tool_def.get("category", ""),
                        "description": tool_def.get("description", ""),
                    },
                })
        
        if vectors:
            self.index.upsert(vectors=vectors)
            logger.info(f"Upserted {len(vectors)} tools to Pinecone")
        
        return len(vectors)
    
    def query(
        self,
        embedding: List[float],
        top_k: int = 3,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """Query for similar tools."""
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=include_metadata,
        )
        
        matches = []
        for match in results.matches:
            matches.append({
                "tool_name": match.id,
                "score": match.score,
                "metadata": match.metadata if include_metadata else {},
            })
        
        return matches
    
    def delete_all(self):
        """Delete all vectors from index."""
        self.index.delete(delete_all=True)
        logger.info("Deleted all vectors from Pinecone index")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return self.index.describe_index_stats()


class PineconeToolMatcher:
    """High-level tool matcher using Pinecone."""
    
    def __init__(
        self,
        api_key: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        **kwargs,
    ):
        self.store = PineconeToolStore(api_key=api_key, **kwargs)
        self.embedding_model = embedding_model
        self._embedder = None
    
    @property
    def embedder(self):
        """Lazy load embedder."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(self.embedding_model)
            except ImportError:
                raise ImportError("sentence-transformers not installed")
        return self._embedder
    
    def embed(self, text: str) -> List[float]:
        """Embed a text string."""
        return self.embedder.encode(text).tolist()
    
    def index_tools(self, tool_registry: Dict[str, Any]) -> int:
        """Index tools from registry."""
        embeddings = {}
        for tool_name, tool_def in tool_registry.items():
            text = f"{tool_name} {tool_def.get('description', '')} {tool_def.get('category', '')}"
            embeddings[tool_name] = self.embed(text)
        
        return self.store.upsert_tools(tool_registry, embeddings)
    
    def match(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Match a query to tools."""
        embedding = self.embed(query)
        return self.store.query(embedding, top_k=top_k)
    
    def get_best_match(self, query: str, threshold: float = 0.5) -> Optional[str]:
        """Get the best matching tool above threshold."""
        matches = self.match(query, top_k=1)
        if matches and matches[0]["score"] >= threshold:
            return matches[0]["tool_name"]
        return None
