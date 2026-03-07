# unified_core/intelligence/meta_cognition.py

import time
import requests
import logging
import re

logger = logging.getLogger("meta_cognition")

class MetaCognition:
    def __init__(self):
        self.confidence_score = 0.5  # Initial confidence score
        self.reasoning_history = []
        self.llm_url = "http://localhost:11434/api/generate"
        self.model = "qwen2.5-coder:14b"

    def evaluate_reasoning(self, reasoning_result):
        """Evaluate the reasoning using local LLM to get a genuine confidence score."""
        prompt = f"Evaluate the logical soundness and reliability of this reasoning. Respond ONLY with a confidence score between 0.0 and 1.0.\nReasoning:\n{reasoning_result}"
        
        try:
            response = requests.post(self.llm_url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }, timeout=3.0)
            
            if response.status_code == 200:
                text = response.json().get('response', '').strip()
                match = re.search(r'0\.\d+|1\.0', text)
                if match:
                    logger.debug(f"MetaCognition LLM evaluated confidence: {match.group()}")
                    return float(match.group())
        except Exception as e:
            logger.debug(f"LLM meta-cognition evaluation failed, using fallback: {e}")
            
        # Fallback heuristic if LLM is unavailable
        new_confidence = 0.7 if "highly reliable" in str(reasoning_result) else 0.4
        return new_confidence

    def update_confidence(self, new_confidence):
        self.confidence_score = new_confidence

    def decide_with_meta_cognition(self, decision_function, *args, **kwargs):
        reasoning_result = decision_function(*args, **kwargs)
        actual_confidence = self.evaluate_reasoning(reasoning_result)
        
        if actual_confidence < self.confidence_score:
            # The agent is more confident in its current reasoning
            return reasoning_result
        
        # Update confidence score based on the new reasoning
        self.update_confidence(actual_confidence)
        return reasoning_result

if __name__ == '__main__':
    def sample_decision_function(x, y):
        return x + y  # This is a placeholder for any decision-making function

    meta_cognition = MetaCognition()
    
    result = meta_cognition.decide_with_meta_cognition(sample_decision_function, 3, 4)
    print(f"Decision Result: {result}, Confidence Score: {meta_cognition.confidence_score}")