"""
Intelligent routing layer for Noogh (Decoupled Mode).
Internal Neural Engine routing is disabled.
All routing decisions are handled locally by AgentKernel.
"""

# NOTE:
# We intentionally disable all imports from neural_engine here
# because Gateway now talks to Neural via HTTP only.
# This prevents hard crashes when neural_engine is not installed.

HAS_INTERNAL_NEURAL = False


def intelligent_router(task: str):
    """
    Stub router for decoupled Neural Engine mode.
    Always returns None → AgentKernel decides locally.
    """
    return None
