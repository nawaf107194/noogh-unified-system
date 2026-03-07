"""
Memory Tools for ALLaM
Provides memory storage, recall, and statistics.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


async def store_memory(content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Store a memory in the system.
    
    Args:
        content: The content to store
        metadata: Optional metadata
        
    Returns:
        Dict with memory ID and status
    """
    try:
        from neural_engine.memory_consolidator import MemoryConsolidator
        
        # Get or create memory consolidator
        consolidator = MemoryConsolidator(base_dir="./data")
        
        memory_id = consolidator.store_memory(
            content=content,
            metadata=metadata or {"source": "allam_tool"}
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "summary_ar": f"تم حفظ الذاكرة بنجاح (ID: {memory_id[:8]}...)"
        }
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل حفظ الذاكرة: {str(e)}"
        }


async def recall_memory(query: str, n_results: int = 5) -> Dict[str, Any]:
    """
    Recall memories based on semantic search.
    
    Args:
        query: Search query
        n_results: Number of results
        
    Returns:
        Dict with matching memories
    """
    try:
        from neural_engine.recall_engine import get_recall_engine
        
        engine = get_recall_engine()
        memories = await engine.recall(query, n_results=n_results)
        
        results = []
        for mem in memories:
            results.append({
                "id": mem.get("id", "unknown"),
                "content": mem.get("content", "")[:200],
                "similarity": round(mem.get("similarity", 0), 3)
            })
        
        return {
            "success": True,
            "count": len(results),
            "memories": results,
            "summary_ar": f"تم العثور على {len(results)} ذكريات متعلقة بـ '{query[:30]}...'"
        }
    except Exception as e:
        logger.error(f"Failed to recall memories: {e}")
        return {
            "success": False,
            "error": str(e),
            "memories": [],
            "summary_ar": f"فشل استرجاع الذاكرة: {str(e)}"
        }


def get_memory_stats() -> Dict[str, Any]:
    """
    Get memory system statistics.
    
    Returns:
        Dict with memory stats
    """
    try:
        from neural_engine.recall_engine import get_recall_engine
        
        engine = get_recall_engine()
        stats = engine.get_collection_stats()
        
        return {
            "success": True,
            "total_memories": stats.get("total_memories", 0),
            "collection_name": stats.get("collection_name", "unknown"),
            "summary_ar": f"إجمالي الذكريات المخزنة: {stats.get('total_memories', 0)}"
        }
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_memories": 0,
            "summary_ar": f"فشل قراءة إحصائيات الذاكرة: {str(e)}"
        }


# Tool registration helper
def register_memory_tools(registry=None):
    """NO-OP: Tools are now defined in unified_core.tools.definitions.
    
    This function previously registered tools with the deprecated
    neural_engine.tools.tool_registry. All tools are now managed
    statically via unified_core.tool_registry.
    """
    logger.debug(
        "register_memory_tools() is superseded by unified_core.tools.definitions"
    )
