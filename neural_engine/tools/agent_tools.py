"""
Agent Tools for ALLaM
Enables spawning and delegating to specialized agents.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


async def spawn_dev_agent(task: str) -> Dict[str, Any]:
    """
    Spawn a development agent for coding tasks.
    
    Args:
        task: Task description
        
    Returns:
        Dict with agent result
    """
    try:
        from unified_core.dev_agent import DevAgent
        
        agent = DevAgent()
        result = await agent.execute(task)
        
        return {
            "success": True,
            "agent": "dev_agent",
            "task": task,
            "result": result,
            "summary_ar": f"وكيل التطوير أنجز: {task[:50]}..."
        }
    except Exception as e:
        logger.error(f"Dev agent failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل وكيل التطوير: {str(e)}"
        }


async def spawn_secops_agent(task: str) -> Dict[str, Any]:
    """
    Spawn a security operations agent.
    
    Args:
        task: Security task description
        
    Returns:
        Dict with agent result
    """
    try:
        from unified_core.secops_agent import SecOpsAgent
        
        agent = SecOpsAgent()
        result = await agent.execute(task)
        
        return {
            "success": True,
            "agent": "secops_agent",
            "task": task,
            "result": result,
            "summary_ar": f"وكيل الأمان أنجز: {task[:50]}..."
        }
    except Exception as e:
        logger.error(f"SecOps agent failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل وكيل الأمان: {str(e)}"
        }


async def delegate_to_agent(agent_type: str, task: str) -> Dict[str, Any]:
    """
    Delegate a task to a specialized agent.
    
    Args:
        agent_type: Type of agent (dev, secops, unified, learning)
        task: Task to delegate
        
    Returns:
        Dict with delegation result
    """
    try:
        if agent_type == "dev":
            return await spawn_dev_agent(task)
        elif agent_type == "secops":
            return await spawn_secops_agent(task)
        elif agent_type == "unified":
            from neural_engine.autonomic_system.unified_agent import UnifiedAgent
            agent = UnifiedAgent()
            result = await agent.process(task)
            return {
                "success": True,
                "agent": "unified_agent",
                "task": task,
                "result": result,
                "summary_ar": f"الوكيل الموحد أنجز: {task[:50]}..."
            }
        elif agent_type == "learning":
            from neural_engine.specialized_systems import SelfImprovementLoop
            loop = SelfImprovementLoop()
            result = loop.start_cycle(focus=task)
            return {
                "success": True,
                "agent": "learning_agent",
                "task": task,
                "result": result,
                "summary_ar": f"وكيل التعلم أنجز: {task[:50]}..."
            }
        else:
            return {
                "success": False,
                "error": f"Unknown agent type: {agent_type}",
                "summary_ar": f"نوع وكيل غير معروف: {agent_type}"
            }
    except Exception as e:
        logger.error(f"Agent delegation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل تفويض المهمة: {str(e)}"
        }


def list_available_agents() -> Dict[str, Any]:
    """
    List all available agents and their capabilities.
    
    Returns:
        Dict with agent list
    """
    agents = [
        {
            "id": "dev_agent",
            "name": "وكيل التطوير",
            "description": "متخصص في مهام البرمجة والتطوير",
            "capabilities": ["كتابة الكود", "مراجعة الكود", "إصلاح الأخطاء"]
        },
        {
            "id": "secops_agent",
            "name": "وكيل الأمان",
            "description": "متخصص في الأمان والحماية",
            "capabilities": ["فحص الثغرات", "مراجعة الأمان", "تشفير"]
        },
        {
            "id": "unified_agent",
            "name": "الوكيل الموحد",
            "description": "وكيل متعدد الأغراض",
            "capabilities": ["المهام العامة", "التنسيق", "التحليل"]
        },
        {
            "id": "learning_agent",
            "name": "وكيل التعلم",
            "description": "متخصص في التعلم الذاتي",
            "capabilities": ["اكتشاف الفجوات", "جمع البيانات", "التدريب"]
        }
    ]
    
    return {
        "success": True,
        "agents": agents,
        "count": len(agents),
        "summary_ar": f"يوجد {len(agents)} وكلاء متاحين"
    }


# Tool registration helper
def register_agent_tools(registry=None):
    """NO-OP: Tools are now defined in unified_core.tools.definitions.
    
    This function previously registered tools with the deprecated
    neural_engine.tools.tool_registry. All tools are now managed
    statically via unified_core.tool_registry.
    """
    logger.debug(
        "register_agent_tools() is superseded by unified_core.tools.definitions"
    )
