"""
Specialized Tools for ALLaM
Provides code intelligence, web research, and multi-agent capabilities.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# SECURITY: Allowed directories for file operations
import os
from pathlib import Path

# Only allow access to project directories
ALLOWED_ROOTS = [
    Path("/home/noogh/projects/noogh_unified_system/src"),
    Path("./").resolve(),
]

def _is_path_safe(path: str) -> bool:
    """
    Check if path is within allowed directories.
    SECURITY: Prevents path traversal and access to sensitive files.
    """
    try:
        resolved = Path(path).resolve()
        for allowed in ALLOWED_ROOTS:
            try:
                resolved.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False


# =====================================
# Code Intelligence Tools
# =====================================

def analyze_code(file_path: str) -> Dict[str, Any]:
    """
    Analyze a Python file for structure and documentation.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dict with code analysis
    """
    try:
        from neural_engine.specialized_systems import CodeAnalyzer
        
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file(file_path)
        
        return {
            "success": True,
            "file": file_path,
            "classes": result.get("classes", []),
            "functions": result.get("functions", []),
            "lines": result.get("total_lines", 0),
            "summary_ar": f"تحليل الملف: {len(result.get('classes', []))} كلاس، {len(result.get('functions', []))} دالة"
        }
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل تحليل الكود: {str(e)}"
        }


def read_code(file_path: str, start_line: int = 1, end_line: int = None) -> Dict[str, Any]:
    """
    Read source code from a file.
    
    Args:
        file_path: Path to the file
        start_line: Starting line (1-indexed)
        end_line: Ending line (optional)
        
    Returns:
        Dict with code content
    """
    # SECURITY FIX: Validate path before reading
    if not _is_path_safe(file_path):
        logger.warning(f"SECURITY_BLOCKED: read_code attempted on {file_path}")
        return {
            "success": False,
            "error": "SECURITY_BLOCKED: Path not allowed",
            "summary_ar": "تم حظر الوصول: المسار غير مسموح به"
        }
    
    try:
        from neural_engine.specialized_systems import CodeReader
        
        reader = CodeReader()
        content = reader.read_file(file_path, start_line, end_line)
        
        lines = content.split('\n')
        return {
            "success": True,
            "file": file_path,
            "content": content[:2000] + "..." if len(content) > 2000 else content,
            "lines": len(lines),
            "summary_ar": f"تم قراءة {len(lines)} سطر من {file_path}"
        }
    except Exception as e:
        logger.error(f"Code reading failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل قراءة الملف: {str(e)}"
        }


def list_project_files(directory: str = "./", pattern: str = "*.py") -> Dict[str, Any]:
    """
    List files in a project directory.
    
    Args:
        directory: Directory path
        pattern: File pattern (e.g., "*.py")
        
    Returns:
        Dict with file list
    """
    # SECURITY FIX: Validate path before listing
    if not _is_path_safe(directory):
        logger.warning(f"SECURITY_BLOCKED: list_project_files attempted on {directory}")
        return {
            "success": False,
            "error": "SECURITY_BLOCKED: Directory not allowed",
            "summary_ar": "تم حظر الوصول: المجلد غير مسموح به"
        }
    
    try:
        import glob
        
        full_pattern = os.path.join(directory, "**", pattern)
        files = glob.glob(full_pattern, recursive=True)
        
        # Limit to 50 files
        files = files[:50]
        
        return {
            "success": True,
            "directory": directory,
            "pattern": pattern,
            "files": files,
            "count": len(files),
            "summary_ar": f"تم العثور على {len(files)} ملف في {directory}"
        }
    except Exception as e:
        logger.error(f"File listing failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل استعراض الملفات: {str(e)}"
        }


# =====================================
# Web Research Tools
# =====================================

async def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web for information.
    
    Args:
        query: Search query
        num_results: Number of results
        
    Returns:
        Dict with search results
    """
    try:
        from neural_engine.specialized_systems import WebSearcher
        
        searcher = WebSearcher()
        results = await searcher.search(query, num_results=num_results)
        
        return {
            "success": True,
            "query": query,
            "results": results[:num_results],
            "count": len(results),
            "summary_ar": f"تم العثور على {len(results)} نتيجة لـ '{query}'"
        }
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "summary_ar": f"فشل البحث: {str(e)}"
        }


