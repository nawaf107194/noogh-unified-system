from typing import List, Dict
import numpy as np

class MultiHypothesisReasoning:
    def __init__(self, hypotheses: List[Dict[str, float]]):
        """
        Initialize the multi-hypothesis reasoning module with a list of hypotheses.
        
        Each hypothesis is represented as a dictionary with keys 'name' and 'weight'.
        The 'name' key corresponds to the name of the hypothesis (e.g., 'bull', 'bear').
        The 'weight' key corresponds to the initial confidence weight assigned to the hypothesis.
        
        :param hypotheses: List of hypotheses with their initial weights.
        """
        self.hypotheses = hypotheses
        self.current_weights = {h['name']: h['weight'] for h in hypotheses}

    def update_hypothesis_weights(self, evidence: Dict[str, float]):
        """
        Update the weights of each hypothesis based on new evidence.
        
        The evidence is provided as a dictionary where the key is the name of the hypothesis,
        and the value is the strength of the evidence supporting that hypothesis.
        
        :param evidence: Dictionary of evidence supporting each hypothesis.
        """
        total_evidence_strength = sum(evidence.values())
        normalized_evidence = {k: v / total_evidence_strength for k, v in evidence.items()}
        
        for hypothesis_name in self.current_weights.keys():
            if hypothesis_name in normalized_evidence:
                # Update the weight using a simple linear model
                self.current_weights[hypothesis_name] *= (1 + normalized_evidence[hypothesis_name])
            else:
                # If no evidence is provided for a hypothesis, slightly reduce its weight
                self.current_weights[hypothesis_name] *= 0.95

    def get_decision(self):
        """
        Get the decision based on the current weights of the hypotheses.
        
        Returns the name of the hypothesis with the highest weight.
        """
        return max(self.current_weights, key=self.current_weights.get)

    def normalize_weights(self):
        """
        Normalize the weights so they sum up to 1, representing probabilities.
        """
        total_weight = sum(self.current_weights.values())
        self.current_weights = {k: v / total_weight for k, v in self.current_weights.items()}

# Example usage:
if __name__ == "__main__":
    hypotheses = [
        {'name': 'bull', 'weight': 0.6},
        {'name': 'bear', 'weight': 0.4}
    ]
    
    mhr = MultiHypothesisReasoning(hypotheses)
    
    # Simulate receiving new evidence
    evidence = {'bull': 0.8, 'bear': 0.2}
    mhr.update_hypothesis_weights(evidence)
    
    print("Current Hypothesis Weights:", mhr.current_weights)
    print("Decision Based on Current Weights:", mhr.get_decision())
    
    # Normalize weights for probabilistic interpretation
    mhr.normalize_weights()
    print("Normalized Hypothesis Weights:", mhr.current_weights)