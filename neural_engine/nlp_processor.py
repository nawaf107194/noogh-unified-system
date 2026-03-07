import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class NLPProcessor:
    """
    Basic Natural Language Processing unit.
    Handles tokenization, cleaning, and normalization.
    """

    def __init__(self):
        logger.info("NLPProcessor initialized.")

    def clean_text(self, text: str) -> str:
        """
        Smart text cleaning.
        Normalizes whitespace EXCEPT inside triple-backtick code blocks
        to maintain vital indentation for Python/Bash/etc.
        """
        if not text:
            return ""
        
        # Split by code blocks
        parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
        cleaned_parts = []
        
        for i, part in enumerate(parts):
            if i % 2 == 1:
                # Inside code block - DO NOT touch indentation or whitespace
                cleaned_parts.append(part)
            else:
                # Outside code block - normal whitespace normalization
                cleaned_parts.append(re.sub(r"\s+", " ", part))
                
        return "".join(cleaned_parts).strip()

    def tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization."""
        return self.clean_text(text).split(" ")
