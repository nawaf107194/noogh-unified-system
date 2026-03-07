"""
Semantic Tool Ranker - ChromaDB-based

Two-stage constrained routing:
1. Semantic Ranker: ranks tools by query similarity (top_k only)
2. Tool Policy Model: selects from candidates

Rules:
- ONLY returns tools from registry
- No invented tools ever
- Fallback to all tools if ranking fails
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available - semantic ranking disabled")


# =============================================================================
# TOOL REGISTRY (13 tools - matches tool_mapping_spec.json)
# =============================================================================

TOOL_REGISTRY = {
    "filesystem.read": {
        "description": "Read file contents from filesystem. قراءة محتوى ملف",
        "examples": ["read file", "show contents", "open file", "get file content", "اقرأ الملف", "اعرض محتوى", "افتح الملف", "قراءة"],
        "category": "filesystem",
    },
    "filesystem.write": {
        "description": "Write content to a file. كتابة محتوى في ملف",
        "examples": ["write file", "save file", "create file", "store data", "اكتب في الملف", "احفظ", "سجّل", "كتابة", "إنشاء ملف", "ضع النص"],
        "category": "filesystem",
    },
    "filesystem.exists": {
        "description": "Check if a file or path exists. التحقق من وجود ملف",
        "examples": ["file exists", "check file", "does it exist", "هل الملف موجود", "تحقق من وجود", "موجود", "exists"],
        "category": "filesystem",
    },
    "filesystem.list": {
        "description": "List files in a directory. عرض الملفات في مجلد",
        "examples": ["list files", "show directory", "ls", "what's in folder", "اعرض الملفات", "قائمة الملفات", "المجلد", "dir", "الملفات في"],
        "category": "filesystem",
    },
    "filesystem.delete": {
        "description": "Delete a file. حذف ملف",
        "examples": ["delete file", "remove file", "erase", "احذف الملف", "امسح", "حذف", "rm"],
        "category": "filesystem",
    },
    "calculator.add": {
        "description": "Add two numbers. جمع رقمين",
        "examples": ["add", "plus", "sum", "5 + 3", "اجمع", "زائد", "مجموع", "جمع", "addition"],
        "category": "calculator",
    },
    "calculator.multiply": {
        "description": "Multiply two numbers. ضرب رقمين",
        "examples": ["multiply", "times", "product", "5 * 3", "اضرب", "ضرب", "حاصل ضرب", "×"],
        "category": "calculator",
    },
    "calculator.compute": {
        "description": "Evaluate a mathematical expression. حساب تعبير رياضي",
        "examples": ["calculate", "compute", "eval", "math", "احسب", "ما نتيجة", "حساب", "رياضيات", "evaluate"],
        "category": "calculator",
    },
    "http.get": {
        "description": "Make HTTP GET request. طلب HTTP GET",
        "examples": ["get url", "fetch", "http get", "request", "اجلب", "GET", "جلب من", "طلب"],
        "category": "http",
    },
    "http.post": {
        "description": "Make HTTP POST request. إرسال طلب POST",
        "examples": ["post to", "send data", "http post", "أرسل", "POST", "إرسال", "send request"],
        "category": "http",
    },
    "process.run": {
        "description": "Run a system command. تشغيل أمر نظام",
        "examples": ["run command", "execute", "shell", "terminal", "شغّل", "نفّذ", "تشغيل", "bash"],
        "category": "process",
    },
    "noop": {
        "description": "No operation - for greetings, chat, or blocked requests. لا عملية - للتحيات والدردشة",
        "examples": ["hello", "thanks", "chat", "blocked", "مرحبا", "شكرا", "كيف حالك", "أهلا", "hi", "hey", "السلام"],
        "category": "control",
    },
    "finish": {
        "description": "Complete the task and return result. إنهاء المهمة وإرجاع النتيجة",
        "examples": ["done", "finish", "complete", "end task", "انتهى", "تم", "خلاص", "أنهي", "انتهيت", "مهمة منتهية"],
        "category": "control",
    },
}


class SemanticToolRanker:
    """
    Ranks tools by semantic similarity to user query.
    
    Uses ChromaDB for fast vector similarity search.
    ONLY returns tools from the predefined registry.
    """
    
    def __init__(self, persist_dir: Optional[str] = None):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB required. pip install chromadb")
        
        # Initialize ChromaDB
        if persist_dir:
            self.client = chromadb.PersistentClient(path=persist_dir)
        else:
            self.client = chromadb.Client()
        
        # Use default embedding (all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Create collection
        self.collection = self.client.get_or_create_collection(
            name="noogh_tools_v2",
            embedding_function=self.embedding_fn,
            metadata={"description": "NOOGH 13-tool registry for semantic matching"}
        )
        
        # Index tools
        self._index_tools()
        
        logger.info("SemanticToolRanker initialized with 13 tools")
    
    def _index_tools(self):
        """Index all tools from registry."""
        documents = []
        metadatas = []
        ids = []
        
        for tool_name, info in TOOL_REGISTRY.items():
            # Create searchable document
            doc = f"""
            Tool: {tool_name}
            Category: {info['category']}
            Description: {info['description']}
            Examples: {', '.join(info['examples'])}
            """
            
            documents.append(doc)
            metadatas.append({
                "tool_name": tool_name,
                "category": info["category"],
            })
            ids.append(tool_name)
        
        # Upsert (idempotent)
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
    
    def rank_tools(
        self, 
        query: str, 
        top_k: int = 3,
        min_score: float = 0.2,
    ) -> List[str]:
        """
        Rank tools by semantic similarity to query.
        
        Args:
            query: User's natural language query
            top_k: Maximum number of tools to return
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of tool names (from registry only)
        """
        if not query.strip():
            return list(TOOL_REGISTRY.keys())[:top_k]
        
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, len(TOOL_REGISTRY)),
            include=["metadatas", "distances"],
        )
        
        ranked = []
        for i, (tool_id, distance) in enumerate(zip(
            results["ids"][0],
            results["distances"][0],
        )):
            # Convert L2 distance to similarity (lower = better)
            similarity = 1 / (1 + distance)
            
            if similarity >= min_score:
                # Verify tool is in registry (safety check)
                if tool_id in TOOL_REGISTRY:
                    ranked.append(tool_id)
        
        # Always include noop as fallback
        if "noop" not in ranked and len(ranked) < top_k:
            ranked.append("noop")
        
        return ranked[:top_k]
    
    def get_all_tools(self) -> List[str]:
        """Get all tools in registry."""
        return list(TOOL_REGISTRY.keys())
    
    def is_valid_tool(self, tool_name: str) -> bool:
        """Check if tool exists in registry."""
        return tool_name in TOOL_REGISTRY


class SemanticRankerFallback:
    """Fallback ranker when ChromaDB unavailable - returns all tools."""
    
    def rank_tools(self, query: str, top_k: int = 3, min_score: float = 0.2) -> List[str]:
        """Return top tools based on simple keyword matching."""
        query_lower = query.lower()
        
        # Simple keyword matching
        matches = []
        
        keywords = {
            "filesystem.write": ["write", "save", "create", "اكتب", "احفظ"],
            "filesystem.read": ["read", "show", "open", "اقرأ", "اعرض"],
            "filesystem.list": ["list", "dir", "ls", "الملفات"],
            "filesystem.exists": ["exist", "check", "موجود"],
            "filesystem.delete": ["delete", "remove", "احذف"],
            "calculator.add": ["add", "plus", "+", "اجمع", "زائد"],
            "calculator.multiply": ["multiply", "times", "*", "اضرب"],
            "calculator.compute": ["calculate", "compute", "احسب", "نتيجة"],
            "http.get": ["get", "fetch", "http", "اجلب"],
            "http.post": ["post", "send", "أرسل"],
            "finish": ["done", "finish", "complete", "تم", "انتهى"],
            "noop": ["hello", "hi", "thanks", "مرحبا", "شكرا"],
        }
        
        for tool, kws in keywords.items():
            for kw in kws:
                if kw in query_lower:
                    matches.append(tool)
                    break
        
        # Always include noop
        if not matches:
            matches = ["noop", "calculator.compute", "filesystem.read"]
        elif "noop" not in matches:
            matches.append("noop")
        
        return matches[:top_k]
    
    def get_all_tools(self) -> List[str]:
        return list(TOOL_REGISTRY.keys())
    
    def is_valid_tool(self, tool_name: str) -> bool:
        return tool_name in TOOL_REGISTRY


def get_ranker(persist: bool = False) -> SemanticToolRanker:
    """Get the appropriate ranker (ChromaDB or fallback)."""
    if CHROMADB_AVAILABLE:
        persist_dir = None
        if persist:
            persist_dir = str(Path(__file__).parent.parent / ".data" / "chroma_ranker")
        return SemanticToolRanker(persist_dir=persist_dir)
    else:
        logger.warning("ChromaDB unavailable, using fallback ranker")
        return SemanticRankerFallback()


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Semantic Tool Ranker")
    print("=" * 60)
    
    ranker = get_ranker()
    
    test_queries = [
        ("اكتب hello في ملف", ["filesystem.write"]),
        ("اقرأ الملف /tmp/test.txt", ["filesystem.read"]),
        ("احسب 5 + 3", ["calculator.add", "calculator.compute"]),
        ("مرحبا كيف حالك", ["noop"]),
        ("خلاص انتهيت", ["finish"]),
        ("اجلب health من localhost", ["http.get"]),
        ("اعرض الملفات في المجلد", ["filesystem.list"]),
        ("هل الملف موجود", ["filesystem.exists"]),
    ]
    
    correct = 0
    for query, expected in test_queries:
        ranked = ranker.rank_tools(query, top_k=3)
        hit = any(e in ranked for e in expected)
        status = "✅" if hit else "❌"
        if hit:
            correct += 1
        print(f"{status} '{query[:30]}...' → {ranked} (expected: {expected})")
    
    print(f"\nAccuracy: {correct}/{len(test_queries)} ({100*correct/len(test_queries):.0f}%)")
