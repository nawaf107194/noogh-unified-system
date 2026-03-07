"""
NOOGH File Auto-Classifier
===========================
Intelligent automatic classification of unknown files.

The system analyzes files based on:
- Filename patterns
- Directory location
- Import statements
- Code structure
- Function/class names

Philosophy:
- PROPOSE only, never auto-apply
- High confidence required
- Human confirmation for ambiguous cases
"""

import os
import re
import ast
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from collections import Counter

from neural_engine.autonomy.file_awareness import (
    FileAwareness, FileCategory, get_file_awareness
)

logger = logging.getLogger(__name__)


@dataclass
class ClassificationProposal:
    """A proposed classification for a file."""
    filepath: str
    current_category: FileCategory
    proposed_category: FileCategory
    confidence: float  # 0.0 - 1.0
    reasons: List[str]
    requires_review: bool
    

class FileAutoClassifier:
    """
    🧠 Intelligent File Auto-Classifier
    
    Analyzes unknown files and proposes classifications
    based on multiple signals with STRONG indicators.
    """
    
    # Keyword patterns for classification - IMPROVED
    CATEGORY_SIGNALS = {
        FileCategory.AUTHORITY: {
            # Strong: core system files
            "keywords": ["engine", "core", "main", "loop", "decision", "policy", 
                        "constitution", "registry", "executor", "processor", "manager"],
            "imports": ["fastapi", "asyncio", "neural_engine"],  # Removed weak ones
            "functions": ["run", "execute", "process", "handle", "start", "initialize"],
            "dir_patterns": ["reasoning", "autonomy", "core", "api", "engine"],
            "class_patterns": ["engine", "manager", "processor", "controller", "service"],
        },
        FileCategory.PATTERN: {
            # Strong: utility and script files
            "keywords": ["handler", "util", "helper", "wrapper", "adapter", "formatter", 
                        "bridge", "cli", "tool"],
            "imports": ["argparse", "click", "subprocess"],  # Executable indicators
            "functions": ["format", "convert", "parse", "build", "create", "main"],
            "dir_patterns": ["utils", "helpers", "handlers", "adapters", "scripts", 
                            "tools", "cli", "bin"],
            "special_patterns": ["if __name__", "argparse", "sys.argv"],
        },
        FileCategory.HISTORICAL: {
            # Strong: old/experimental files
            "keywords": ["old", "legacy", "deprecated", "backup", "v1", "v2", "v0",
                        "experiment", "draft", "poc", "prototype", "archive"],
            "imports": [],
            "functions": ["test_", "_test", "old_", "_old", "_deprecated"],
            "dir_patterns": ["old", "legacy", "deprecated", "experiments", "archive", 
                            "backup", "drafts", "poc"],
            "filename_patterns": ["_old", "_backup", "_v1", "_v2", "_legacy", "_deprecated"],
        },
        FileCategory.SENSITIVE: {
            # Strong: security files
            "keywords": ["auth", "security", "password", "token", "secret", 
                        "key", "credential", "encrypt", "decrypt", "jwt", "oauth"],
            "imports": ["cryptography", "hashlib", "secrets", "jwt", "bcrypt", "ssl"],
            "functions": ["verify", "authenticate", "authorize", "encrypt", "decrypt", 
                         "hash", "sign", "validate_token"],
            "dir_patterns": ["auth", "security", "crypto", "secrets"],
        },
        FileCategory.DATA: {
            # DATA should ONLY match data files, NOT training scripts
            "keywords": ["constants", "fixtures", "config", "settings", "defaults"],
            "imports": [],  # Don't match json/yaml imports - too weak
            "functions": [],
            "dir_patterns": ["config", "fixtures", "constants"],
            "file_extensions": [".json", ".jsonl", ".yaml", ".yml", ".csv", 
                               ".parquet", ".txt", ".xml"],  # Non-py files only
        },
    }
    
    # Special rules that override normal classification
    SPECIAL_RULES = [
        # Training scripts → PATTERN, not DATA
        {
            "name": "training_script",
            "condition": lambda s: ("train" in s["filename"] and 
                                   any("torch" in i or "transformers" in i for i in s["imports"])),
            "category": FileCategory.PATTERN,
            "reason": "سكربت تدريب (executable)",
            "confidence": 0.8,
        },
        # Start/run scripts → PATTERN
        {
            "name": "executable_script",
            "condition": lambda s: (any(kw in s["filename"] for kw in ["start", "run", "launch", "exec"]) or
                                   s.get("has_main_block", False)),
            "category": FileCategory.PATTERN,
            "reason": "سكربت قابل للتنفيذ",
            "confidence": 0.85,
        },
        # Test files → HISTORICAL
        {
            "name": "test_file",
            "condition": lambda s: (s["filename"].startswith("test_") or 
                                   s["filename"].endswith("_test") or
                                   "tests" in str(s.get("full_path", ""))),
            "category": FileCategory.HISTORICAL,
            "reason": "ملف اختبار",
            "confidence": 0.9,
        },
        # Security-related files → SENSITIVE
        {
            "name": "security_file",
            "condition": lambda s: any(kw in s["filename"] for kw in 
                                      ["auth", "security", "secret", "key", "token", "password"]),
            "category": FileCategory.SENSITIVE,
            "reason": "ملف متعلق بالأمان",
            "confidence": 0.9,
        },
    ]
    
    def __init__(self):
        self.awareness = get_file_awareness()
        self.base_path = Path("/home/noogh/projects/noogh_unified_system/src")
        logger.info("🔍 File Auto-Classifier v2 initialized")

    
    def analyze_file(self, filepath: str) -> ClassificationProposal:
        """
        Analyze a single file and propose a classification.
        
        Returns:
            ClassificationProposal with category, confidence, and reasons
        """
        current = self.awareness.classify(filepath)
        
        # Gather signals
        signals = self._gather_signals(filepath)
        
        # Check special rules FIRST (higher priority)
        for rule in self.SPECIAL_RULES:
            try:
                if rule["condition"](signals):
                    return ClassificationProposal(
                        filepath=filepath,
                        current_category=current,
                        proposed_category=rule["category"],
                        confidence=rule["confidence"],
                        reasons=[rule["reason"]],
                        requires_review=rule["confidence"] < 0.7
                    )
            except Exception:
                continue
        
        # Normal scoring if no special rule matched
        scores = {}
        reasons = {}
        
        for category, patterns in self.CATEGORY_SIGNALS.items():
            score, category_reasons = self._score_category(signals, patterns, category)
            scores[category] = score
            reasons[category] = category_reasons
        
        # Find best match
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        best_reasons = reasons[best_category]
        
        # Determine confidence
        if best_score >= 5:
            confidence = 0.9
        elif best_score >= 3:
            confidence = 0.7
        elif best_score >= 2:
            confidence = 0.5
        else:
            confidence = 0.3
            best_category = FileCategory.UNKNOWN
        
        return ClassificationProposal(
            filepath=filepath,
            current_category=current,
            proposed_category=best_category,
            confidence=confidence,
            reasons=best_reasons if best_reasons else ["لم يتم العثور على إشارات قوية"],
            requires_review=confidence < 0.7
        )
    
    def _gather_signals(self, filepath: str) -> Dict:
        """Gather all signals from a file."""
        signals = {
            "filename": "",
            "dirname": "",
            "full_path": "",
            "imports": [],
            "functions": [],
            "classes": [],
            "keywords_in_code": [],
            "has_main_block": False,
        }
        
        # Full path handling
        if not filepath.startswith('/'):
            full_path = self.base_path / filepath
        else:
            full_path = Path(filepath)
        
        signals["filename"] = full_path.stem.lower()
        signals["dirname"] = full_path.parent.name.lower()
        signals["full_path"] = str(full_path)
        
        # Parse Python file if exists
        if full_path.exists() and full_path.suffix == '.py':
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for main block (executable indicator)
                if 'if __name__' in content and '__main__' in content:
                    signals["has_main_block"] = True
                
                # Parse AST
                try:
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                signals["imports"].append(alias.name.lower())
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                signals["imports"].append(node.module.lower())
                        elif isinstance(node, ast.FunctionDef):
                            signals["functions"].append(node.name.lower())
                        elif isinstance(node, ast.ClassDef):
                            signals["classes"].append(node.name.lower())
                except SyntaxError:
                    pass
                
                # Extract keywords from content
                words = re.findall(r'\b[a-z_]+\b', content.lower())
                signals["keywords_in_code"] = list(set(words))
                
            except Exception as e:
                logger.debug(f"Error analyzing {filepath}: {e}")
        
        return signals
    
    def _score_category(self, signals: Dict, patterns: Dict, category: FileCategory) -> Tuple[int, List[str]]:
        """Score how well a file matches a category."""
        score = 0
        reasons = []
        
        # Check filename keywords
        for kw in patterns.get("keywords", []):
            if kw in signals["filename"]:
                score += 2
                reasons.append(f"اسم الملف يحتوي على '{kw}'")
        
        # Check directory patterns
        for dir_pat in patterns.get("dir_patterns", []):
            if dir_pat in signals["dirname"]:
                score += 2
                reasons.append(f"موجود في مجلد '{dir_pat}'")
        
        # Check imports
        for imp in patterns.get("imports", []):
            if any(imp in i for i in signals["imports"]):
                score += 1
                reasons.append(f"يستورد '{imp}'")
        
        # Check function patterns
        for func_pat in patterns.get("functions", []):
            matching = [f for f in signals["functions"] if func_pat in f]
            if matching:
                score += 1
                reasons.append(f"دوال مطابقة: {', '.join(matching[:3])}")
        
        return score, reasons
    
    def analyze_unknown_files(self, limit: int = 50) -> List[ClassificationProposal]:
        """
        Analyze all unknown files and propose classifications.
        
        Returns:
            List of ClassificationProposal
        """
        proposals = []
        
        # Get all Python files
        for root, dirs, files in os.walk(self.base_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for f in files:
                if not f.endswith('.py'):
                    continue
                
                filepath = os.path.join(root, f)
                rel_path = os.path.relpath(filepath, self.base_path)
                
                # Check if unknown
                current = self.awareness.classify(filepath)
                if current == FileCategory.UNKNOWN:
                    proposal = self.analyze_file(filepath)
                    proposals.append(proposal)
                    
                    if len(proposals) >= limit:
                        break
            
            if len(proposals) >= limit:
                break
        
        # Sort by confidence (highest first)
        proposals.sort(key=lambda p: p.confidence, reverse=True)
        
        return proposals
    
    def get_classification_report(self, limit: int = 50) -> Dict:
        """
        Generate a classification report for unknown files.
        
        Returns:
            Report with proposals, stats, and recommendations
        """
        proposals = self.analyze_unknown_files(limit)
        
        # Group by proposed category
        by_category = {}
        for p in proposals:
            cat = p.proposed_category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "file": p.filepath,
                "confidence": p.confidence,
                "reasons": p.reasons,
                "requires_review": p.requires_review
            })
        
        # Stats
        high_confidence = len([p for p in proposals if p.confidence >= 0.7])
        needs_review = len([p for p in proposals if p.requires_review])
        
        return {
            "total_analyzed": len(proposals),
            "high_confidence": high_confidence,
            "needs_review": needs_review,
            "by_category": by_category,
            "recommendations": [
                f"✅ {high_confidence} ملف يمكن تصنيفه بثقة عالية",
                f"⚠️ {needs_review} ملف يحتاج مراجعة يدوية",
            ]
        }
    
    def propose_single(self, filepath: str) -> Dict:
        """
        Propose classification for a single file.
        Returns dict suitable for API response.
        """
        proposal = self.analyze_file(filepath)
        
        return {
            "filepath": filepath,
            "current_category": proposal.current_category.value,
            "proposed_category": proposal.proposed_category.value,
            "confidence": proposal.confidence,
            "confidence_label": self._confidence_label(proposal.confidence),
            "reasons": proposal.reasons,
            "requires_review": proposal.requires_review,
            "status": "proposed" if proposal.proposed_category != FileCategory.UNKNOWN else "uncertain"
        }
    
    def _confidence_label(self, confidence: float) -> str:
        """Get human-readable confidence label."""
        if confidence >= 0.9:
            return "🟢 عالية جداً"
        elif confidence >= 0.7:
            return "🟡 عالية"
        elif confidence >= 0.5:
            return "🟠 متوسطة"
        else:
            return "🔴 منخفضة"


# ========== Singleton ==========

_auto_classifier: Optional[FileAutoClassifier] = None

def get_auto_classifier() -> FileAutoClassifier:
    """Get the global auto-classifier instance."""
    global _auto_classifier
    if _auto_classifier is None:
        _auto_classifier = FileAutoClassifier()
    return _auto_classifier


if __name__ == "__main__":
    # Test the auto-classifier
    logging.basicConfig(level=logging.INFO)
    
    classifier = FileAutoClassifier()
    
    print("🔍 Analyzing Unknown Files...\n")
    
    report = classifier.get_classification_report(limit=20)
    
    print(f"📊 Total Analyzed: {report['total_analyzed']}")
    print(f"✅ High Confidence: {report['high_confidence']}")
    print(f"⚠️ Needs Review: {report['needs_review']}")
    
    print("\n📁 By Category:")
    for cat, files in report['by_category'].items():
        print(f"\n  {cat.upper()} ({len(files)} files):")
        for f in files[:3]:
            print(f"    • {f['file']}")
            print(f"      Confidence: {f['confidence']:.0%}")
            print(f"      Reasons: {', '.join(f['reasons'][:2])}")
