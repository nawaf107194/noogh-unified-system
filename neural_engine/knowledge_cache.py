"""
NOOGH Knowledge Cache
=====================
Simple in-memory cache for training data knowledge.
Used to augment model responses with relevant information.
"""

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class KnowledgeCache:
    """In-memory cache of training data for quick retrieval."""
    
    # Categories that are most useful for knowledge
    PRIORITY_CATEGORIES = [
        "python_code",
        "arabic_instruction", 
        "function_calling",
        "linux_admin",
        "math_reasoning",
        "api_design",
        "general"
    ]
    
    def __init__(self, data_dir: str = "/home/noogh/projects/noogh_unified_system/src/training_data"):
        self.data_dir = Path(data_dir)
        self.knowledge: Dict[str, List[Dict]] = {cat: [] for cat in self.PRIORITY_CATEGORIES}
        self.loaded = False
        self.total_samples = 0
    
    def load_dataset(self, max_per_category: int = 100):
        """Load knowledge from the ultimate dataset."""
        dataset_path = self.data_dir / "NOOGH_ULTIMATE_DATASET.jsonl"
        
        if not dataset_path.exists():
            logger.warning(f"Dataset not found: {dataset_path}")
            return
        
        logger.info(f"📚 Loading knowledge from {dataset_path}...")
        
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        sample = json.loads(line)
                        category = sample.get("category", "general")
                        
                        # Only load priority categories
                        if category in self.PRIORITY_CATEGORIES:
                            if len(self.knowledge[category]) < max_per_category:
                                self.knowledge[category].append({
                                    "instruction": sample.get("instruction", ""),
                                    "input": sample.get("input", ""),
                                    "output": sample.get("output", "")[:500]  # Limit output
                                })
                                self.total_samples += 1
                    except:
                        continue
            
            self.loaded = True
            logger.info(f"✅ Loaded {self.total_samples} knowledge samples")
            
            # Log breakdown
            for cat, samples in self.knowledge.items():
                if samples:
                    logger.debug(f"   - {cat}: {len(samples)} samples")
                    
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
    
    def search(self, query: str, n: int = 3) -> List[Dict]:
        """
        Search for relevant knowledge using enhanced keyword matching.
        Returns top N relevant samples.
        """
        if not self.loaded:
            self.load_dataset()
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Stop words to ignore (common but not meaningful)
        stop_words = {"you", "are", "a", "the", "is", "to", "in", "for", "with", "and", "or",
                      "كيف", "هل", "ما", "من", "في", "على", "أن", "هذا", "هذه", "التي", "الذي"}
        meaningful_words = query_words - stop_words
        
        # Synonym mappings for technical terms
        synonyms = {
            "حرارة": ["temperature", "temp", "monitor", "gpu", "cpu", "nvidia-smi", "sensors"],
            "gpu": ["gpu", "nvidia", "cuda", "graphics", "nvidia-smi"],
            "cpu": ["cpu", "processor", "cores", "load"],
            "لينكس": ["linux", "ubuntu", "bash", "shell", "terminal"],
            "بايثون": ["python", "py", "script"],
            "python": ["python", "py", "script", "import"],
            "مساحة": ["disk", "df", "storage", "space"],
            "قرص": ["disk", "df", "drive", "storage"],
            "شبكة": ["network", "neural", "net", "socket"],
            "neural": ["neural", "network", "nn", "deep", "learning"],
            "ذاكرة": ["memory", "ram", "free", "top"],
            "عمليات": ["process", "ps", "top", "htop"],
            "api": ["api", "rest", "endpoint", "flask", "fastapi"],
            "خادم": ["server", "http", "flask", "uvicorn"],
        }
        
        # Expand query with synonyms
        expanded_words = set(meaningful_words)
        for word in list(meaningful_words):
            word_lower = word.lower()
            if word_lower in synonyms:
                expanded_words.update(synonyms[word_lower])
            for key, values in synonyms.items():
                if word_lower in values or key in word_lower:
                    expanded_words.update(values)
        
        # Determine if this is a technical/code query
        tech_indicators = {"python", "كود", "code", "script", "api", "linux", "command", 
                          "أمر", "gpu", "cpu", "حرارة", "temperature", "neural", "شبكة"}
        is_technical = bool(expanded_words & tech_indicators)
        
        results = []
        
        # Priority categories for technical queries
        priority_categories = ["python_code", "linux_admin"] if is_technical else []
        
        for category, samples in self.knowledge.items():
            for sample in samples:
                instruction = sample['instruction']
                
                # Skip samples that are just system prompts
                if instruction.strip().startswith("SYSTEM:") or instruction.strip().startswith("# "):
                    continue
                
                # Calculate relevance score
                text = f"{instruction} {sample['input']}".lower()
                text_words = set(text.split())
                
                # Count matching meaningful words
                matches = len(expanded_words & text_words)
                
                # Bonus for priority categories (technical queries)
                if category in priority_categories:
                    matches += 3
                
                # Bonus for exact phrase match
                for word in meaningful_words:
                    if len(word) > 3 and word in text:
                        matches += 2
                
                # Minimum threshold - INCREASED from 2 to 4 for better accuracy
                if matches >= 4:
                    results.append({
                        "category": category,
                        "instruction": instruction,
                        "input": sample["input"],
                        "output": sample["output"],
                        "relevance": matches
                    })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:n]
    
    def get_category_samples(self, category: str, n: int = 5) -> List[Dict]:
        """Get random samples from a category."""
        if not self.loaded:
            self.load_dataset()
        
        if category in self.knowledge and self.knowledge[category]:
            return random.sample(self.knowledge[category], min(n, len(self.knowledge[category])))
        return []
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "loaded": self.loaded,
            "total_samples": self.total_samples,
            "categories": {cat: len(samples) for cat, samples in self.knowledge.items()}
        }


# ========== Global Instance ==========

_cache: Optional[KnowledgeCache] = None

def get_knowledge_cache() -> KnowledgeCache:
    """Get or create global knowledge cache."""
    global _cache
    if _cache is None:
        _cache = KnowledgeCache()
        _cache.load_dataset()  # Pre-load
    return _cache


def search_knowledge(query: str, n: int = 3) -> List[Dict]:
    """Quick search for relevant knowledge."""
    cache = get_knowledge_cache()
    return cache.search(query, n)


def get_relevant_context(query: str) -> str:
    """
    Get relevant context strings for a query.
    Used to augment the prompt with knowledge.
    """
    results = search_knowledge(query, n=2)
    
    if not results:
        return ""
    
    context_parts = ["📚 **معرفة متاحة:**"]
    for i, r in enumerate(results, 1):
        context_parts.append(f"\n**{i}. {r['category']}:**")
        context_parts.append(f"Q: {r['instruction'][:100]}...")
        context_parts.append(f"A: {r['output'][:200]}...")
    
    return "\n".join(context_parts)


if __name__ == "__main__":
    # Test the cache
    cache = KnowledgeCache()
    cache.load_dataset()
    
    print(f"Stats: {cache.get_stats()}")
    
    # Test search
    results = cache.search("python neural network")
    print(f"\nSearch results for 'python neural network':")
    for r in results:
        print(f"  - [{r['category']}] {r['instruction'][:50]}...")
