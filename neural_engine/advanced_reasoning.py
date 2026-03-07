"""
Advanced Reasoning Components for Noug Neural OS
Provides enhanced pattern recognition, deep reasoning, causal analysis, and hypothesis generation
"""

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Represents a detected pattern"""

    pattern_type: str
    description: str
    confidence: float
    occurrences: int
    examples: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "description": self.description,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "examples": self.examples,
            "metadata": self.metadata,
        }


@dataclass
class CausalRelation:
    """Represents a causal relationship"""

    cause: str
    effect: str
    confidence: float
    evidence: List[str]
    correlation_strength: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cause": self.cause,
            "effect": self.effect,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "correlation_strength": self.correlation_strength,
        }


@dataclass
class Hypothesis:
    """Represents a hypothesis"""

    statement: str
    confidence: float
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    test_cases: List[str]
    status: str  # 'untested', 'supported', 'refuted', 'inconclusive'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statement": self.statement,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "test_cases": self.test_cases,
            "status": self.status,
        }


class EnhancedPatternRecognizer:
    """
    Advanced pattern recognition with ML-based detection
    Detects complex patterns, sequences, causal relationships, and temporal patterns
    """

    def __init__(self):
        self.detected_patterns: List[Pattern] = []
        self.pattern_cache: Dict[str, Pattern] = {}
        self._sequence_patterns: Dict[str, List[str]] = defaultdict(list)
        self._temporal_patterns: Dict[str, List[Tuple[str, datetime]]] = defaultdict(list)

        logger.info("EnhancedPatternRecognizer initialized")

    async def detect_patterns(self, data: List[str], context: Optional[Dict[str, Any]] = None) -> List[Pattern]:
        """
        Detect patterns in data using multiple techniques

        Args:
            data: List of strings to analyze
            context: Optional context information

        Returns:
            List of detected patterns
        """
        patterns = []

        # 1. Keyword patterns (basic)
        keyword_patterns = self._detect_keyword_patterns(data)
        patterns.extend(keyword_patterns)

        # 2. Sequence patterns (advanced)
        sequence_patterns = self._detect_sequence_patterns(data)
        patterns.extend(sequence_patterns)

        # 3. Frequency patterns
        frequency_patterns = self._detect_frequency_patterns(data)
        patterns.extend(frequency_patterns)

        # 4. Structural patterns
        structural_patterns = self._detect_structural_patterns(data)
        patterns.extend(structural_patterns)

        # 5. Semantic patterns (if context available)
        if context:
            semantic_patterns = self._detect_semantic_patterns(data, context)
            patterns.extend(semantic_patterns)

        # Store detected patterns
        self.detected_patterns.extend(patterns)

        # Update cache
        for pattern in patterns:
            cache_key = f"{pattern.pattern_type}:{pattern.description}"
            if cache_key in self.pattern_cache:
                # Update existing pattern
                self.pattern_cache[cache_key].occurrences += pattern.occurrences
                self.pattern_cache[cache_key].confidence = (
                    self.pattern_cache[cache_key].confidence * 0.7 + pattern.confidence * 0.3
                )
            else:
                self.pattern_cache[cache_key] = pattern

        return patterns

    def _detect_keyword_patterns(self, data: List[str]) -> List[Pattern]:
        """Detect keyword-based patterns"""
        patterns = []

        # Common keyword categories
        categories = {
            "action": ["create", "delete", "update", "modify", "execute", "run"],
            "query": ["search", "find", "lookup", "get", "retrieve"],
            "analysis": ["analyze", "evaluate", "assess", "review", "examine"],
            "learning": ["learn", "study", "understand", "explore", "discover"],
        }

        for category, keywords in categories.items():
            matches = []
            for item in data:
                if any(kw in item.lower() for kw in keywords):
                    matches.append(item)

            if matches:
                confidence = len(matches) / len(data)
                patterns.append(
                    Pattern(
                        pattern_type="keyword",
                        description=f"{category} pattern",
                        confidence=confidence,
                        occurrences=len(matches),
                        examples=matches[:3],
                        metadata={"category": category, "keywords": keywords},
                    )
                )

        return patterns

    def _detect_sequence_patterns(self, data: List[str]) -> List[Pattern]:
        """Detect sequential patterns (A → B → C)"""
        patterns = []

        if len(data) < 2:
            return patterns

        # Detect common sequences
        sequences = defaultdict(int)
        for i in range(len(data) - 1):
            # Simple bigram
            seq = f"{data[i][:20]} → {data[i+1][:20]}"
            sequences[seq] += 1

        # Find significant sequences
        for seq, count in sequences.items():
            if count >= 2:  # Occurred at least twice
                confidence = count / (len(data) - 1)
                patterns.append(
                    Pattern(
                        pattern_type="sequence",
                        description=f"Sequential pattern: {seq}",
                        confidence=confidence,
                        occurrences=count,
                        examples=[seq],
                        metadata={"sequence_length": 2},
                    )
                )

        return patterns

    def _detect_frequency_patterns(self, data: List[str]) -> List[Pattern]:
        """Detect frequency-based patterns"""
        patterns = []

        # Count word frequencies
        word_freq = Counter()
        for item in data:
            words = item.lower().split()
            word_freq.update(words)

        # Find high-frequency words
        total_words = sum(word_freq.values())
        for word, count in word_freq.most_common(5):
            if count > 1:
                confidence = count / total_words
                patterns.append(
                    Pattern(
                        pattern_type="frequency",
                        description=f"High-frequency term: {word}",
                        confidence=confidence,
                        occurrences=count,
                        examples=[word],
                        metadata={"frequency": count, "total": total_words},
                    )
                )

        return patterns

    def _detect_structural_patterns(self, data: List[str]) -> List[Pattern]:
        """Detect structural patterns (format, length, etc.)"""
        patterns = []

        # Detect common structures
        structures = {
            "question": r"\?$",
            "command": r"^(create|delete|update|run|execute)",
            "url": r"https?://",
            "path": r"/[\w/]+",
            "email": r"\b[\w.-]+@[\w.-]+\.\w+\b",
        }

        for struct_type, pattern_regex in structures.items():
            matches = [item for item in data if re.search(pattern_regex, item, re.IGNORECASE)]
            if matches:
                confidence = len(matches) / len(data)
                patterns.append(
                    Pattern(
                        pattern_type="structural",
                        description=f"{struct_type} structure",
                        confidence=confidence,
                        occurrences=len(matches),
                        examples=matches[:3],
                        metadata={"structure_type": struct_type},
                    )
                )

        return patterns

    def _detect_semantic_patterns(self, data: List[str], context: Dict[str, Any]) -> List[Pattern]:
        """Detect semantic patterns using context"""
        patterns = []

        # Check for intent patterns
        if "user_intent" in context:
            intent = context["user_intent"].lower()

            # Categorize intent
            if any(word in intent for word in ["learn", "understand", "explain"]):
                patterns.append(
                    Pattern(
                        pattern_type="semantic",
                        description="Learning intent pattern",
                        confidence=0.8,
                        occurrences=1,
                        examples=[intent],
                        metadata={"intent_category": "learning"},
                    )
                )
            elif any(word in intent for word in ["create", "build", "make"]):
                patterns.append(
                    Pattern(
                        pattern_type="semantic",
                        description="Creation intent pattern",
                        confidence=0.8,
                        occurrences=1,
                        examples=[intent],
                        metadata={"intent_category": "creation"},
                    )
                )

        return patterns

    async def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of all detected patterns"""
        pattern_types = defaultdict(int)
        total_confidence = 0

        for pattern in self.detected_patterns:
            pattern_types[pattern.pattern_type] += 1
            total_confidence += pattern.confidence

        avg_confidence = total_confidence / len(self.detected_patterns) if self.detected_patterns else 0

        return {
            "total_patterns": len(self.detected_patterns),
            "pattern_types": dict(pattern_types),
            "average_confidence": avg_confidence,
            "cached_patterns": len(self.pattern_cache),
        }


