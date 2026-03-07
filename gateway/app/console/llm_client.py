import os
from typing import Any, Dict


class LLMClient:
    def __init__(self):
        # Load the production-grade Master Prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "uc3_system_prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r") as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = "You are UC3, the Unified Cognitive Agent."

    async def classify_intent(self, user_text: str) -> Dict[str, Any]:
        """
        P1.7: Classify user intent using deterministic Mini DSL.

        Guarantees: Same input → Same output (100% reproducible)
        No LLM, no randomness, pure rule-based classification.

        Returns JSON matching INTENT_SCHEMA.
        """
        from gateway.app.console.intent_classifier import classify_intent_deterministic

        # Get deterministic classification
        result = classify_intent_deterministic(user_text)

        # Convert to UC3 expected format
        return {
            "mode": result["mode"],
            "confidence": result["confidence"],
            "summary": result["summary"],
            "requested_actions": [],
            "safety_notes": "read-only" if result["mode"] in ["OBSERVE", "ANALYZE"] else "requires confirmation",
        }

    async def reason(self, user_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the Neural Engine to reason about the user input with context.
        """
        import httpx

        neural_url = os.getenv("NEURAL_ENGINE_URL", "http://localhost:8002")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{neural_url}/api/v1/process", json={"text": user_text, "context": context, "store_memory": True}
                )
                response.raise_for_status()
                data = response.json()
                import logging

                logging.getLogger(__name__).info(f"DEBUG: Neural Response: {data}")
                return data
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Neural Engine rationalization failed: {e}")
            return {
                "conclusion": f"Error: Failed to connect to Neural Engine at {neural_url}. {str(e)}",
                "confidence": 0.0,
                "reasoning_trace": [f"Connection error: {e}"],
                "suggested_actions": [],
            }

    def get_system_prompt(self) -> str:
        """Return the full UC3 Master Prompt for LLM calls."""
        return self.system_prompt
