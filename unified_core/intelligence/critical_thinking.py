"""
Critical Thinking Module - Evaluate Evidence, Detect Biases, Avoid Fallacies
Part of NOOGH Cognitive Enhancement (Phase 1 - Quick Win #2)

This module implements critical thinking to evaluate reasoning by:
1. Checking evidence quality
2. Detecting cognitive biases
3. Checking for logical fallacies
4. Generating alternative explanations
5. Evaluating assumptions
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger("unified_core.intelligence.critical_thinking")


@dataclass
class Evidence:
    """Represents a piece of evidence used in reasoning."""
    content: str
    source: str
    timestamp: str = None

    @property
    def age_days(self) -> int:
        if not self.timestamp:
            return 0
        try:
            ts = datetime.fromisoformat(self.timestamp)
            delta = datetime.now(timezone.utc) - ts
            return max(0, delta.days)
        except ValueError:
            return 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class CriticalThinker:
    """
    Evaluates reasoning by questioning assumptions, evaluating evidence, and detecting biases.
    """

    COGNITIVE_BIASES = [
        'confirmation_bias',      # Seeking confirming evidence
        'availability_bias',      # Overweight recent/memorable
        'anchoring_bias',         # Over-rely on first info
        'correlation_causation',  # Confuse correlation with cause
        'survivorship_bias',      # Only see successes
        'recency_bias'            # Overweight recent data
    ]

    LOGICAL_FALLACIES = [
        'hasty_generalization',   # Too small sample
        'false_dichotomy',        # Only two options assumed
        'slippery_slope',         # Chain reaction assumed
        'circular_reasoning',     # Premise = conclusion
        'post_hoc',               # After = because
    ]

    def _call_neural_engine_eval(self, claim: str, evidence_text: str, reasoning: str) -> List[str]:
        """Call Neural Engine to critically evaluate reasoning."""
        import asyncio
        from dotenv import load_dotenv
        import pathlib
        
        env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            
        from unified_core.neural_bridge import NeuralEngineClient
        
        async def _run():
            client = NeuralEngineClient()
            try:
                system = "أنت NOOGH، مفكر نقدي ومحلل مالي. تفحص الادعاءات والمغالطات بدقة وحزم. لا تجامل، كن مباشراً."
                prompt = (f"الادعاء الذي يتم تقييمه: {claim}\n\n"
                          f"الأدلة المتاحة: {evidence_text}\n\n"
                          f"المنطق المستخدم: {reasoning}\n\n"
                          "هل هناك أي مغالطات منطقية، أو انحيازات معرفية، أو ادعاءات غير مدعومة في هذا التفكير؟\n"
                          "قم بالرد في نقاط قصيرة ومباشرة تبدأ بـ '-' إذا كان هناك عيوب.\n"
                          "إذا كان المنطق سليماً تماماً ومبنياً على أدلة قاطعة، أجب بوضوح 'سليم ولا توجد مغالطات'.")
                          
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ]
                resp = await client.complete(messages, max_tokens=300)
                if resp.get('success'):
                    content = resp.get('content', '').strip()
                    if 'سليم ولا' in content or 'لا توجد مغالطات' in content:
                        return []
                    issues = [line.strip('- *') for line in content.split('\n') if line.strip() and len(line) > 5]
                    return issues
                return [f"فشل التحليل الإدراكي: {resp.get('error', 'Unknown Error')}"]
            except Exception as e:
                logger.error(f"Neural Eval failed: {e}")
                return [f"خطأ في التحليل: {str(e)}"]
            finally:
                await client.close()
                
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: asyncio.run(_run()))
                return future.result()
        else:
            return asyncio.run(_run())

    def evaluate_reasoning(self, claim: str, evidence: List[Evidence], reasoning: str) -> Dict[str, Any]:
        """Critically evaluate a reasoning chain using heuristic checks + Neural Engine Logic."""
        logger.info(f"Evaluating reasoning for claim: {claim[:50]}...")
        issues = []

        # 1. Check evidence quality (Heuristic Base)
        evidence_quality = self._evaluate_evidence(evidence)
        if evidence_quality['quality'] < 0.7:
            issues.append(f"Weak evidence: {evidence_quality['reason']}")

        # 2. Detect cognitive biases (Heuristic Base)
        biases = self._detect_biases(claim, evidence, reasoning)
        issues.extend(biases)

        # 3. Check for logical fallacies (Heuristic Base)
        fallacies = self._detect_fallacies(reasoning)
        issues.extend(fallacies)

        # 4. Neural Engine Cognitive Analysis
        evidence_text = " ".join([e.content for e in evidence]) if evidence else "لا توجد أدلة"
        neural_issues = self._call_neural_engine_eval(claim, evidence_text, reasoning)
        issues.extend(neural_issues)

        # 5. Alternative explanations
        alternatives = self._generate_alternatives(claim, evidence)

        # 6. Evaluate assumptions
        assumptions = self._identify_assumptions(reasoning)
        questionable = self._question_assumptions(assumptions)
        issues.extend(questionable)

        result = {
            'claim': claim,
            'valid': len(issues) == 0,
            'issues': issues,
            'alternatives': alternatives,
            'assumptions': assumptions,
            'confidence': self._calculate_confidence(evidence_quality, issues),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # EventBus + NeuronFabric integration
        if biases or fallacies:
            try:
                from unified_core.integration.event_bus import get_event_bus, EventPriority
                bus = get_event_bus()
                bus.publish_sync(
                    "bias_detected",
                    {
                        "claim": claim[:100],
                        "biases": biases,
                        "fallacies": fallacies,
                        "confidence": result['confidence'],
                    },
                    "CriticalThinker",
                    EventPriority.HIGH
                )
            except Exception:
                pass
            try:
                from unified_core.core.neuron_fabric import get_neuron_fabric, NeuronType
                fabric = get_neuron_fabric()
                for issue in (biases + fallacies)[:3]:
                    fabric.create_neuron(
                        proposition=f"WARNING: {issue[:80]}",
                        neuron_type=NeuronType.META,
                        confidence=0.3,
                        domain="intelligence",
                        tags=["bias_warning", "critical_thinking"],
                        metadata={"claim": claim[:80], "source": "CriticalThinker"}
                    )
            except Exception:
                pass
        
        return result

    def _evaluate_evidence(self, evidence: List[Evidence]) -> Dict[str, Any]:
        """Assess evidence quality."""
        if not evidence:
            return {
                'quality': 0.0,
                'checks': {'has_evidence': False},
                'reason': "No evidence provided"
            }

        checks = {
            'sample_size': len(evidence) >= 5, # Adjusted for realistic small sample agent tests
            'recency': all(e.age_days < 30 for e in evidence),
            'diversity': len(set(e.source for e in evidence)) >= 2,
            'consistency': self._check_consistency(evidence)
        }

        quality = sum(checks.values()) / len(checks)

        return {
            'quality': quality,
            'checks': checks,
            'reason': self._explain_quality(checks)
        }

    def _explain_quality(self, checks: Dict[str, bool]) -> str:
        """Explain the output of evidence evaluation."""
        failed = [k for k, v in checks.items() if not v]
        if not failed:
            return "Good quality evidence"
        return f"Failed checks: {', '.join(failed)}"

    def _check_consistency(self, evidence: List[Evidence]) -> bool:
        """Check if evidence pieces are mutually consistent."""
        # Simplified: assume consistent unless explicit "contradiction" word found
        texts = " ".join([e.content.lower() for e in evidence])
        return "contradict" not in texts and "oppose" not in texts

    def _detect_biases(self, claim: str, evidence: List[Evidence], reasoning: str) -> List[str]:
        """Detect cognitive biases."""
        detected = []

        if self._seeks_only_confirming(evidence, claim):
            detected.append("Confirmation bias: Only seeking supporting evidence")

        if self._overweights_recent(evidence):
            detected.append("Availability/Recency bias: Overweighting recent events")

        if self._confuses_correlation_causation(reasoning):
            detected.append("Correlation ≠ causation: Confusing association with cause")

        return detected

    def _seeks_only_confirming(self, evidence: List[Evidence], claim: str) -> bool:
        # Simplified heuristic
        return len(evidence) <= 1 or all("support" in e.content.lower() for e in evidence)

    def _overweights_recent(self, evidence: List[Evidence]) -> bool:
        return all(e.age_days < 1 for e in evidence) and len(evidence) > 0

    def _confuses_correlation_causation(self, reasoning: str) -> bool:
        reasoning_lower = reasoning.lower()
        return "caused" in reasoning_lower and ("because after" in reasoning_lower or "associated" in reasoning_lower)

    def _detect_fallacies(self, reasoning: str) -> List[str]:
        """Check for common logical fallacies."""
        fallacies = []
        reasoning_lower = reasoning.lower()
        if "all " in reasoning_lower and "always" in reasoning_lower:
            fallacies.append("Hasty generalization: Assuming a universal rule from limited cases")
        if "either" in reasoning_lower and "or" in reasoning_lower and "must" in reasoning_lower:
            fallacies.append("False dichotomy: Assumes only two possible options")
        return fallacies

    def _generate_alternatives(self, claim: str, evidence: List[Evidence]) -> List[str]:
        """Generate alternative explanations for same evidence."""
        alternatives = []

        if self._has_causal_claim(claim):
            alternatives.append(self._reverse_causation(claim))
        
        alternatives.append(self._common_cause_explanation(claim, evidence))
        alternatives.append(self._coincidence_explanation(claim, evidence))
        alternatives.append(self._measurement_artifact(evidence))

        return alternatives

    def _has_causal_claim(self, claim: str) -> bool:
        causal_words = ['cause', 'because', 'due to', 'leads to', 'improved', 'decreased', 'increased']
        return any(w in claim.lower() for w in causal_words)

    def _reverse_causation(self, claim: str) -> str:
        return "Reverse causation: The assumed effect actually caused the assumed cause"

    def _common_cause_explanation(self, claim: str, evidence: List[Evidence]) -> str:
        return "Common cause: A third unseen variable caused both phenomena"

    def _coincidence_explanation(self, claim: str, evidence: List[Evidence]) -> str:
        return "Coincidence: The events happen to occur together by random chance"

    def _measurement_artifact(self, evidence: List[Evidence]) -> str:
        return "Measurement artifact: The change is due to how/when we measured it, not a real effect"

    def _identify_assumptions(self, reasoning: str) -> List[str]:
        return ["Assumption: Environment conditions remained stable", "Assumption: Sample is representative"]

    def _question_assumptions(self, assumptions: List[str]) -> List[str]:
        issues = []
        for assump in assumptions:
            if "stable" in assump.lower():
                issues.append(f"Unverified assumption: {assump}")
        return issues

    def _calculate_confidence(self, evidence_quality: Dict[str, Any], issues: List[str]) -> float:
        base = evidence_quality['quality']
        penalty = len(issues) * 0.15
        return max(0.0, round(base - penalty, 2))


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    critic = CriticalThinker()

    claim = "Adding cache improved performance by 20%"
    evidence = [
        Evidence("Response time dropped from 100ms to 80ms today", "system_logs", datetime.now(timezone.utc).isoformat()),
        Evidence("CPU usage is lower today", "system_logs", datetime.now(timezone.utc).isoformat())
    ]
    reasoning = "Because after we deployed the cache, performance improved, it means the cache caused the improvement."

    print("=" * 70)
    print("CRITICAL THINKING ANALYSIS")
    print("=" * 70)
    
    evaluation = critic.evaluate_reasoning(claim, evidence, reasoning)
    
    print(f"Claim: {evaluation['claim']}")
    print(f"Valid: {evaluation['valid']}")
    print(f"Confidence: {evaluation['confidence']}")
    print("\nIssues found:")
    for issue in evaluation['issues']:
        print(f" ✗ {issue}")
    
    print("\nAlternative Explanations:")
    for alt in evaluation['alternatives']:
        print(f" 💡 {alt}")

    print("\nAssumptions:")
    for assump in evaluation['assumptions']:
        print(f" ? {assump}")