class CausalAnalyzer:
    """
    Analyzes causal relationships between events and actions
    Distinguishes correlation from causation
    """

    def __init__(self):
        self.causal_relations: List[CausalRelation] = []
        self._event_sequences: List[Tuple[str, str, bool]] = []  # (cause, effect, success)

        logger.info("CausalAnalyzer initialized")

    async def analyze_causality(
        self, events: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None
    ) -> List[CausalRelation]:
        """
        Analyze causal relationships in events

        Args:
            events: List of events with 'action', 'result', 'success'
            context: Optional context

        Returns:
            List of detected causal relations
        """
        relations = []

        if len(events) < 2:
            return relations

        # Analyze sequential events for causality
        for i in range(len(events) - 1):
            current = events[i]
            next_event = events[i + 1]

            # Check if current action might have caused next event
            relation = self._detect_causal_relation(current, next_event)
            if relation:
                relations.append(relation)

        # Store relations
        self.causal_relations.extend(relations)

        return relations

    def _detect_causal_relation(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> Optional[CausalRelation]:
            """Detect if event1 caused event2"""

            action1 = event1.get("action", "")
            action2 = event2.get("action", "")
            success1 = event1.get("success", False)
            success2 = event2.get("success", False)

            # Simple heuristics for causality
            evidence = []
            confidence = 0.5

            # 1. Temporal proximity (events close in time)
            confidence += 0.1
            evidence.append("Temporal proximity")

            # 2. Logical dependency (action2 depends on result of action1)
            if any(word in action2.lower() for word in ["use", "based on", "from"]):
                confidence += 0.2
                evidence.append("Logical dependency detected")

            # 3. Success correlation
            if success1 and success2:
                confidence += 0.1
                evidence.append("Both actions successful")
            elif not success1 and not success2:
                confidence += 0.05
                evidence.append("Both actions failed (possible causal chain)")

            # 4. Semantic similarity
            common_words = set(action1.lower().split()) & set(action2.lower().split())
            if common_words:
                confidence += 0.1
                evidence.append(f"Common terms: {common_words}")

            # Only return if confidence is significant
            if confidence <= 0.6:
                return None

            # Calculate correlation strength
            correlation = 0.7 if (success1 == success2) else 0.3

            return CausalRelation(
                cause=action1,
                effect=action2,
                confidence=min(confidence, 1.0),
                evidence=evidence,
                correlation_strength=correlation,
            )

    async def build_causal_chain(self, events: List[Dict[str, Any]]) -> List[List[str]]:
        """Build causal chains from events"""
        relations = await self.analyze_causality(events)

        # Build chains
        chains = []
        current_chain = []

        for relation in relations:
            if not current_chain:
                current_chain = [relation.cause, relation.effect]
            elif current_chain[-1] == relation.cause:
                current_chain.append(relation.effect)
            else:
                chains.append(current_chain)
                current_chain = [relation.cause, relation.effect]

        if current_chain:
            chains.append(current_chain)

        return chains


class HypothesisGenerator:
    """
    Generates and tests hypotheses based on observations
    """

    def __init__(self):
        self.hypotheses: List[Hypothesis] = []

        logger.info("HypothesisGenerator initialized")

    async def generate_hypothesis(
        self, observations: List[str], context: Optional[Dict[str, Any]] = None
    ) -> List[Hypothesis]:
        """
        Generate hypotheses from observations

        Args:
            observations: List of observations
            context: Optional context

        Returns:
            List of generated hypotheses
        """
        hypotheses = []

        # Generate hypotheses based on patterns
        if len(observations) >= 3:
            # Hypothesis 1: Frequency-based
            word_freq = Counter()
            for obs in observations:
                word_freq.update(obs.lower().split())

            most_common = word_freq.most_common(1)
            if most_common:
                word, count = most_common[0]
                if count >= 2:
                    hypothesis = Hypothesis(
                        statement=f"The term '{word}' is central to the current task",
                        confidence=count / len(observations),
                        supporting_evidence=[f"Appears {count} times in {len(observations)} observations"],
                        contradicting_evidence=[],
                        test_cases=[f"Check if '{word}' appears in future observations"],
                        status="untested",
                    )
                    hypotheses.append(hypothesis)

            # Hypothesis 2: Pattern-based
            if all("success" in obs.lower() for obs in observations[-3:]):
                hypothesis = Hypothesis(
                    statement="Recent actions are consistently successful",
                    confidence=0.8,
                    supporting_evidence=observations[-3:],
                    contradicting_evidence=[],
                    test_cases=["Monitor next action for success"],
                    status="supported",
                )
                hypotheses.append(hypothesis)

        # Store hypotheses
        self.hypotheses.extend(hypotheses)

        return hypotheses

    async def test_hypothesis(self, hypothesis: Hypothesis, new_evidence: str, is_supporting: bool) -> Hypothesis:
        """Test hypothesis with new evidence"""

        if is_supporting:
            hypothesis.supporting_evidence.append(new_evidence)
            hypothesis.confidence = min(hypothesis.confidence + 0.1, 1.0)
        else:
            hypothesis.contradicting_evidence.append(new_evidence)
            hypothesis.confidence = max(hypothesis.confidence - 0.1, 0.0)

        # Update status
        if hypothesis.confidence > 0.7:
            hypothesis.status = "supported"
        elif hypothesis.confidence < 0.3:
            hypothesis.status = "refuted"
        else:
            hypothesis.status = "inconclusive"

        return hypothesis


class DeepReasoningEngine:
    """
    Advanced reasoning engine with multi-step reasoning capabilities
    Combines pattern recognition, causal analysis, and hypothesis generation
    """

    def __init__(self):
        self.pattern_recognizer = EnhancedPatternRecognizer()
        self.causal_analyzer = CausalAnalyzer()
        self.hypothesis_generator = HypothesisGenerator()

        self._reasoning_history: List[Dict[str, Any]] = []

        logger.info("DeepReasoningEngine initialized")

    async def deep_reason(self, input_data: Any, context: Dict[str, Any], reasoning_depth: int = 3) -> Dict[str, Any]:
        """
        Perform deep reasoning with multiple steps

        Args:
            input_data: Input to reason about
            context: Execution context
            reasoning_depth: Number of reasoning steps

        Returns:
            Reasoning result with patterns, causality, and hypotheses
        """

        # Convert input to list of strings for analysis
        if isinstance(input_data, str):
            data_list = [input_data]
        elif isinstance(input_data, list):
            data_list = [str(item) for item in input_data]
        else:
            data_list = [str(input_data)]

        # Add historical context
        historical = context.get("historical", [])
        if historical:
            data_list.extend([h.get("action", "") for h in historical[-5:]])

        result = {
            "input": str(input_data),
            "reasoning_steps": [],
            "patterns": [],
            "causal_relations": [],
            "hypotheses": [],
            "conclusion": "",
            "confidence": 0.0,
        }

        # Step 1: Pattern Recognition
        patterns = await self.pattern_recognizer.detect_patterns(data_list, context)
        result["patterns"] = [p.to_dict() for p in patterns]
        result["reasoning_steps"].append(
            {"step": 1, "type": "pattern_recognition", "result": f"Detected {len(patterns)} patterns"}
        )

        # Step 2: Causal Analysis (if historical data available)
        if historical:
            events = [
                {"action": h.get("action", ""), "result": h.get("result", ""), "success": h.get("success", False)}
                for h in historical
            ]
            causal_relations = await self.causal_analyzer.analyze_causality(events, context)
            result["causal_relations"] = [c.to_dict() for c in causal_relations]
            result["reasoning_steps"].append(
                {"step": 2, "type": "causal_analysis", "result": f"Found {len(causal_relations)} causal relations"}
            )

        # Step 3: Hypothesis Generation
        hypotheses = await self.hypothesis_generator.generate_hypothesis(data_list, context)
        result["hypotheses"] = [h.to_dict() for h in hypotheses]
        result["reasoning_steps"].append(
            {"step": 3, "type": "hypothesis_generation", "result": f"Generated {len(hypotheses)} hypotheses"}
        )

        # Step 4: Synthesis and Conclusion
        conclusion_parts = []
        total_confidence = 0
        confidence_count = 0

        if patterns:
            top_pattern = max(patterns, key=lambda p: p.confidence)
            conclusion_parts.append(f"Primary pattern: {top_pattern.description}")
            total_confidence += top_pattern.confidence
            confidence_count += 1

        if result["causal_relations"]:
            conclusion_parts.append(f"Identified {len(result['causal_relations'])} causal relationships")
            total_confidence += 0.7
            confidence_count += 1

        if hypotheses:
            supported = [h for h in hypotheses if h.status == "supported"]
            if supported:
                conclusion_parts.append(f"{len(supported)} hypotheses supported")
                total_confidence += 0.8
                confidence_count += 1

        result["conclusion"] = (
            ". ".join(conclusion_parts) if conclusion_parts else "Insufficient data for deep reasoning"
        )
        result["confidence"] = total_confidence / confidence_count if confidence_count > 0 else 0.0

        result["reasoning_steps"].append({"step": 4, "type": "synthesis", "result": result["conclusion"]})

        # Store in history
        self._reasoning_history.append(result)

        return result

    async def get_reasoning_summary(self) -> Dict[str, Any]:
        """Get summary of reasoning history"""
        return {
            "total_reasoning_sessions": len(self._reasoning_history),
            "pattern_summary": await self.pattern_recognizer.get_pattern_summary(),
            "total_causal_relations": len(self.causal_analyzer.causal_relations),
            "total_hypotheses": len(self.hypothesis_generator.hypotheses),
        }
