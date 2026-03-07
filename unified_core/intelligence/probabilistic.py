from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import math

@dataclass
class Hypothesis:
    """Represents a potential explanation or belief to be evaluated under uncertainty."""
    name: str
    description: str
    base_rate: float  # P(H): Initial probability or prior
    
@dataclass
class EvidenceProb:
    """Represents an observed piece of evidence."""
    name: str
    description: str
    baseline_prob: float  # P(E): How common is this evidence anyway?
    likelihood_if_true: float  # P(E|H): Probability of seeing this IF the hypothesis is true

@dataclass
class Outcome:
    """Represents a potential outcome of a decision."""
    description: str
    probability: float
    utility: float  # The value (positive) or cost (negative) of this outcome

@dataclass
class ProbabilisticOption:
    """Represents an actionable option with multiple possible outcomes."""
    name: str
    possible_outcomes: List[Outcome] = field(default_factory=list)


class ProbabilisticReasoner:
    """Core module for reasoning under uncertainty using Bayesian probabilities and Expected Value theory."""
    
    def evaluate_with_uncertainty(self, hypothesis: Hypothesis, evidence_list: List[EvidenceProb]) -> Dict[str, Any]:
        """
        Bayesian reasoning over multiple pieces of evidence: 
        P(H|E_1...E_n) ∝ P(H) * Π P(E_i|H)
        Normalized against the total probability of observing the evidence.
        """
        # Start with the prior P(H)
        prior = hypothesis.base_rate
        posterior_numerator = prior
        
        # Calculate likelihood product and evidence probability
        total_likelihood = 1.0
        total_evidence_prob = 1.0
        
        # We assume independent evidence for simplicity of the naive Bayes calculation
        for ev in evidence_list:
            # P(E_i|H)
            posterior_numerator *= ev.likelihood_if_true
            total_likelihood *= ev.likelihood_if_true
            # P(E_i)
            total_evidence_prob *= ev.baseline_prob
            
        # P(E) can't be exactly 0, prevent division error
        if total_evidence_prob <= 0.0:
            total_evidence_prob = 0.0001
            
        # Naive Bayes calculation (unnormalized)
        unnormalized_posterior = posterior_numerator
        
        # To get the true posterior, we need P(~H).
        # We assume P(E_i|~H) can be roughly derived from the baseline P(E_i) in this simplified model.
        # P(E) = P(E|H)P(H) + P(E|~H)P(~H)
        # So: P(E|~H) = (P(E) - P(E|H)P(H)) / P(~H)
        
        prob_not_h = 1.0 - prior
        if prob_not_h <= 0.0:
            prob_not_h = 0.0001
            
        likelihood_not_h = 1.0
        for ev in evidence_list:
            p_e_given_not_h = (ev.baseline_prob - (ev.likelihood_if_true * prior)) / prob_not_h
            # Clamp between 0.0001 and 0.9999
            p_e_given_not_h = max(0.0001, min(0.9999, p_e_given_not_h))
            likelihood_not_h *= p_e_given_not_h
            
        denominator = unnormalized_posterior + (likelihood_not_h * prob_not_h)
        posterior = unnormalized_posterior / denominator if denominator > 0 else 0.0
        
        # Clamp between 0 and 1
        posterior = max(0.0, min(1.0, posterior))
        
        return {
            'hypothesis': hypothesis.name,
            'prior': prior,
            'posterior': posterior,
            'confidence': posterior,
            'evidence_strength': total_likelihood / total_evidence_prob if total_evidence_prob > 0 else float('inf')
        }

    def _calculate_variance(self, option: ProbabilisticOption, expected_value: float) -> float:
        """Calculate the variance (risk dispersion) of the option."""
        if not option.possible_outcomes:
            return 0.0
        variance = sum(
            outcome.probability * ((outcome.utility - expected_value) ** 2)
            for outcome in option.possible_outcomes
        )
        return variance

    def _calculate_risk(self, option: ProbabilisticOption) -> float:
        """Calculate catastrophic risk (probability of a highly negative outcome)."""
        risk = 0.0
        for outcome in option.possible_outcomes:
            if outcome.utility < -50.0:  # Arbitrary threshold for "severe loss"
                risk += outcome.probability
        return risk

    def decision_under_uncertainty(self, options: List[ProbabilisticOption], risk_aversion: float = 1.0) -> Dict[str, Any]:
        """
        Choose the best option considering expected value and risk penalty.
        risk_aversion: multiplier for the penalty of standard deviation (variance penalty).
        """
        if not options:
            return {}
            
        evaluations = []

        for option in options:
            # Expected value = Σ(probability × utility)
            # Ensure probabilities sum to 1.0 implicitly, or normalize them
            total_prob = sum(o.probability for o in option.possible_outcomes)
            normalized_outcomes = option.possible_outcomes
            if total_prob > 0 and abs(total_prob - 1.0) > 0.01:
                normalized_outcomes = [
                    Outcome(o.description, o.probability / total_prob, o.utility)
                    for o in option.possible_outcomes
                ]
                
            ev = sum(outcome.probability * outcome.utility for outcome in normalized_outcomes)
            variance = self._calculate_variance(option, ev)
            std_dev = math.sqrt(variance)
            catastrophic_risk = self._calculate_risk(option)
            
            # Risk-adjusted value: EV - (Risk_Aversion * StdDev)
            risk_adjusted_value = ev - (risk_aversion * std_dev)

            evaluations.append({
                'option': option.name,
                'expected_value': ev,
                'standard_deviation': std_dev,
                'catastrophic_risk_prob': catastrophic_risk,
                'risk_adjusted_score': risk_adjusted_value
            })

        # Choose option with highest risk-adjusted value
        best_option = max(evaluations, key=lambda x: x['risk_adjusted_score'])
        
        return {
            'best_choice': best_option['option'],
            'evaluations': sorted(evaluations, key=lambda x: x['risk_adjusted_score'], reverse=True)
        }
