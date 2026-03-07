# unified_core/intelligence/multi_hypothesis_reasoning.py

import numpy as np
from typing import List, Dict

class MultiHypothesisReasoner:
    def __init__(self):
        self.hypotheses = []
    
    def add_hypothesis(self, hypothesis: Dict[str, any]):
        """
        Add a new hypothesis to the reasoning process.
        
        :param hypothesis: A dictionary containing the attributes of the hypothesis.
        """
        self.hypotheses.append(hypothesis)
    
    def evaluate(self) -> List[Dict[str, any]]:
        """
        Evaluate all hypotheses and return a list of their evaluations.
        
        :return: A list of dictionaries containing the evaluation results for each hypothesis.
        """
        evaluations = []
        for hypothesis in self.hypotheses:
            score = 0
            # Example: Score based on certain conditions
            if 'bullish' in hypothesis and hypothesis['bullish']:
                score += 1
            if 'bearish' in hypothesis and not hypothesis['bearish']:
                score -= 1
            
            evaluations.append({
                'hypothesis': hypothesis,
                'score': score
            })
        
        # Normalize scores to ensure they are comparable
        max_score = max([e['score'] for e in evaluations])
        min_score = min([e['score'] for e in evaluations])
        normalized_scores = [((e['score'] - min_score) / (max_score - min_score)) for e in evaluations]
        
        return evaluations, normalized_scores
    
    def select_best_hypothesis(self, scores: List[float]) -> Dict[str, any]:
        """
        Select the hypothesis with the highest score.
        
        :param scores: A list of scores corresponding to each hypothesis.
        :return: The best hypothesis dictionary.
        """
        index = np.argmax(scores)
        return self.hypotheses[index]

# Example usage
if __name__ == "__main__":
    reasoner = MultiHypothesisReasoner()
    reasoner.add_hypothesis({'bullish': True, 'volume': 1000})
    reasoner.add_hypothesis({'bearish': False, 'volume': 500})
    
    evaluations, scores = reasoner.evaluate()
    best_hypothesis = reasoner.select_best_hypothesis(scores)
    print("Best Hypothesis:", best_hypothesis)