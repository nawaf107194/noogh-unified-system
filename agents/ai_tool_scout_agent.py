import asyncio
import logging
import sqlite3
import json
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
load_dotenv("/home/noogh/projects/noogh_unified_system/src/.env")

from tools.openpedia_scraper import OpenPediaScraper
from unified_core.neural_bridge import NeuralEngineBridge, NeuralRequest

logger = logging.getLogger("ai_tool_scout_agent")

class AIToolScoutAgent:
    """
    Agent that autonomously scouts for new AI tools, 
    evaluates their relevance to NOOGH using the NeuralBridge,
    and maintains a database of potential integrations.
    """
    
    def __init__(self, neural_bridge: Optional[NeuralEngineBridge] = None):
        self.neural_bridge = neural_bridge
        self.db_path = "/home/noogh/projects/noogh_unified_system/src/data/ai_tools.sqlite"
        self.scraper = OpenPediaScraper(self.db_path)
        self._running = False
        self.scan_interval = 3600 * 24 # Original plan says every 24 hours

    async def start(self):
        """Starts the periodic scouting loop."""
        if self._running:
            return
        self._running = True
        logger.info("AIToolScoutAgent started.")
        asyncio.create_task(self._periodic_run())

    def stop(self):
        """Stops the periodic scouting loop."""
        self._running = False
        logger.info("AIToolScoutAgent stopped.")

    async def _periodic_run(self):
        """The main loop for the scouting agent."""
        while self._running:
            try:
                await self.run_scouting_cycle()
            except Exception as e:
                logger.error(f"Error in AIToolScoutAgent cycle: {e}")
            await asyncio.sleep(self.scan_interval)

    async def run_scouting_cycle(self):
        """Runs a discovery and evaluation cycle."""
        logger.info("🚀 Starting AI Tool Scouting Cycle...")
        
        # 1. Discover tools
        discovered_tools = self.scraper.run_discovery()
        
        # 2. Evaluate new or high-relevance tools with NeuralBridge
        for tool in discovered_tools:
            if tool["relevance_score"] >= 0.5:
                await self.deep_evaluate_tool(tool)
        
        logger.info("✅ Scouting cycle completed.")

    async def deep_evaluate_tool(self, tool: Dict[str, Any]):
        """Uses NeuralBridge to evaluate if a tool should be integrated."""
        if not self.neural_bridge:
            from unified_core.neural_bridge import get_neural_bridge
            self.neural_bridge = get_neural_bridge()

        prompt = f"""
        Analyze this AI tool for integration into the NOOGH Unified System:
        Tool Name: {tool['name']}
        Category: {tool['category']}
        Description: {tool['description']}
        API Available: {'Yes' if tool['api_available'] else 'No'}
        Relevance Score (Initial): {tool['relevance_score']}
        
        Goal: Determine if NOOGH should create a specialized agent for this tool.
        Return ONLY a JSON object with:
        {{
            "should_integrate": bool,
            "integration_priority": "high|medium|low",
            "suggested_agent_name": "string",
            "proposed_role": "string",
            "technical_risk": "string"
        }}
        """
        
        request = NeuralRequest(
            query=prompt, 
            urgency=0.5, 
            require_decision=True,
            context={"tool_data": tool}
        )
        
        try:
            response = await self.neural_bridge.think_with_authority(request)
            if response.success:
                content = response.content
                logger.info(f"🧠 Neural Evaluation for {tool['name']} (Raw): {content}")
                
                # Robust JSON extraction
                evaluation = {}
                if isinstance(content, dict):
                    evaluation = content
                else:
                    try:
                        import re
                        match = re.search(r"\{.*\}", str(content), re.DOTALL)
                        if match:
                            evaluation = json.loads(match.group())
                    except Exception as parse_err:
                        logger.error(f"Failed to parse JSON for {tool['name']}: {parse_err}")
                
                if evaluation:
                    self._update_tool_evaluation(tool["name"], evaluation)
                else:
                    logger.warning(f"No valid evaluation JSON found for {tool['name']}")
        except Exception as e:
            logger.error(f"Failed to evaluate tool {tool['name']}: {e}")

    def _update_tool_evaluation(self, tool_name: str, evaluation: Dict[str, Any]):
        """Persists evaluation results to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # We add status 'evaluated' and store findings
            cursor.execute('''
                UPDATE ai_tools 
                SET status = ?, 
                    relevance_score = CASE WHEN ? = 'high' THEN 0.9 ELSE relevance_score END
                WHERE name = ?
            ''', ("evaluated", evaluation.get("integration_priority"), tool_name))
        except Exception as e:
            logger.error(f"Error updating evaluation for {tool_name}: {e}")
        conn.commit()
        conn.close()

if __name__ == "__main__":
    # For manual testing
    import asyncio
    async def main():
        logging.basicConfig(level=logging.INFO)
        agent = AIToolScoutAgent()
        await agent.run_scouting_cycle()
    asyncio.run(main())
