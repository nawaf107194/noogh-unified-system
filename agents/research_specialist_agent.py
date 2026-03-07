import logging
import asyncio
import time
from typing import Dict, Any, List

from unified_core.orchestration.agent_worker import AgentWorker
from unified_core.orchestration.messages import AgentRole
from tools.adapters.perplexity_adapter import PerplexityAdapter

logger = logging.getLogger("agents.research_specialist")

class ResearchSpecialistAgent(AgentWorker):
    """
    Agent for deep research and synthesis.
    Orchestrates traditional web search and advanced AI thinking tools.
    """
    
    def __init__(self):
        custom_handlers = {
            "THINK_DEEP": self._think_deep,
            "SYNTHESIZE_RESEARCH": self._synthesize_research,
        }
        role = AgentRole("research_specialist")
        super().__init__(role, custom_handlers)
        self.perplexity = PerplexityAdapter()
        logger.info("✅ ResearchSpecialistAgent initialized")

    async def _think_deep(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs in-depth research on a topic.
        
        Args:
            query (str): The research query.
        """
        query = task.get("query", task.get("input", ""))
        if not query:
            return {"success": False, "error": "No query provided"}

        logger.info(f"🧠 Deep Thinking requested: {query}")
        
        # Execute research via adapter
        result = await self.perplexity.research(query)
        
        if result["success"]:
            logger.info(f"✅ Deep research completed for: {query}")
        else:
            logger.warning(f"⚠️ Deep research failed: {result.get('error')}")
            
        return result

    async def _synthesize_research(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combines multiple research points into a technical report.
        """
        findings = task.get("findings", [])
        topic = task.get("topic", "General Discovery")
        
        if not findings:
            return {"success": False, "error": "No findings to synthesize"}
            
        report = f"# Research Synthesis: {topic}\n\n"
        report += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for i, item in enumerate(findings):
            report += f"## Analysis Point {i+1}\n"
            if isinstance(item, dict):
                content = item.get("content", str(item))
                citations = item.get("citations", [])
                report += f"{content}\n\n"
                if citations:
                    report += "**Sources:**\n"
                    for c in citations:
                        report += f"- {c}\n"
            else:
                report += f"{item}\n"
            report += "\n---\n\n"
            
        return {"success": True, "report": report}

if __name__ == "__main__":
    async def main():
        logging.basicConfig(level=logging.INFO)
        agent = ResearchSpecialistAgent()
        agent.start()
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
            
    asyncio.run(main())
