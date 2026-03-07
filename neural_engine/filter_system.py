import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FilterSystem:
    """
    Blocks irrelevant or malformed inputs (Spam filter / Pre-processing gate).
    """

    def __init__(self):
        logger.info("FilterSystem initialized.")

    def pass_filters(self, input_data: Dict[str, Any]) -> bool:
            """
            Returns True if input should proceed, False otherwise.
            """
            if not input_data:
                return False

            content_key = "content"
            text_key = "text"

            content = input_data.get(content_key)
            if content is None:
                content = input_data.get(text_key)

            if content is None or (isinstance(content, str) and not content.strip()):
                return False

            return True
