"""
NOOGH Self-Learning System
===========================
Enables the AI to learn and evolve from conversations.

Learning Types:
1. Conversation Learning - Store successful Q&A pairs
2. Error Learning - Learn from mistakes and corrections
3. Preference Learning - Learn user preferences
4. Knowledge Expansion - Extract and store new knowledge
"""

import json
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationLearner:
    """Learn from successful conversations."""
    
    def __init__(self, data_dir: str = "/home/noogh/projects/noogh_unified_system/src/data/learning"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.conversations_file = self.data_dir / "learned_conversations.jsonl"
        self.preferences_file = self.data_dir / "user_preferences.json"
        self.knowledge_file = self.data_dir / "extracted_knowledge.jsonl"
        self.errors_file = self.data_dir / "learned_errors.jsonl"
        
        # Load preferences
        self.preferences = self._load_preferences()
        
        # Learning statistics
        self.stats = {
            "conversations_learned": 0,
            "errors_learned": 0,
            "knowledge_extracted": 0,
            "last_learning": None
        }
        
        logger.info("🧠 Self-Learning System initialized")
    
    def _load_preferences(self) -> Dict:
        """Load user preferences from file."""
        if self.preferences_file.exists():
            try:
                return json.loads(self.preferences_file.read_text())
            except:
                pass
        return {
            "language": "ar",
            "response_style": "detailed",
            "topics_of_interest": [],
            "corrections_history": []
        }
    
    def _save_preferences(self):
        """Save preferences to file."""
        self.preferences_file.write_text(json.dumps(self.preferences, ensure_ascii=False, indent=2))
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID."""
        return hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
    
    # ========== Conversation Learning ==========
    
    def learn_from_conversation(
        self,
        query: str,
        response: str,
        success: bool = True,
        user_feedback: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Learn from a successful conversation.
        Stores the Q&A pair for future reference.
        """
        if not success or len(response) < 20:
            return
        
        learning_entry = {
            "id": self._generate_id(query),
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response[:1000],  # Limit response size
            "success": success,
            "user_feedback": user_feedback,
            "metadata": metadata or {},
            "category": self._categorize_query(query)
        }
        
        # Append to file
        with open(self.conversations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(learning_entry, ensure_ascii=False) + "\n")
        
        self.stats["conversations_learned"] += 1
        self.stats["last_learning"] = datetime.now().isoformat()
        
        logger.info(f"📚 Learned conversation: {query[:50]}...")
    
    def _categorize_query(self, query: str) -> str:
        """Categorize query type."""
        q = query.lower()
        
        if any(kw in q for kw in ["gpu", "cpu", "نظام", "حالة", "system"]):
            return "system"
        elif any(kw in q for kw in ["قصة", "شعر", "حكمة", "اكتب"]):
            return "creative"
        elif any(kw in q for kw in ["+", "-", "*", "/", "×", "÷"]):
            return "math"
        elif any(kw in q for kw in ["من أنت", "اسمك", "نوقه"]):
            return "identity"
        elif any(kw in q for kw in ["فلسفة", "رأي", "تفسير"]):
            return "philosophy"
        else:
            return "general"
    
    # ========== Error Learning ==========
    
    def learn_from_error(
        self,
        query: str,
        failed_response: str,
        error_type: str,
        correction: Optional[str] = None
    ):
        """
        Learn from an error or failed response.
        Helps avoid similar mistakes in the future.
        """
        error_entry = {
            "id": self._generate_id(query),
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "failed_response": failed_response[:500],
            "error_type": error_type,
            "correction": correction,
            "learned": True
        }
        
        with open(self.errors_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + "\n")
        
        self.stats["errors_learned"] += 1
        logger.info(f"⚠️ Learned from error: {error_type}")
    
    # ========== Knowledge Extraction ==========
    
    def extract_knowledge(self, text: str, source: str = "conversation"):
        """
        Extract and store new knowledge from text.
        Looks for facts, definitions, and useful information.
        """
        # Simple knowledge extraction patterns
        knowledge_patterns = [
            # Definitions: "X هو Y"
            (r'(.+?) (هو|هي|يعني|تعني) (.+)', "definition"),
            # Facts: "أن X"
            (r'(أن|إن) (.+)', "fact"),
            # User info: "أنا X" or "اسمي X"
            (r'(أنا|اسمي|أسمي) (.+)', "user_info"),
        ]
        
        import re
        for pattern, ktype in knowledge_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    content = " ".join(match)
                else:
                    content = match
                
                if len(content) > 10:
                    knowledge_entry = {
                        "id": self._generate_id(content),
                        "timestamp": datetime.now().isoformat(),
                        "content": content[:500],
                        "type": ktype,
                        "source": source,
                        "verified": False
                    }
                    
                    with open(self.knowledge_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(knowledge_entry, ensure_ascii=False) + "\n")
                    
                    self.stats["knowledge_extracted"] += 1
    
    # ========== Preference Learning ==========
    
    def update_preference(self, key: str, value: Any):
        """Update a user preference."""
        self.preferences[key] = value
        self._save_preferences()
        logger.info(f"📝 Updated preference: {key} = {value}")
    
    def add_topic_of_interest(self, topic: str):
        """Add a topic of interest."""
        if topic not in self.preferences["topics_of_interest"]:
            self.preferences["topics_of_interest"].append(topic)
            self._save_preferences()
    
    def record_correction(self, original: str, corrected: str):
        """Record a user correction to learn from."""
        self.preferences["corrections_history"].append({
            "timestamp": datetime.now().isoformat(),
            "original": original[:200],
            "corrected": corrected[:200]
        })
        # Keep only last 100 corrections
        self.preferences["corrections_history"] = self.preferences["corrections_history"][-100:]
        self._save_preferences()
    
    # ========== Recall Learned Content ==========
    
    def recall_similar_conversations(self, query: str, n: int = 5) -> List[Dict]:
            """
            Recall similar past conversations.
            Simple keyword-based matching for now.
            """
            if not isinstance(query, str):
                raise TypeError("Query must be a string.")
            if not isinstance(n, int) or n <= 0:
                raise ValueError("The number of results must be a positive integer.")

            if not self.conversations_file.exists():
                logger.warning("Conversations file does not exist.")
                return []

            results = []
            query_words = set(query.lower().split())

            try:
                with open(self.conversations_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            stored_words = set(entry.get("query", "").lower().split())

                            # Calculate simple similarity
                            overlap = len(query_words & stored_words)
                            if overlap > 1:  # At least 2 words in common
                                entry["similarity"] = overlap / max(len(query_words), 1)
                                results.append(entry)
                        except Exception as e:
                            logger.error(f"Error processing line: {line}. Error: {e}")
                            continue
            except Exception as e:
                logger.error(f"Error reading from file: {self.conversations_file}. Error: {e}")

            # Sort by similarity
            results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            return results[:n]
    
    def get_learning_stats(self) -> Dict:
        """Get learning statistics."""
        return {
            **self.stats,
            "preferences": self.preferences,
            "files": {
                "conversations": self.conversations_file.exists() and self.conversations_file.stat().st_size or 0,
                "errors": self.errors_file.exists() and self.errors_file.stat().st_size or 0,
                "knowledge": self.knowledge_file.exists() and self.knowledge_file.stat().st_size or 0
            }
        }


# ========== Global Instance ==========

_learner: Optional[ConversationLearner] = None

def get_learner() -> ConversationLearner:
    """Get or create global learner instance."""
    global _learner
    if _learner is None:
        _learner = ConversationLearner()
    return _learner


# ========== Integration with ReAct Loop ==========

def learn_from_react_result(query: str, result: Any, success: bool = True):
    """
    Called after each ReAct loop to learn from the interaction.
    """
    learner = get_learner()
    
    # Extract response
    response = ""
    if hasattr(result, "answer"):
        response = result.answer
    elif isinstance(result, dict):
        response = result.get("answer", "")
    
    # Learn from successful conversations
    if success and len(response) > 20:
        learner.learn_from_conversation(
            query=query,
            response=response,
            success=True,
            metadata={
                "iterations": getattr(result, "iterations", 0),
                "tool_calls": len(getattr(result, "tool_calls", [])),
                "confidence": getattr(result, "confidence", 0.5)
            }
        )
        
        # Extract knowledge
        learner.extract_knowledge(query, source="user_query")
        learner.extract_knowledge(response, source="model_response")
    
    # Learn from errors
    elif not success:
        learner.learn_from_error(
            query=query,
            failed_response=response,
            error_type="failed_response"
        )


if __name__ == "__main__":
    # Test the learner
    learner = get_learner()
    
    # Test learning
    learner.learn_from_conversation(
        query="ما هي عاصمة السعودية",
        response="عاصمة المملكة العربية السعودية هي الرياض",
        success=True
    )
    
    print("Stats:", learner.get_learning_stats())
