"""
ChromaDB Vector Store - Semantic Tool Matching

Enables semantic matching of user queries to tools using embeddings.
Useful when exact keyword matching fails.

Example:
    "save this file" → matches filesystem.write
    "put data here" → matches filesystem.write
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. pip install chromadb")


class SemanticToolMatcher:
    """Matches user queries to tools using semantic similarity."""
    
    def __init__(
        self, 
        collection_name: str = "noogh_tools",
        persist_directory: Optional[str] = None,
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed. pip install chromadb")
        
        self.collection_name = collection_name
        
        # Initialize client
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        
        # Use default embedding function (sentence-transformers)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "NOOGH tool registry for semantic matching"}
        )
        
        logger.info(f"ChromaDB collection '{collection_name}' initialized")
    
    def index_tools(self, tool_registry: Dict[str, Any]) -> int:
        """
        Index tools from the registry for semantic search.
        
        Args:
            tool_registry: Dict of tool_name -> tool_definition
            
        Returns:
            Number of tools indexed
        """
        documents = []
        metadatas = []
        ids = []
        
        for tool_name, tool_def in tool_registry.items():
            # Create searchable document from tool info
            description = tool_def.get("description", "")
            category = tool_def.get("category", "")
            schema = json.dumps(tool_def.get("schema", {}))
            
            # Combine into searchable text
            doc = f"""
            Tool: {tool_name}
            Category: {category}
            Description: {description}
            Example queries: {self._generate_example_queries(tool_name)}
            """
            
            documents.append(doc)
            metadatas.append({
                "tool_name": tool_name,
                "category": category,
                "schema": schema,
            })
            ids.append(tool_name)
        
        # Upsert (add or update)
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        
        logger.info(f"Indexed {len(documents)} tools in ChromaDB")
        return len(documents)
    
    def _generate_example_queries(self, tool_name: str) -> str:
        """Generate example queries for a tool to improve matching."""
        examples = {
            "filesystem.read": "read file, show contents, open file, display file, get file content",
            "filesystem.write": "write file, save file, create file, store data, put content",
            "filesystem.exists": "check file exists, does file exist, verify file, file exists",
            "filesystem.list": "list files, show directory, dir contents, ls folder",
            "filesystem.delete": "delete file, remove file, erase file",
            "calculator.add": "add numbers, sum, plus, addition, calculate sum",
            "calculator.multiply": "multiply, times, product, multiplication",
            "calculator.compute": "calculate expression, compute, evaluate math",
            "http.get": "fetch url, get webpage, http request, download",
            "http.post": "post data, send request, submit form",
            "process.run": "run command, execute, shell, terminal command",
            "noop": "hello, thanks, general question, chat, conversation",
            "finish": "done, complete, finished, end task, all done",
        }
        return examples.get(tool_name, "")
    
    def match(
        self, 
        query: str, 
        n_results: int = 3,
        threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Match a user query to the most similar tools.
        
        Args:
            query: User's natural language query
            n_results: Number of results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matched tools with scores
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["metadatas", "distances"],
        )
        
        matches = []
        for i, (tool_id, distance, metadata) in enumerate(zip(
            results["ids"][0],
            results["distances"][0],
            results["metadatas"][0],
        )):
            # Convert distance to similarity score (ChromaDB uses L2 distance)
            # Lower distance = higher similarity
            similarity = 1 / (1 + distance)
            
            if similarity >= threshold:
                matches.append({
                    "tool_name": metadata["tool_name"],
                    "category": metadata["category"],
                    "similarity": round(similarity, 4),
                    "rank": i + 1,
                })
        
        return matches
    
    def get_best_match(self, query: str, threshold: float = 0.3) -> Optional[str]:
        """Get the single best matching tool for a query."""
        matches = self.match(query, n_results=1, threshold=threshold)
        if matches:
            return matches[0]["tool_name"]
        return None
    
    @classmethod
    def from_spec_file(cls, spec_path: str, persist_dir: Optional[str] = None) -> "SemanticToolMatcher":
        """
        Create a matcher from a tool_mapping_spec.json file.
        
        Args:
            spec_path: Path to tool_mapping_spec.json
            persist_dir: Optional directory to persist the vector store
        """
        with open(spec_path) as f:
            spec = json.load(f)
        
        matcher = cls(persist_directory=persist_dir)
        matcher.index_tools(spec.get("tools", {}))
        return matcher


# Convenience function
def create_tool_matcher(persist: bool = False) -> SemanticToolMatcher:
    """Create a tool matcher using the default registry."""
    spec_path = Path(__file__).parent.parent / "config" / "tool_mapping_spec.json"
    persist_dir = str(Path(__file__).parent.parent / ".data" / "chroma") if persist else None
    
    return SemanticToolMatcher.from_spec_file(str(spec_path), persist_dir)