async def fetch_webpage(url: str) -> Dict[str, Any]:
    """
    Fetch and extract content from a webpage.
    
    Args:
        url: Webpage URL
        
    Returns:
        Dict with webpage content
    """
    try:
        from neural_engine.specialized_systems import ContentFetcher
        
        fetcher = ContentFetcher()
        content = await fetcher.fetch(url)
        
        return {
            "success": True,
            "url": url,
            "title": content.get("title", ""),
            "text": content.get("text", "")[:3000],
            "summary_ar": f"تم جلب المحتوى من: {url}"
        }
    except Exception as e:
        logger.error(f"Webpage fetch failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل جلب الصفحة: {str(e)}"
        }


# =====================================
# Multi-Agent Tools
# =====================================

def create_agent(
    name: str,
    agent_type: str = "goal_based",
    capabilities: List[str] = None
) -> Dict[str, Any]:
    """
    Create a new AI agent.
    
    Args:
        name: Agent name
        agent_type: Type (simple_reflex, model_based, goal_based, learning)
        capabilities: List of capabilities
        
    Returns:
        Dict with agent info
    """
    try:
        from neural_engine.specialized_systems.multi_agent.agent_system import (
            Agent, AgentType, AgentCapability
        )
        
        # Map type string to enum
        type_map = {
            "simple_reflex": AgentType.SIMPLE_REFLEX,
            "model_based": AgentType.MODEL_BASED,
            "goal_based": AgentType.GOAL_BASED,
            "utility_based": AgentType.UTILITY_BASED,
            "learning": AgentType.LEARNING
        }
        
        agent_type_enum = type_map.get(agent_type, AgentType.GOAL_BASED)
        
        # Map capability strings
        cap_map = {
            "delegate": AgentCapability.DELEGATE_TASKS,
            "api": AgentCapability.API_CALLS,
            "internet": AgentCapability.ACCESS_INTERNET,
            "code": AgentCapability.INTERPRET_CODE,
            "memory": AgentCapability.MEMORY_ACCESS,
            "autonomous": AgentCapability.AUTONOMOUS_ACTION
        }
        
        agent_caps = []
        for cap in (capabilities or ["memory", "code"]):
            if cap in cap_map:
                agent_caps.append(cap_map[cap])
        
        agent = Agent(
            agent_id=f"agent_{name}",
            name=name,
            agent_type=agent_type_enum,
            capabilities=agent_caps
        )
        
        return {
            "success": True,
            "agent_id": agent.agent_id,
            "name": name,
            "type": agent_type,
            "capabilities": capabilities or ["memory", "code"],
            "summary_ar": f"تم إنشاء الوكيل '{name}' من نوع {agent_type}"
        }
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل إنشاء الوكيل: {str(e)}"
        }


# =====================================
# Self-Improvement Tools
# =====================================

def start_self_improvement(focus_area: str = "general") -> Dict[str, Any]:
    """
    Start the self-improvement process.
    
    Args:
        focus_area: Area to focus on (general, coding, arabic, reasoning)
        
    Returns:
        Dict with improvement status
    """
    try:
        from neural_engine.specialized_systems import SelfImprovementEngine
        
        engine = SelfImprovementEngine()
        
        # Start improvement cycle
        result = engine.analyze_gaps(focus_area)
        
        return {
            "success": True,
            "focus_area": focus_area,
            "gaps_found": result.get("gaps", []),
            "recommendations": result.get("recommendations", []),
            "summary_ar": f"تم تحليل {focus_area}: وُجدت {len(result.get('gaps', []))} فجوات"
        }
    except Exception as e:
        logger.error(f"Self-improvement failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل التحسين الذاتي: {str(e)}"
        }


