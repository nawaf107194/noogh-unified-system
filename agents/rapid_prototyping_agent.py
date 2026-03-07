"""NOOGH Rapid Prototyping Sandbox Agent

Purpose: Simulates an AI-first IDE environment (inspired by Cursor/Bolt/VibeCode).
Capabilities:
- RAPID_PROTOTYPE: Generates complete code projects or single scripts instantly in a local workspace directory.
"""

import asyncio
import logging
import time
import os
from typing import Dict, Any

from unified_core.orchestration.agent_worker import AgentWorker
from unified_core.orchestration.messages import AgentRole
from unified_core.core.memory_store import UnifiedMemoryStore
from unified_core.sandbox_service import SandboxService

logger = logging.getLogger("agents.rapid_prototyping")

class RapidPrototypingAgent(AgentWorker):
    """
    Rapid Prototyping IDE module to generate instant code workspaces.
    """
    
    def __init__(self):
        custom_handlers = {
            "RAPID_PROTOTYPE": self._rapid_prototype
        }
        # Assuming web_researcher or dev_agent role works, or generic role
        role = AgentRole("dev_agent") if hasattr(AgentRole, "dev_agent") else AgentRole("web_researcher")
        super().__init__(role, custom_handlers)
        
        self.memory = UnifiedMemoryStore()
        self.sandbox = SandboxService()
        logger.info("✅ RapidPrototypingAgent initialized (Cursor/Bolt Paradigm Active)")
            
    async def _rapid_prototype(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a conceptual prompt and prototypes an entire working script 
        or module using Sandbox Service and returns the file path.
        """
        prompt = task.get("prompt")
        if not prompt:
            return {"success": False, "error": "No prompt provided for rapid generation."}
            
        logger.info(f"🏗️ Generating Rapid Prototype for: {prompt[:50]}...")
        
        # In a real environment, this connects to the NOOGH Neural Engine to stream code!
        # Here we mock the AI generation part but allocate real files
        target_dir = f"/tmp/noogh_rapid_proto_{int(time.time())}"
        os.makedirs(target_dir, exist_ok=True)
        
        target_file = os.path.join(target_dir, "app.py")
        
        try:
            system_prompt = "You are NOOGH's Rapid Prototyping Module (like Cursor/Bolt). Output ONLY raw working Python code. No explanations. No Markdown blocks. Just raw valid code."
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "qwen2.5:7b" if os.environ.get("NEURAL_ENGINE_MODE") == "vllm" else "qwen2.5-coder:7b",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                }
                async with session.post("http://localhost:11434/v1/chat/completions", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    else:
                        response_content = f"# Generated with Error: {await resp.text()}"
            
            generated_code = response_content if response_content else "# Fallback empty file generation\nprint('Hello Builder')"
            generated_code = generated_code.replace("```python", "").replace("```", "").strip()
            
            with open(target_file, "w") as f:
                f.write(generated_code)
                
            # Log to WorldModel so NOOGH knows this tool was used
            obs = {
                "source": "RapidPrototypingAgent",
                "content": f"Generated rapid script for '{prompt}' at {target_file}",
                "timestamp": time.time()
            }
            await self.memory.append_observation(obs)
            
            return {
                "success": True, 
                "workspace": target_dir,
                "entry_file": target_file,
                "lines_generated": len(generated_code.splitlines())
            }
            
        except Exception as e:
            logger.error(f"Rapid prototyping failed: {e}")
            return {"success": False, "error": str(e)}

async def main():
    agent = RapidPrototypingAgent()
    agent.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 RapidPrototypingAgent stopping...")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(main())
