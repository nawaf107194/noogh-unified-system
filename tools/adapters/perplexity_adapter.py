import logging
import asyncio
import os
import json
import aiohttp
from typing import Dict, Any, List

logger = logging.getLogger("tools.adapters.perplexity")

class PerplexityAdapter:
    """
    Adapter for Perplexity AI API.
    Provides structured research with citations.
    """
    
    API_URL = "https://api.perplexity.ai/chat/completions"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not found. Using simulation mode.")

    async def research(self, query: str, model: str = "sonar") -> Dict[str, Any]:
        """
        Performs a deep research query.
        """
        if not self.api_key:
             return {"success": False, "error": "PERPLEXITY_API_KEY missing - Real research required.", "source": "perplexity"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Be precise and provide citations for your research findings."},
                {"role": "user", "content": query}
            ],
            "max_tokens": 1000,
            "temperature": 0.2
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.API_URL, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        citations = data.get("citations", [])
                        return {
                            "success": True,
                            "content": content,
                            "citations": citations,
                            "source": "perplexity"
                        }
                    else:
                        error_text = await resp.text()
                        logger.error(f"Perplexity API Error ({resp.status}): {error_text}")
                        return {"success": False, "error": f"API {resp.status}", "source": "perplexity"}
        except Exception as e:
            logger.error(f"Perplexity Connection Error: {e}")
            return {"success": False, "error": str(e), "source": "perplexity"}


if __name__ == "__main__":
    # Test script
    async def test():
        adapter = PerplexityAdapter()
        res = await adapter.research("What is the latest advancement in AI agent orchestration?")
        print(json.dumps(res, indent=2))
    
    asyncio.run(test())