def get_capability_gaps() -> Dict[str, Any]:
    """
    Detect capability gaps in the system.
    
    Returns:
        Dict with detected gaps
    """
    try:
        from neural_engine.specialized_systems import CapabilityGapDetector
        
        if not isinstance(CapabilityGapDetector, type):
            raise TypeError("CapabilityGapDetector is not a valid class.")
        
        detector = CapabilityGapDetector()
        
        if not hasattr(detector, 'detect_gaps'):
            raise AttributeError("CapabilityGapDetector does not have a detect_gaps method.")
        
        gaps = detector.detect_gaps()
        
        if not isinstance(gaps, list):
            raise ValueError("The result of detect_gaps is not a list.")
        
        return {
            "success": True,
            "gaps": gaps[:10],  # Top 10 gaps
            "total": len(gaps),
            "summary_ar": f"تم اكتشاف {len(gaps)} فجوة في القدرات"
        }
    except ImportError as ie:
        logger.error(f"Import error: {ie}")
        return {
            "success": False,
            "error": str(ie),
            "summary_ar": f"خطأ في الاستيراد: {str(ie)}"
        }
    except (TypeError, AttributeError, ValueError) as e:
        logger.error(f"Type or attribute error: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"خطأ في نوع البيانات أو السمات: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Gap detection failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل اكتشاف الفجوات: {str(e)}"
        }


# =====================================
# Financial Analyst Tools
# =====================================

def analyze_finances(symbol: str = "BTC") -> Dict[str, Any]:
    """
    Analyze financial market data for a symbol.
    
    Args:
        symbol: Stock/crypto symbol (e.g., AAPL, BTC)
        
    Returns:
        Dict with market analysis
    """
    try:
        from neural_engine.specialized_systems.market_data import MarketData
        
        market = MarketData()
        price = market.get_price(symbol)
        
        return {
            "success": True,
            "symbol": symbol,
            "price": price,
            "currency": "USD",
            "summary_ar": f"سعر {symbol}: ${price:.2f}"
        }
    except Exception as e:
        logger.error(f"Financial analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل تحليل {symbol}: {str(e)}"
        }


# =====================================
# Thinking Partner Tools
# =====================================

async def think_together(
    prompt_type: str = "challenge",
    **kwargs
) -> Dict[str, Any]:
    """
    Use advanced thinking prompts for analysis.
    
    Args:
        prompt_type: Type of thinking (challenge, reframe, structure, etc.)
        **kwargs: Additional parameters for the prompt
        
    Returns:
        Dict with thinking analysis
    """
    try:
        from neural_engine.specialized_systems.thinking_partner.thinking_partner import ThinkingPartner
        # DO NOT import ReasoningEngine here - it causes duplicate model loading
        # from neural_engine.reasoning_engine import ReasoningEngine
        
        # Use None for LLM - ThinkingPartner should handle lazy loading
        # llm = ReasoningEngine(backend="local-gpu")  # ❌ This loads the model again!
        
        # Initialize thinking partner without LLM
        partner = ThinkingPartner(llm=None)
        
        # Perform thinking
        result = await partner.think(prompt_type, **kwargs)
        
        return {
            "success": True,
            "prompt_type": prompt_type,
            "analysis": result.get("analysis", ""),
            "timestamp": result.get("timestamp", ""),
            "summary_ar": f"تم التفكير باستخدام: {prompt_type}"
        }
    except Exception as e:
        logger.error(f"Thinking failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل التفكير: {str(e)}"
        }


# =====================================
# Agent Spawning Tools (Phase 3)
# =====================================

