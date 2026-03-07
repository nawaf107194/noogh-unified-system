import logging
import asyncio
import os
import json
import aiohttp
from typing import Dict, Any, List

logger = logging.getLogger("tools.adapters.vendorful")

class VendorfulAdapter:
    """
    Adapter for Vendorful AI.
    Handles strategic response management and RFP automation.
    """
    
    API_URL = "https://api.vendorful.com/v1/responses"
    
    def __6init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("VENDORFUL_API_KEY")
        if not self.api_key:
            logger.warning("VENDORFUL_API_KEY not found. Using simulation mode.")

    async def generate_strategic_response(self, inquiry: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generates a strategic response for a given inquiry or RFP point.
        """
        if not self.api_key:
            return self._simulate_response(inquiry)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": inquiry,
            "context": context or {},
            "optimization_goal": "professional_win_rate"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.API_URL, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "response_text": data.get("suggested_response", ""),
                            "confidence": data.get("confidence_score", 0.0),
                            "source": "vendorful"
                        }
                    else:
                        error_text = await resp.text()
                        logger.error(f"Vendorful API Error ({resp.status}): {error_text}")
                        return {"success": False, "error": f"API {resp.status}", "source": "vendorful"}
        except Exception as e:
            logger.error(f"Vendorful Connection Error: {e}")
            return {"success": False, "error": str(e), "source": "vendorful"}

    def _simulate_response(self, inquiry: str) -> Dict[str, Any]:
        """Simulation fallback if API key is missing."""
        logger.info(f"Simulating Vendorful response for: {inquiry}")
        return {
            "success": True,
            "response_text": f"[Simulated Professional Response to: {inquiry}]\nWe propose a solution that...",
            "confidence": 0.85,
            "source": "simulation"
        }

if __name__ == "__main__":
    async def test():
        adapter = VendorfulAdapter()
        res = await adapter.generate_strategic_response("How does NOOGH handle data sovereignty?")
        print(json.dumps(res, indent=2))
    
    asyncio.run(test())
