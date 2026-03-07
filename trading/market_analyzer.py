import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger("trading.market_analyzer")

class MarketAnalyzer:
    """
    Synthesizes Technical Analysis (SMC/Order Flow) with Fundamental Research.
    Bridges the gap between the Trading Agent and Research Specialist.
    """
    
    def __init__(self, research_agent=None):
        self.research_agent = research_agent
        # Lazy import to avoid circular dependencies if needed
        if not self.research_agent:
            try:
                from agents.research_specialist_agent import ResearchSpecialistAgent
                self.research_agent = ResearchSpecialistAgent()
            except ImportError:
                logger.warning("ResearchSpecialistAgent not found. Market analyzer will be limited to technicals.")

    async def get_fundamental_context(self, symbol: str) -> str:
        """
        Fetches fundamental and sentiment context for a specific symbol.
        """
        if not self.research_agent:
            return "Fundamental analysis unavailable (Research agent not found)."
            
        logger.info(f"🔬 Fetching fundamental context for {symbol}...")
        
        task = {
            "query": f"Briefly analyze {symbol} crypto sentiment, recent big trades (whales), and major news in the last 12 hours. Format as bullet points."
        }
        
        try:
            # Note: Using _think_deep directly for synchronous-like internal call
            # In a full message bus system, this would be a bus request.
            result = await self.research_agent._think_deep(task)
            
            if result.get("success"):
                return result.get("content", "No significant fundamental data found.")
            else:
                return f"Research failed: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Error fetching fundamental context: {e}")
            return "Error during fundamental analysis."

    def synthesize_prompt(self, technical_data: str, fundamental_data: str) -> str:
        """
        Synthesizes technical and fundamental data into a single prompt for the 14B brain.
        """
        return f"""
[TECHNICAL ANALYSIS - SMC/ORDER FLOW]
{technical_data}

[FUNDAMENTAL & SENTIMENT ANALYSIS - PERPLEXITY]
{fundamental_data}

[MISSION]
As NOOGH 14B Sovereign Brain, synthesize these two layers.
- Does the fundamental sentiment confirm the technical trap/signal?
- Are there 'Whale' movements or 'News' that invalidate technical structures?
- Decide if this is a 'GOD-TIER' setup worthy of capital risk.
"""

if __name__ == "__main__":
    # Test stub
    analyzer = MarketAnalyzer()
    print("MarketAnalyzer initialized.")
