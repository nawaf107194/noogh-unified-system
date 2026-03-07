"""
NOOGH Proposal Memory & Rejection Learning
============================================
Tier-9: Learning from rejected proposals WITHOUT self-modification.

The system:
1. Remembers ALL proposals (approved, rejected, pending)
2. Analyzes WHY proposals were rejected
3. Learns patterns to improve future proposals
4. NEVER modifies itself based on learning

Philosophy:
- Memory enables learning
- Learning improves proposals
- Improved proposals need human approval
- The loop is OPEN (human in the middle)

Key Insight:
- This is NOT reinforcement learning
- This is PATTERN RECOGNITION from feedback
- The patterns inform suggestions, not actions
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class ProposalOutcome:
    """Record of a proposal and its outcome."""
    proposal_id: str
    filepath: str
    category: str
    issue_type: str
    description: str
    proposed_at: str
    
    # Outcome
    status: str  # "pending", "approved", "rejected", "expired"
    decided_at: Optional[str] = None
    decided_by: Optional[str] = None
    
    # Rejection details
    rejection_reason: Optional[str] = None
    rejection_category: Optional[str] = None  # "too_risky", "unnecessary", "wrong_approach", "bad_timing", etc.
    
    # Learning extracted
    lesson_learned: Optional[str] = None


@dataclass
class RejectionPattern:
    """A pattern learned from rejections."""
    pattern_id: str
    pattern_type: str  # "file_pattern", "issue_pattern", "category_pattern", "content_pattern"
    description: str
    occurrences: int
    examples: List[str]
    recommendation: str
    confidence: float  # 0-1


class ProposalMemory:
    """
    🧠 Proposal Memory
    
    Stores all proposals and their outcomes for learning.
    Persists to disk for cross-session memory.
    """
    
    def __init__(self, memory_path: Optional[str] = None):
        self.memory_path = Path(memory_path or "/home/noogh/projects/noogh_unified_system/src/.proposal_memory")
        self.memory_path.mkdir(parents=True, exist_ok=True)
        
        self.outcomes: Dict[str, ProposalOutcome] = {}
        self.patterns: Dict[str, RejectionPattern] = {}
        
        self._load_memory()
        logger.info(f"🧠 Proposal Memory initialized: {len(self.outcomes)} outcomes, {len(self.patterns)} patterns")
    
    def _load_memory(self):
        """Load memory from disk."""
        outcomes_file = self.memory_path / "outcomes.json"
        patterns_file = self.memory_path / "patterns.json"
        
        if outcomes_file.exists():
            try:
                with open(outcomes_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        outcome = ProposalOutcome(**item)
                        self.outcomes[outcome.proposal_id] = outcome
            except Exception as e:
                logger.warning(f"Could not load outcomes: {e}")
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        pattern = RejectionPattern(**item)
                        self.patterns[pattern.pattern_id] = pattern
            except Exception as e:
                logger.warning(f"Could not load patterns: {e}")
    
    def _save_memory(self):
        """Persist memory to disk."""
        outcomes_file = self.memory_path / "outcomes.json"
        patterns_file = self.memory_path / "patterns.json"
        
        with open(outcomes_file, 'w') as f:
            json.dump([asdict(o) for o in self.outcomes.values()], f, ensure_ascii=False, indent=2)
        
        with open(patterns_file, 'w') as f:
            json.dump([asdict(p) for p in self.patterns.values()], f, ensure_ascii=False, indent=2)
    
    def record_proposal(self, proposal_id: str, filepath: str, category: str,
                        issue_type: str, description: str) -> ProposalOutcome:
        """Record a new proposal."""
        outcome = ProposalOutcome(
            proposal_id=proposal_id,
            filepath=filepath,
            category=category,
            issue_type=issue_type,
            description=description,
            proposed_at=datetime.now().isoformat(),
            status="pending"
        )
        self.outcomes[proposal_id] = outcome
        self._save_memory()
        return outcome
    
    def record_decision(self, proposal_id: str, approved: bool, 
                        decided_by: str = "user",
                        rejection_reason: Optional[str] = None,
                        rejection_category: Optional[str] = None) -> Optional[ProposalOutcome]:
        """Record the decision on a proposal."""
        if proposal_id not in self.outcomes:
            return None
        
        outcome = self.outcomes[proposal_id]
        outcome.status = "approved" if approved else "rejected"
        outcome.decided_at = datetime.now().isoformat()
        outcome.decided_by = decided_by
        
        if not approved:
            outcome.rejection_reason = rejection_reason
            outcome.rejection_category = rejection_category
            
            # Extract lesson
            outcome.lesson_learned = self._extract_lesson(outcome)
            
            # Update patterns
            self._update_patterns(outcome)
        
        self._save_memory()
        return outcome
    
    def _extract_lesson(self, outcome: ProposalOutcome) -> str:
        """Extract a lesson from a rejection."""
        category = outcome.rejection_category or "unknown"
        
        lessons = {
            "too_risky": f"تجنب اقتراح تغييرات على {outcome.category} بهذا المستوى من المخاطرة",
            "unnecessary": f"التغيير على {outcome.issue_type} قد لا يكون ضرورياً دائماً",
            "wrong_approach": f"هناك طريقة أفضل لمعالجة {outcome.issue_type}",
            "bad_timing": "التوقيت غير مناسب لهذا النوع من التغييرات",
            "scope_too_large": "تقسيم التغييرات الكبيرة إلى أجزاء أصغر",
            "breaks_compatibility": "التأكد من التوافق مع الكود الموجود",
        }
        
        return lessons.get(category, f"رُفض: {outcome.rejection_reason or 'سبب غير محدد'}")
    
    def _update_patterns(self, outcome: ProposalOutcome):
        """Update rejection patterns based on new rejection."""
        # Pattern by category
        cat_pattern_id = f"cat_{outcome.category}"
        if cat_pattern_id in self.patterns:
            self.patterns[cat_pattern_id].occurrences += 1
            if outcome.proposal_id not in self.patterns[cat_pattern_id].examples:
                self.patterns[cat_pattern_id].examples.append(outcome.proposal_id)
        else:
            self.patterns[cat_pattern_id] = RejectionPattern(
                pattern_id=cat_pattern_id,
                pattern_type="category_pattern",
                description=f"الرفض المتكرر لـ {outcome.category}",
                occurrences=1,
                examples=[outcome.proposal_id],
                recommendation=f"كن أكثر حذراً مع ملفات {outcome.category}",
                confidence=0.5
            )
        
        # Pattern by issue type
        issue_pattern_id = f"issue_{outcome.issue_type}"
        if issue_pattern_id in self.patterns:
            self.patterns[issue_pattern_id].occurrences += 1
        else:
            self.patterns[issue_pattern_id] = RejectionPattern(
                pattern_id=issue_pattern_id,
                pattern_type="issue_pattern",
                description=f"الرفض المتكرر لـ {outcome.issue_type}",
                occurrences=1,
                examples=[outcome.proposal_id],
                recommendation=f"إعادة تقييم أسلوب معالجة {outcome.issue_type}",
                confidence=0.5
            )
        
        # Update confidence based on occurrences
        for p in self.patterns.values():
            p.confidence = min(0.95, 0.5 + (p.occurrences * 0.1))
        
        self._save_memory()
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        statuses = Counter(o.status for o in self.outcomes.values())
        categories = Counter(o.category for o in self.outcomes.values())
        rejection_reasons = Counter(
            o.rejection_category for o in self.outcomes.values() 
            if o.status == "rejected" and o.rejection_category
        )
        
        return {
            "total_proposals": len(self.outcomes),
            "by_status": dict(statuses),
            "by_category": dict(categories),
            "rejection_reasons": dict(rejection_reasons),
            "patterns_learned": len(self.patterns),
            "high_confidence_patterns": len([p for p in self.patterns.values() if p.confidence >= 0.7]),
        }


class RejectionLearner:
    """
    📚 Rejection Learner
    
    Learns from rejection patterns to improve future proposals.
    Does NOT modify any code - only influences suggestions.
    """
    
    def __init__(self, memory: ProposalMemory):
        self.memory = memory
        logger.info("📚 Rejection Learner initialized")
    
    def should_propose(self, filepath: str, category: str, issue_type: str) -> Tuple[bool, str, float]:
        """
        Check if a proposal should be made based on past learnings.
        
        Returns:
            (should_propose, reason, confidence)
        """
        warnings = []
        confidence_reduction = 0.0
        
        # Check category patterns
        cat_pattern = self.memory.patterns.get(f"cat_{category}")
        if cat_pattern and cat_pattern.occurrences >= 3:
            warnings.append(f"⚠️ تاريخ رفض عالٍ لـ {category} ({cat_pattern.occurrences} رفض)")
            confidence_reduction += cat_pattern.confidence * 0.3
        
        # Check issue patterns
        issue_pattern = self.memory.patterns.get(f"issue_{issue_type}")
        if issue_pattern and issue_pattern.occurrences >= 2:
            warnings.append(f"⚠️ {issue_type} غالباً يُرفض ({issue_pattern.occurrences} مرة)")
            confidence_reduction += issue_pattern.confidence * 0.2
        
        # Calculate final confidence
        base_confidence = 0.8
        final_confidence = max(0.1, base_confidence - confidence_reduction)
        
        # Decision
        if final_confidence < 0.3:
            return False, f"⛔ تاريخ الرفض يقترح عدم الاقتراح: {'; '.join(warnings)}", final_confidence
        elif warnings:
            return True, f"⚠️ يُقترح مع تحفظ: {'; '.join(warnings)}", final_confidence
        else:
            return True, "✅ لا يوجد تاريخ رفض مقلق", final_confidence
    
    def get_recommendations(self, category: str) -> List[str]:
        """Get recommendations based on past learnings."""
        recommendations = []
        
        for pattern in self.memory.patterns.values():
            if pattern.confidence >= 0.6:
                recommendations.append(pattern.recommendation)
        
        # Category-specific recommendations
        cat_pattern = self.memory.patterns.get(f"cat_{category}")
        if cat_pattern:
            recommendations.insert(0, cat_pattern.recommendation)
        
        return recommendations[:5]  # Top 5
    
    def get_lessons(self, limit: int = 10) -> List[Dict]:
        """Get recent lessons learned."""
        rejected = [o for o in self.memory.outcomes.values() if o.status == "rejected"]
        sorted_rejected = sorted(rejected, key=lambda o: o.decided_at or "", reverse=True)
        
        return [
            {
                "proposal_id": o.proposal_id,
                "category": o.category,
                "issue_type": o.issue_type,
                "rejection_reason": o.rejection_reason,
                "lesson": o.lesson_learned,
                "decided_at": o.decided_at,
            }
            for o in sorted_rejected[:limit]
        ]
    
    def analyze_rejection_trends(self) -> Dict:
        """Analyze rejection trends over time."""
        rejected = [o for o in self.memory.outcomes.values() if o.status == "rejected"]
        
        if not rejected:
            return {"message": "لا توجد رفوضات للتحليل"}
        
        # Group by rejection category
        by_reason = Counter(o.rejection_category for o in rejected if o.rejection_category)
        
        # Find most problematic categories
        by_file_category = Counter(o.category for o in rejected)
        
        # Find most problematic issue types
        by_issue = Counter(o.issue_type for o in rejected)
        
        return {
            "total_rejections": len(rejected),
            "top_rejection_reasons": dict(by_reason.most_common(5)),
            "problematic_categories": dict(by_file_category.most_common(5)),
            "problematic_issues": dict(by_issue.most_common(5)),
            "recommendations": self._generate_trend_recommendations(by_reason, by_file_category),
        }
    
    def _generate_trend_recommendations(self, by_reason: Counter, by_category: Counter) -> List[str]:
        """Generate recommendations based on trends."""
        recommendations = []
        
        if by_reason.get("too_risky", 0) >= 3:
            recommendations.append("💡 تقليل حجم التغييرات المقترحة")
        
        if by_reason.get("unnecessary", 0) >= 3:
            recommendations.append("💡 التركيز على التغييرات ذات الأثر الواضح")
        
        if by_reason.get("wrong_approach", 0) >= 2:
            recommendations.append("💡 طلب توضيح من المستخدم قبل الاقتراح")
        
        for cat, count in by_category.most_common(2):
            if count >= 3:
                recommendations.append(f"💡 تجنب الاقتراحات على ملفات {cat} مؤقتاً")
        
        return recommendations if recommendations else ["✅ لا توجد مشاكل متكررة واضحة"]


# ========== Integration with SelfImprover ==========

class EnhancedSelfImprover:
    """
    🧠 Enhanced Self-Improver with Memory & Learning
    
    Tier-9: Learns from rejections to improve future proposals.
    """
    
    def __init__(self):
        self.memory = ProposalMemory()
        self.learner = RejectionLearner(self.memory)
        
        # Import base improver
        from neural_engine.autonomy.self_improver import get_self_improver
        self.base_improver = get_self_improver()
        
        logger.info("🧠 Enhanced Self-Improver (Tier-9) initialized")
    
    def propose_with_learning(self, filepath: str, issue_type: str,
                               proposed_fix: str, description: str) -> Dict:
        """
        Propose improvement with learning-based recommendations.
        """
        # Get category
        category = self.base_improver.awareness.classify(filepath)
        cat_value = category.value if hasattr(category, 'value') else str(category)
        
        # Check past learnings
        should_propose, learning_reason, confidence = self.learner.should_propose(
            filepath, cat_value, issue_type
        )
        
        # Get recommendations
        recommendations = self.learner.get_recommendations(cat_value)
        
        if not should_propose:
            return {
                "proposed": False,
                "reason": learning_reason,
                "confidence": confidence,
                "recommendations": recommendations,
                "message": "⛔ تاريخ الرفض يقترح عدم تقديم هذا الاقتراح"
            }
        
        # Create proposal through base improver
        proposal = self.base_improver.propose_improvement(
            filepath, issue_type, proposed_fix, description
        )
        
        # Record in memory
        self.memory.record_proposal(
            proposal_id=proposal.id,
            filepath=filepath,
            category=cat_value,
            issue_type=issue_type,
            description=description
        )
        
        return {
            "proposed": True,
            "proposal_id": proposal.id,
            "blocked": proposal.blocked,
            "block_reason": proposal.block_reason,
            "learning_confidence": confidence,
            "learning_reason": learning_reason,
            "recommendations": recommendations,
            "message": "📝 تم إنشاء الاقتراح مع مراعاة التعلم السابق"
        }
    
    def record_user_decision(self, proposal_id: str, approved: bool,
                              rejection_reason: Optional[str] = None,
                              rejection_category: Optional[str] = None) -> Dict:
        """
        Record user's decision on a proposal.
        This is the LEARNING point.
        """
        outcome = self.memory.record_decision(
            proposal_id=proposal_id,
            approved=approved,
            decided_by="user",
            rejection_reason=rejection_reason,
            rejection_category=rejection_category
        )
        
        if outcome is None:
            return {"error": "Proposal not found"}
        
        if approved:
            return {
                "status": "approved",
                "message": "✅ تم تسجيل الموافقة",
                "proposal_id": proposal_id,
            }
        else:
            return {
                "status": "rejected",
                "message": "📚 تم تسجيل الرفض وتعلم الدرس",
                "proposal_id": proposal_id,
                "lesson_learned": outcome.lesson_learned,
                "patterns_updated": len(self.memory.patterns),
            }
    
    def get_learning_status(self) -> Dict:
        """Get current learning status."""
        stats = self.memory.get_stats()
        trends = self.learner.analyze_rejection_trends()
        lessons = self.learner.get_lessons(5)
        
        return {
            "memory_stats": stats,
            "rejection_trends": trends,
            "recent_lessons": lessons,
            "patterns": [
                {
                    "id": p.pattern_id,
                    "type": p.pattern_type,
                    "description": p.description,
                    "occurrences": p.occurrences,
                    "confidence": p.confidence,
                    "recommendation": p.recommendation,
                }
                for p in self.memory.patterns.values()
            ]
        }


# ========== Singleton ==========

_enhanced_improver: Optional[EnhancedSelfImprover] = None

def get_enhanced_improver() -> EnhancedSelfImprover:
    """Get the global enhanced improver instance."""
    global _enhanced_improver
    if _enhanced_improver is None:
        _enhanced_improver = EnhancedSelfImprover()
    return _enhanced_improver


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧠 Tier-9: Proposal Memory & Rejection Learning Test\n")
    
    enhancer = EnhancedSelfImprover()
    
    # Test 1: Propose with learning
    print("=" * 50)
    print("TEST 1: Propose with Learning")
    result = enhancer.propose_with_learning(
        filepath="scripts/test_script.py",
        issue_type="bare_except",
        proposed_fix="except Exception as e:",
        description="Fix bare except"
    )
    print(f"  Proposed: {result['proposed']}")
    print(f"  Confidence: {result.get('learning_confidence', 'N/A')}")
    
    # Test 2: Record rejection
    if result.get('proposal_id'):
        print("\n" + "=" * 50)
        print("TEST 2: Record Rejection")
        rejection = enhancer.record_user_decision(
            proposal_id=result['proposal_id'],
            approved=False,
            rejection_reason="Not necessary for this file",
            rejection_category="unnecessary"
        )
        print(f"  Lesson: {rejection.get('lesson_learned')}")
    
    # Test 3: Check learning status
    print("\n" + "=" * 50)
    print("TEST 3: Learning Status")
    status = enhancer.get_learning_status()
    print(f"  Total Proposals: {status['memory_stats']['total_proposals']}")
    print(f"  Patterns Learned: {status['memory_stats']['patterns_learned']}")
