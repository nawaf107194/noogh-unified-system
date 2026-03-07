from typing import Dict, List, Tuple
import numpy as np

class MultiHypothesisReasoning:
    def __init__(self, hypotheses: List[str], weights: Dict[str, float]):
        """
        Initialize the multi-hypothesis reasoning module.
        
        :param hypotheses: A list of hypothesis names (e.g., ['bull', 'bear']).
        :param weights: A dictionary mapping each hypothesis to its initial weight.
        """
        self.hypotheses = hypotheses
        self.weights = weights
        self.evidence = {h: [] for h in hypotheses}

    def update_evidence(self, hypothesis: str, new_evidence: float) -> None:
        """
        Update the evidence for a given hypothesis.
        
        :param hypothesis: The hypothesis to update evidence for.
        :param new_evidence: New evidence value to add.
        """
        if hypothesis in self.hypotheses:
            self.evidence[hypothesis].append(new_evidence)
        else:
            raise ValueError(f"Hypothesis '{hypothesis}' not recognized.")

    def calculate_weights(self) -> Dict[str, float]:
        """
        Recalculate the weights of each hypothesis based on accumulated evidence.
        
        :return: Updated weights for each hypothesis.
        """
        updated_weights = {}
        total_evidence = sum(np.mean(evid) * self.weights[hyp] for hyp, evid in self.evidence.items())
        
        for hypothesis, evidence_list in self.evidence.items():
            if evidence_list:
                mean_evidence = np.mean(evidence_list)
                updated_weights[hypothesis] = (mean_evidence * self.weights[hypothesis]) / total_evidence
            else:
                updated_weights[hypothesis] = self.weights[hypothesis]

        return updated_weights

    def decide_action(self, updated_weights: Dict[str, float]) -> str:
        """
        Decide on an action based on the updated weights of each hypothesis.
        
        :param updated_weights: The updated weights of each hypothesis.
        :return: The action to take ('buy', 'sell', or 'hold').
        """
        max_weight_hypothesis = max(updated_weights, key=updated_weights.get)
        if max_weight_hypothesis == 'bull':
            return 'buy'
        elif max_weight_hypothesis == 'bear':
            return 'sell'
        else:
            return 'hold'

# Example usage
if __name__ == "__main__":
    # Initialize with two hypotheses: bull and bear
    mhr = MultiHypothesisReasoning(['bull', 'bear'], {'bull': 0.5, 'bear': 0.5})
    
    # Simulate adding evidence
    mhr.update_evidence('bull', 0.8)
    mhr.update_evidence('bear', 0.6)
    mhr.update_evidence('bull', 0.9)
    
    # Calculate updated weights
    updated_weights = mhr.calculate_weights()
    
    # Decide on an action
    action = mhr.decide_action(updated_weights)
    
    print(f"Updated Weights: {updated_weights}")
    print(f"Action: {action}")