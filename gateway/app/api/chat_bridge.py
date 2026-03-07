"""
Chat-to-Orchestrator Bridge

Enables legacy Gateway chat interface to invoke modern multi-agent orchestrator
while maintaining backward compatibility with existing Neural Engine chat.
"""

import httpx
from typing import Optional, Dict, Any
from unified_core.observability import get_logger

logger = get_logger("gateway.chat_bridge")

import os

# Dashboard API base URL for agent invocation
DASHBOARD_API_URL = os.getenv("DASHBOARD_API_URL", "http://192.168.8.166:8003/api")


def detect_agent_intent(user_message: str) -> Optional[Dict[str, Any]]:
        """
        Detect if user message requires agent capabilities
    
        Args:
            user_message: User's chat message
        
        Returns:
            dict with agent intent if detected, None otherwise
            Example: {"agent_type": "code_executor", "task": "run python script"}
        """
        if not isinstance(user_message, str):
            logger.error(f"Invalid input type. Expected string, got {type(user_message)}")
            raise TypeError("Expected a string input")

        message_lower = user_message.lower().strip()

        # Code execution patterns (English + Arabic)
        code_keywords = ["execute", "run code", "python", "script", "cmd", "نفذ", "شغّل", "شغل"]
        if any(kw in message_lower for kw in code_keywords):
            logger.info(f"Detected code execution intent: {user_message}")
            return {
                "agent_type": "code_executor",
                "task": user_message,
                "capabilities": ["code_execution"]
            }

        # File operations patterns (English + Arabic)
        file_keywords = [
            "read file", "write file", "create file", "delete file",
            "اكتب ملف", "اقرأ ملف", "أنشئ ملف", "احذف ملف",
            "اقرا ملف", "انشئ ملف"
        ]
        if any(kw in message_lower for kw in file_keywords):
            logger.info(f"Detected file operation intent: {user_message}")
            return {
                "agent_type": "file_manager",
                "task": user_message,
                "capabilities": ["file_operations"]
            }

        # No agent needed
        logger.info(f"No agent intent detected: {user_message}")
        return None


async def invoke_agent_from_chat(
    intent: Dict[str, Any],
    user_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Invoke orchestrator agent via Dashboard API
    
    Args:
        intent: Agent intent from detect_agent_intent()
        user_token: JWT token for authentication
        
    Returns:
        dict: Agent response
        
    Raises:
        Exception: If orchestrator is not available or agent invocation fails
    """
    agent_type = intent.get("agent_type")
    task = intent.get("task")
    
    logger.info(f"Invoking agent: {agent_type} for task: {task[:50]}...")
    
    # Real implementation: Call orchestrator via Dashboard API
    # Note: This requires orchestrator to be running and exposing agent APIs
    headers = {}
    if user_token:
        headers["Authorization"] = f"Bearer {user_token}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{DASHBOARD_API_URL}/agents/invoke",
                json={
                    "agent_type": agent_type,
                    "task": task,
                    "capabilities": intent.get("capabilities", [])
                },
                headers=headers
            )
            
            if response.status_code == 404:
                # Orchestrator agent API not implemented yet
                raise Exception("Orchestrator agent API endpoint not available")
            
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error(f"Agent invocation failed: {e}")
        raise Exception(f"Failed to invoke agent {agent_type}: {str(e)}")