async def spawn_dev_agent(
    task_description: str,
    language: str = "python"
) -> Dict[str, Any]:
    """
    Spawn a development agent to generate code.
    
    Args:
        task_description: Description of the code to generate
        language: Programming language (python, rust, cpp, etc.)
        
    Returns:
        Dict with generated code
    """
    try:
        from unified_core.dev_agent import DevAgent, GenerationRequest, CodeLanguage
        
        # Map language string to enum
        lang_map = {
            "python": CodeLanguage.PYTHON,
            "rust": CodeLanguage.RUST,
            "cpp": CodeLanguage.CPP,
            "javascript": CodeLanguage.JAVASCRIPT,
            "go": CodeLanguage.GO,
            "sql": CodeLanguage.SQL
        }
        
        lang_enum = lang_map.get(language.lower(), CodeLanguage.PYTHON)
        
        # Create request
        request = GenerationRequest(
            task_description=task_description,
            language=lang_enum
        )
        
        # Initialize agent
        agent = DevAgent()
        
        # Generate code
        result = await agent.generate(request)
        
        if result.success:
            return {
                "success": True,
                "code": result.artifact.code[:1000],  # First 1000 chars
                "filename": result.artifact.filename,
                "language": language,
                "iterations": result.iterations,
                "security_approved": result.security_approved,
                "summary_ar": f"تم توليد كود {language}: {result.artifact.filename}"
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "summary_ar": f"فشل توليد الكود: {result.error}"
            }
    except Exception as e:
        logger.error(f"DevAgent spawn failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل إنشاء وكيل التطوير: {str(e)}"
        }


async def spawn_secops_agent(
    code: str,
    language: str = "python"
) -> Dict[str, Any]:
    """
    Spawn a security agent to audit code.
    
    Args:
        code: Code to audit
        language: Programming language
        
    Returns:
        Dict with security audit result
    """
    try:
        from unified_core.secops_agent import SecOpsAgent, SeverityLevel
        from unified_core.dev_agent import CodeArtifact, CodeLanguage
        
        # Map language
        lang_map = {
            "python": CodeLanguage.PYTHON,
            "rust": CodeLanguage.RUST,
        }
        lang_enum = lang_map.get(language.lower(), CodeLanguage.PYTHON)
        
        # Create artifact
        artifact = CodeArtifact(
            language=lang_enum,
            code=code,
            filename="temp_audit.py",
            description="Security audit"
        )
        
        # Initialize security agent
        agent = SecOpsAgent(max_severity=SeverityLevel.MEDIUM)
        
        # Audit
        result = await agent.audit(artifact)
        
        return {
            "success": True,
            "approved": result.approved,
            "issues": result.issues[:5],  # Top 5 issues
            "risk_score": result.risk_score,
            "execution_time_ms": result.execution_time_ms,
            "summary_ar": f"{'✅ مُعتمد' if result.approved else '❌ مرفوض'} - نقاط المخاطر: {result.risk_score:.1f}"
        }
    except Exception as e:
        logger.error(f"SecOpsAgent spawn failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary_ar": f"فشل التدقيق الأمني: {str(e)}"
        }


async def delegate_to_agent(
    agent_type: str,
    task: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Delegate a task to a specialized agent.
    
    Args:
        agent_type: Type of agent (dev, secops, multi)
        task: Task description
        **kwargs: Additional parameters
        
    Returns:
        Dict with delegation result
    """
    try:
        if agent_type == "dev":
            return await spawn_dev_agent(task, kwargs.get("language", "python"))
        elif agent_type == "secops":
            return await spawn_secops_agent(kwargs.get("code", ""), kwargs.get("language", "python"))
        elif agent_type == "multi":
            return create_agent(
                name=kwargs.get("name", "delegated_agent"),
                agent_type=kwargs.get("agent_type", "goal_based"),
                capabilities=kwargs.get("capabilities", ["memory", "code"])
            )
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
            "summary_ar": f"فشل التفويض: {str(e)}"
        }


# Tool registration helper
def register_specialized_tools(registry=None):
    """NO-OP: Tools are now defined in unified_core.tools.definitions.
    
    This function previously registered tools with the deprecated
    neural_engine.tools.tool_registry. All tools are now managed
    statically via unified_core.tool_registry.
    """
    logger.debug(
        "register_specialized_tools() is superseded by unified_core.tools.definitions"
    )

