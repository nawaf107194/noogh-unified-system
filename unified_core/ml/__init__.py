"""
ML Module - Vector Stores & Experiment Tracking

Provides:
- ChromaDB: Local semantic tool matching (prototyping)
- Pinecone: Production vector search (cloud)
- W&B: Experiment tracking
"""

from .vector_store import SemanticToolMatcher, create_tool_matcher, CHROMADB_AVAILABLE
from .experiment_tracker import ExperimentTracker, LocalExperimentTracker, get_tracker, WANDB_AVAILABLE
from .pinecone_store import PineconeToolStore, PineconeToolMatcher, PINECONE_AVAILABLE

__all__ = [
    # ChromaDB
    "SemanticToolMatcher",
    "create_tool_matcher",
    "CHROMADB_AVAILABLE",
    
    # Pinecone
    "PineconeToolStore",
    "PineconeToolMatcher",
    "PINECONE_AVAILABLE",
    
    # W&B
    "ExperimentTracker",
    "LocalExperimentTracker",
    "get_tracker",
    "WANDB_AVAILABLE",
]
