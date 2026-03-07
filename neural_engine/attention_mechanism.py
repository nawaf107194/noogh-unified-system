import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AttentionMechanism:
    """
    Assigns conceptual 'energy' or importance to inputs.
    High priority inputs (e.g., specific keywords, urgent signals) get higher scores.
    """

    def __init__(self):
        self.urgent_keywords = ["error", "alert", "critical", "urgent"]
        logger.info("AttentionMechanism initialized.")

    def weigh_importance(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Calculate and append attention score to input.
            """
            score = 0.5  # Default neutral score

            text_content = input_data.get("content", "")
            if not text_content:
                return input_data

            if any(kw in text_content.lower() for kw in self.urgent_keywords):
                score = 0.9

            input_data["attention_score"] = score
            return input_data
