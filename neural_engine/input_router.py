import logging
from typing import Any, Dict

from .attention_mechanism import AttentionMechanism
from .filter_system import FilterSystem

logger = logging.getLogger(__name__)


class InputRouter:
    """
    Receives raw inputs from Sensory Layers, filters noise, prioritizing important signals,
    and routes them to the appropriate Cortex module.
    """

    def __init__(self):
        self.attention = AttentionMechanism()
        self.filters = FilterSystem()
        logger.info("InputRouter initialized.")

    async def route(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and route a raw input.

        Steps:
        1. Filter System (Reject noise/spam)
        2. Attention Mechanism (Score priority)
        3. Routing Logic (Determine destination)
        """
        if not self.filters.pass_filters(raw_input):
            logger.info("Input filtered out.")
            return None

        weighted_input = self.attention.weigh_importance(raw_input)
        logger.debug(f"Input routed with attention score: {weighted_input.get('attention_score')}")

        return weighted_input
