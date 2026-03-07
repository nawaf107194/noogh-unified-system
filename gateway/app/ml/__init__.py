"""
Integration with HuggingFace for AutoML capabilities.
"""

import os
from pathlib import Path

# Setup Cache environment variables
# We avoid hard dependencies on core.paths here to prevent circular imports/side-effects.
# If env vars are set, use them. Otherwise, default to local relative paths or let libraries handle it.

if os.getenv("HF_CACHE_DIR"):
    HF_CACHE_DIR = Path(os.getenv("HF_CACHE_DIR"))
    HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(HF_CACHE_DIR)
    os.environ["TRANSFORMERS_CACHE"] = str(HF_CACHE_DIR / "transformers")
    os.environ["DATASETS_CACHE"] = str(HF_CACHE_DIR / "datasets")
