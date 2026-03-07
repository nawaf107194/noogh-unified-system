import logging

logger = logging.getLogger(__name__)


class ContentGenerator:
    """
    Generates creative text formats.
    """

    def __init__(self):
        logger.info("ContentGenerator initialized.")

    def generate_haiku(self, topic: str) -> str:
        """
        Generates a Haiku about the topic.
        """
        # Template-based for now (Phase 4)
        return f"Code flows like water,\n{topic} is the stone inside,\nSilence brings the bug."
