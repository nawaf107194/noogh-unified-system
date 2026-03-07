"""
Explanation Generation Module
Part of NOOGH Cognitive Enhancement (Phase 1 - Quick Win #3)

This module implements explanation generation to communicate decisions clearly by:
1. Explaining reasoning chains
2. Explaining why alternatives were rejected
3. Summarizing confidence and risks
4. Tailoring explanations to different audiences
5. Self-explanation for metacognitive logs
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

logger = logging.getLogger("unified_core.intelligence.explainer")

@dataclass
class Alternative:
    name: str
    description: str
    rejection_reason: str

@dataclass
class Decision:
    trigger: str
    action: str
    reasoning_steps: List[str]
    selection_reason: str
    alternatives: List[Alternative] = field(default_factory=list)
    evidence_quality: float = 0.8
    strategy_success_rate: float = 0.85
    risk_score: int = 15
    confidence: float = 0.9
    risks: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


class Explainer:
    """Generate clear explanations for decisions and reasoning."""

    def explain_decision(self, decision: Decision, audience: str = 'technical') -> str:
        """Generate explanation tailored to audience."""
        
        explanation = {
            'summary': self._one_line_summary(decision),
            'reasoning': self._explain_reasoning(decision),
            'alternatives': self._explain_alternatives(decision),
            'trade_offs': self._explain_trade_offs(decision),
            'confidence': self._explain_confidence(decision),
            'risks': self._explain_risks(decision),
            'next_steps': self._explain_next_steps(decision)
        }

        # Tailor to audience
        if audience == 'technical':
            explanation['details'] = self._technical_details(decision)
        elif audience == 'executive':
            explanation = self._executive_summary(explanation)
        elif audience == 'user':
            explanation = self._simplify(explanation)

        return self._format(explanation, audience)

    def _one_line_summary(self, decision: Decision) -> str:
        return f"Decided to {decision.action} because {decision.selection_reason}."

    def _explain_reasoning(self, decision: Decision) -> str:
        """Explain the reasoning chain."""
        chain = []
        chain.append(f"Observed: {decision.trigger}")
        for step in decision.reasoning_steps:
            chain.append(f"Therefore: {step}")
        chain.append(f"Conclusion: {decision.action}")
        return '\n'.join(f"  {i+1}. {step}" for i, step in enumerate(chain))

    def _explain_alternatives(self, decision: Decision) -> str:
        """Explain why other options weren't chosen."""
        explanations = []
        for alt in decision.alternatives:
            explanations.append(f"  ❌ {alt.name}: {alt.rejection_reason}")
        explanations.append(f"  ✅ Chosen - {decision.action}: {decision.selection_reason}")
        return '\n'.join(explanations)

    def _explain_trade_offs(self, decision: Decision) -> str:
        if not decision.alternatives:
            return "No significant trade-offs as no viable alternatives were presented."
        return "Trading off alternative approaches for higher confidence and better fit with current constraints."

    def _explain_confidence(self, decision: Decision) -> Dict[str, Any]:
        """Explain confidence level."""
        factors = []

        if decision.evidence_quality > 0.8:
            factors.append("✓ Strong evidence")
        else:
            factors.append("⚠ Weak evidence")

        if decision.strategy_success_rate > 0.7:
            factors.append("✓ Proven strategy")
        else:
            factors.append("⚠ Untested approach")

        if decision.risk_score < 30:
            factors.append("✓ Low risk")
        else:
            factors.append("⚠ High risk")

        return {
            'level': decision.confidence,
            'factors': factors,
            'interpretation': self._interpret_confidence(decision.confidence)
        }

    def _interpret_confidence(self, confidence: float) -> str:
        if confidence >= 0.9: return "Very High"
        if confidence >= 0.7: return "High"
        if confidence >= 0.5: return "Moderate"
        return "Low"

    def _explain_risks(self, decision: Decision) -> str:
        if not decision.risks:
            return "No critical risks identified."
        return '\n'.join(f"  - {risk}" for risk in decision.risks)

    def _explain_next_steps(self, decision: Decision) -> str:
        if not decision.next_steps:
            return "Action is self-contained. No immediate next steps."
        return '\n'.join(f"  {i+1}. {step}" for i, step in enumerate(decision.next_steps))

    def _technical_details(self, decision: Decision) -> str:
        return f"Trigger: {decision.trigger} | Risk Score: {decision.risk_score}"

    def _executive_summary(self, explanation: Dict[str, Any]) -> Dict[str, Any]:
        # Strip complex logic, focus on summary, risks, and next steps
        return {
            'summary': explanation['summary'],
            'risks': explanation['risks'],
            'confidence': explanation['confidence'],
            'next_steps': explanation['next_steps']
        }

    def _simplify(self, explanation: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'summary': explanation['summary'],
            'reasoning': "We looked at the situation and picked the safest path.",
            'next_steps': explanation['next_steps']
        }

    def _format(self, explanation: Dict[str, Any], audience: str) -> str:
        lines = [f"=== DECISION EXPLANATION ({audience.upper()}) ==="]
        lines.append(f"Summary: {explanation['summary']}\n")
        
        if 'reasoning' in explanation:
            lines.append("Reasoning Chain:")
            lines.append(explanation['reasoning'] + "\n")
            
        if 'alternatives' in explanation:
            lines.append("Alternatives Considered:")
            lines.append(explanation['alternatives'] + "\n")

        if 'confidence' in explanation:
            conf = explanation['confidence']
            lines.append(f"Confidence: {conf['level']*100:.1f}% ({conf['interpretation']})")
            lines.append("Factors: " + ", ".join(conf['factors']) + "\n")

        if 'risks' in explanation:
            lines.append("Known Risks:")
            lines.append(explanation['risks'] + "\n")

        if 'next_steps' in explanation:
            lines.append("Next Steps:")
            lines.append(explanation['next_steps'])

        if 'details' in explanation:
            lines.append(f"\nTechnical Details: {explanation['details']}")

        return '\n'.join(lines)

    def explain_to_self(self, thinking_process: Dict[str, Any]) -> str:
        """Self-explanation: Explain own thinking to improve understanding."""
        lines = ["=== METACOGNITIVE SELF-EXPLANATION ==="]
        lines.append(f"What I Did: {thinking_process.get('what_i_did', 'N/A')}")
        lines.append(f"Why I Did It: {thinking_process.get('why_i_did_it', 'N/A')}")
        lines.append(f"What I Learned: {thinking_process.get('what_i_learned', 'N/A')}")
        lines.append(f"Improvements: {thinking_process.get('what_id_do_differently', 'N/A')}")
        return '\n'.join(lines)
