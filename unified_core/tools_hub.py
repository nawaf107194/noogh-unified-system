"""
NOOGH Tools Hub — طبقة التكامل الموحدة للأدوات الخارجية
═══════════════════════════════════════════════════════
يربط 18 أداة AI خارجية بنظام NOOGH عبر adapters موحدة.

Architecture:
    ToolsHub (Singleton)
    ├── ShannonAdapter       — AI Pentesting (security scanning)
    ├── SmolAgentsAdapter    — HuggingFace agent framework
    ├── Mem0Adapter          — Persistent memory engine
    ├── LangChainAdapter     — LLM pipeline orchestration
    ├── VERLAdapter          — RL for LLMs (training)
    ├── ComposioAdapter      — External tool integrations
    ├── AutoGPTAdapter       — Self-driving agent patterns
    ├── OpenHandsAdapter     — Agentic IDE patterns
    ├── AiderAdapter         — Git-native code assistant
    ├── OpenCodeAdapter      — Claude Code alternative
    ├── GeminiADKAdapter     — Google Agent Development Kit
    ├── AgentsCourseAdapter  — HuggingFace educational resources
    ├── EvoAgentXAdapter     — Self-evolving agent framework  [NEW]
    ├── Agent0Adapter        — Zero-data self-evolution       [NEW]
    ├── AIHedgeFundAdapter   — Multi-agent trading simulation [NEW]
    ├── AgentZeroAdapter     — Self-correcting autonomous agent[NEW]
    ├── OpenR1Adapter        — HuggingFace RL pipelines       [NEW]
    └── XCoderRLAdapter      — RL training dataset (40K tasks)[NEW]

Usage:
    hub = get_tools_hub()
    await hub.initialize()
    
    # Security scan
    results = await hub.shannon.scan_project("/path/to/project")
    
    # Persistent memory
    await hub.mem0.add_memory("user_preference", {"key": "value"})
    
    # Agent creation via smolagents
    agent = await hub.smolagents.create_agent(tools=[...])
"""

import asyncio
import importlib
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("unified_core.tools_hub")

# ══════════════════════════════════════════════════════════
# Base Adapter
# ══════════════════════════════════════════════════════════

TOOLS_DIR = Path("/home/noogh/projects/tools")


class BaseToolAdapter:
    """قاعدة لكل adapter — تهيئة كسولة مع fallback أمن"""
    
    name: str = "base"
    tool_dir: str = ""
    required_packages: List[str] = []
    
    def __init__(self):
        self._initialized = False
        self._available = False
        self._error = None
        self._module = None
    
    @property
    def available(self) -> bool:
        return self._available
    
    @property
    def initialized(self) -> bool:
        return self._initialized
    
    async def initialize(self) -> bool:
        """تهيئة الأداة — كسولة وآمنة"""
        try:
            tool_path = TOOLS_DIR / self.tool_dir
            if not tool_path.exists():
                self._error = f"Tool directory not found: {tool_path}"
                logger.warning(f"⚠️ {self.name}: {self._error}")
                return False
            
            # Add to Python path if needed
            src_path = tool_path / "src"
            if src_path.exists():
                if str(src_path) not in sys.path:
                    sys.path.insert(0, str(src_path))
            elif str(tool_path) not in sys.path:
                sys.path.insert(0, str(tool_path))
            
            self._available = True
            self._initialized = True
            logger.info(f"✅ {self.name} adapter initialized")
            return True
            
        except Exception as e:
            self._error = str(e)
            logger.warning(f"⚠️ {self.name} initialization failed: {e}")
            return False
    
    def status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "available": self._available,
            "initialized": self._initialized,
            "error": self._error,
            "tool_dir": str(TOOLS_DIR / self.tool_dir),
        }


# ══════════════════════════════════════════════════════════
# 1. Shannon — AI Pentester
# ══════════════════════════════════════════════════════════

class ShannonAdapter(BaseToolAdapter):
    """
    Shannon AI Pentester — فحص أمني مستقل
    يكتشف ثغرات ويستغلها فعلياً (Proof by Exploitation)
    """
    name = "Shannon"
    tool_dir = "shannon"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        if result:
            # Verify Shannon structure
            shannon_path = TOOLS_DIR / "shannon"
            configs = shannon_path / "configs"
            self._configs_dir = configs if configs.exists() else None
            self._docker_available = (shannon_path / "docker-compose.yml").exists()
        return result
    
    async def scan_project(self, target_path: str, mode: str = "lite") -> Dict[str, Any]:
        """
        فحص أمني لمشروع باستخدام Shannon
        mode: 'lite' (local) or 'full' (Docker)
        """
        if not self._available:
            return {"error": "Shannon not available", "status": "skipped"}
        
        try:
            shannon_dir = TOOLS_DIR / "shannon"
            
            # Check if we can run Shannon via Docker
            if self._docker_available and mode == "full":
                cmd = [
                    "docker-compose", "-f", str(shannon_dir / "docker-compose.yml"),
                    "run", "--rm", "shannon",
                    "--target", target_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                return {
                    "status": "completed",
                    "mode": "docker",
                    "output": result.stdout,
                    "errors": result.stderr
                }
            else:
                # Lite mode — analyze configs and structure
                vulnerabilities = await self._static_analysis(target_path)
                return {
                    "status": "completed",
                    "mode": "static",
                    "vulnerabilities": vulnerabilities,
                    "target": target_path
                }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    async def _static_analysis(self, target_path: str) -> List[Dict]:
        """تحليل استاتيكي أساسي — نمط Shannon"""
        findings = []
        target = Path(target_path)
        
        # Check for common security issues
        patterns = {
            "eval(": "Code Injection — eval() usage",
            "exec(": "Code Injection — exec() usage",
            "subprocess.call(": "Command Injection risk — subprocess.call",
            "os.system(": "Command Injection risk — os.system",
            "pickle.loads": "Deserialization vulnerability — pickle",
            "yaml.load(": "YAML deserialization — use yaml.safe_load",
            "shell=True": "Shell injection risk — shell=True",
            "password": "Possible hardcoded credential",
            "secret": "Possible hardcoded secret",
            "api_key": "Possible exposed API key",
        }
        
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text(errors="ignore")
                for pattern, desc in patterns.items():
                    if pattern in content:
                        # Count occurrences
                        lines = [i+1 for i, line in enumerate(content.split('\n')) 
                                if pattern in line]
                        findings.append({
                            "file": str(py_file.relative_to(target)),
                            "pattern": pattern,
                            "description": desc,
                            "severity": "HIGH" if "injection" in desc.lower() else "MEDIUM",
                            "lines": lines[:5],
                        })
            except Exception:
                continue
        
        return findings
    
    def get_report(self, scan_results: Dict) -> str:
        """تقرير مقروء من نتائج الفحص"""
        if "error" in scan_results:
            return f"❌ Shannon Scan Error: {scan_results['error']}"
        
        vulns = scan_results.get("vulnerabilities", [])
        if not vulns:
            return "✅ Shannon: No vulnerabilities detected"
        
        report = f"🔒 Shannon Security Report\n{'='*40}\n"
        report += f"Total findings: {len(vulns)}\n\n"
        
        for v in vulns:
            severity_icon = "🔴" if v['severity'] == "HIGH" else "🟡"
            report += f"{severity_icon} [{v['severity']}] {v['description']}\n"
            report += f"   📁 {v['file']} (lines: {v['lines']})\n\n"
        
        return report


# ══════════════════════════════════════════════════════════
# 2. SmolAgents — HuggingFace Agent Framework
# ══════════════════════════════════════════════════════════

class SmolAgentsAdapter(BaseToolAdapter):
    """
    HuggingFace smolagents — إطار بناء Agents خفيف
    يدعم إنشاء agents بأدوات مخصصة وتنفيذ كود
    """
    name = "SmolAgents"
    tool_dir = "smolagents"
    
    async def initialize(self) -> bool:
        self._smolagents = None
        result = await super().initialize()
        return result
    
    async def install(self) -> bool:
        """تثبيت smolagents عبر pip"""
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", "-e",
                str(TOOLS_DIR / "smolagents"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                self._smolagents = importlib.import_module("smolagents")
                logger.info("✅ SmolAgents installed successfully")
                return True
            else:
                logger.error(f"❌ SmolAgents install failed: {stderr.decode()[:200]}")
                return False
        except Exception as e:
            logger.error(f"❌ SmolAgents install error: {e}")
            return False
    
    async def create_code_agent(self, model_id: str = None, tools: list = None) -> Any:
        """إنشاء CodeAgent من smolagents"""
        if not self._smolagents:
            await self.install()
        
        if self._smolagents:
            try:
                CodeAgent = getattr(self._smolagents, 'CodeAgent', None)
                if CodeAgent:
                    agent = CodeAgent(
                        tools=tools or [],
                        model=model_id or "local"
                    )
                    return agent
            except Exception as e:
                logger.error(f"Agent creation failed: {e}")
        return None
    
    def get_available_tools(self) -> List[str]:
        """قائمة الأدوات المتاحة في smolagents"""
        if not self._smolagents:
            return []
        try:
            return [name for name in dir(self._smolagents) 
                    if 'tool' in name.lower() or 'Tool' in name]
        except Exception:
            return []


# ══════════════════════════════════════════════════════════
# 3. Mem0 — Persistent Memory Engine
# ══════════════════════════════════════════════════════════

class Mem0Adapter(BaseToolAdapter):
    """
    Mem0 (Memori) — ذاكرة دائمة لأنظمة AI
    تخزين واسترجاع واستدعاء ذكريات ذكية
    """
    name = "Mem0"
    tool_dir = "memori"
    
    async def initialize(self) -> bool:
        self._mem0 = None
        result = await super().initialize()
        return result
    
    async def install(self) -> bool:
        """تثبيت Mem0"""
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", "-e",
                str(TOOLS_DIR / "memori"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                self._mem0 = importlib.import_module("mem0")
                logger.info("✅ Mem0 installed successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Mem0 install error: {e}")
            return False
    
    async def create_memory(self, config: Dict = None) -> Any:
        """إنشاء Memory instance للتكامل مع NOOGH"""
        if not self._mem0:
            await self.install()
        
        if self._mem0:
            try:
                Memory = getattr(self._mem0, 'Memory', None)
                if Memory:
                    return Memory(config=config or {})
            except Exception as e:
                logger.error(f"Memory creation failed: {e}")
        return None
    
    async def add_memory(self, content: str, metadata: Dict = None, 
                         user_id: str = "noogh") -> Dict:
        """إضافة ذكرى جديدة"""
        try:
            memory = await self.create_memory()
            if memory:
                result = memory.add(content, user_id=user_id, metadata=metadata or {})
                return {"status": "added", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def search_memory(self, query: str, user_id: str = "noogh") -> List[Dict]:
        """بحث في الذاكرة"""
        try:
            memory = await self.create_memory()
            if memory:
                return memory.search(query, user_id=user_id)
        except Exception as e:
            logger.error(f"Memory search error: {e}")
        return []


# ══════════════════════════════════════════════════════════
# 4. LangChain — LLM Pipeline Orchestration
# ══════════════════════════════════════════════════════════

class LangChainAdapter(BaseToolAdapter):
    """
    LangChain — إطار بناء تطبيقات LLM متقدمة
    chains, agents, RAG, memory
    """
    name = "LangChain"
    tool_dir = "langchain"
    
    async def initialize(self) -> bool:
        self._langchain = None
        result = await super().initialize()
        return result
    
    async def install(self) -> bool:
        """تثبيت LangChain Core"""
        try:
            langchain_core = TOOLS_DIR / "langchain" / "libs" / "core"
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", "-e",
                str(langchain_core),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            langchain_main = TOOLS_DIR / "langchain" / "libs" / "langchain"
            proc2 = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", "-e",
                str(langchain_main),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc2.communicate()
            
            self._langchain = importlib.import_module("langchain")
            return True
        except Exception as e:
            logger.error(f"LangChain install error: {e}")
            return False
    
    def get_available_modules(self) -> List[str]:
        """قائمة modules LangChain المتاحة"""
        libs_path = TOOLS_DIR / "langchain" / "libs"
        if libs_path.exists():
            return [d.name for d in libs_path.iterdir() if d.is_dir()]
        return []


# ══════════════════════════════════════════════════════════
# 5. VERL — Reinforcement Learning for LLMs
# ══════════════════════════════════════════════════════════

class VERLAdapter(BaseToolAdapter):
    """
    VERL (Volcano Engine RL) — Reinforcement Learning خاص بالـ LLMs
    fine-tuning وتحسين الأداء بـ RL
    """
    name = "VERL"
    tool_dir = "verl"
    
    async def initialize(self) -> bool:
        self._verl = None
        result = await super().initialize()
        return result
    
    def get_training_configs(self) -> List[str]:
        """قائمة إعدادات التدريب المتاحة"""
        examples = TOOLS_DIR / "verl" / "examples"
        if examples.exists():
            return [str(f.relative_to(examples)) 
                    for f in examples.rglob("*.yaml")]
        return []
    
    def get_algorithms(self) -> List[str]:
        """الخوارزميات المدعومة"""
        return ["PPO", "GRPO", "ReMax", "REINFORCE"]


# ══════════════════════════════════════════════════════════
# 6. Composio — External Tool Integrations
# ══════════════════════════════════════════════════════════

class ComposioAdapter(BaseToolAdapter):
    """
    Composio — ربط AI Agents بأدوات خارجية
    GitHub, Jira, Slack, Gmail, 150+ integration
    """
    name = "Composio"
    tool_dir = "composio"
    
    async def initialize(self) -> bool:
        self._composio = None
        result = await super().initialize()
        return result
    
    def get_available_integrations(self) -> List[str]:
        """قائمة التكاملات المتاحة"""
        return [
            "github", "gitlab", "jira", "slack", "discord",
            "gmail", "google_drive", "notion", "linear",
            "trello", "asana", "figma", "vercel", "aws"
        ]


# ══════════════════════════════════════════════════════════
# 7. AutoGPT — Self-Driving Agent Patterns
# ══════════════════════════════════════════════════════════

class AutoGPTAdapter(BaseToolAdapter):
    """
    AutoGPT — أنماط Agent ذاتي القيادة
    تحليل ودراسة patterns لتحسين NOOGH
    """
    name = "AutoGPT"
    tool_dir = "AutoGPT"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        if result:
            self._platform_dir = TOOLS_DIR / "AutoGPT" / "autogpt_platform"
            self._classic_dir = TOOLS_DIR / "AutoGPT" / "classic"
        return result
    
    def get_architecture_insights(self) -> Dict[str, Any]:
        """استخراج أنماط معمارية من AutoGPT"""
        insights = {
            "goal_decomposition": "AutoGPT breaks goals into sub-tasks automatically",
            "memory_management": "Uses both short-term and long-term memory",
            "self_feedback": "Agent evaluates its own outputs",
            "plugin_system": "Extensible via plugins",
            "command_registry": "Commands registered with descriptions",
        }
        
        # Check for platform components
        if self._platform_dir and self._platform_dir.exists():
            components = [d.name for d in self._platform_dir.iterdir() 
                         if d.is_dir() and not d.name.startswith('.')]
            insights["platform_components"] = components
        
        return insights


# ══════════════════════════════════════════════════════════
# 8. OpenHands — Agentic IDE Patterns
# ══════════════════════════════════════════════════════════

class OpenHandsAdapter(BaseToolAdapter):
    """
    OpenHands — AI Agent يدير مشاريع (مثل Devin)
    دراسة أنماط coding agent
    """
    name = "OpenHands"
    tool_dir = "OpenHands"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        if result:
            self._openhands_dir = TOOLS_DIR / "OpenHands"
        return result
    
    def get_agent_patterns(self) -> Dict[str, str]:
        """أنماط الـ Agent المستخدمة"""
        return {
            "sandboxed_execution": "Code runs in isolated Docker containers",
            "observation_action_loop": "Agent observes → thinks → acts",
            "file_system_awareness": "Agent understands project structure",
            "terminal_integration": "Direct terminal command execution",
            "browser_integration": "Can browse and interact with web pages",
            "multi_agent_delegation": "Tasks can be delegated between agents",
        }


# ══════════════════════════════════════════════════════════
# 9. Aider — Git-Native Code Assistant
# ══════════════════════════════════════════════════════════

class AiderAdapter(BaseToolAdapter):
    """
    Aider — مساعد كتابة كود مبني على Git
    يعدل كود ويعرض التغييرات كـ diffs
    """
    name = "Aider"
    tool_dir = "aider"
    
    async def initialize(self) -> bool:
        self._aider = None
        result = await super().initialize()
        return result
    
    async def run_edit(self, files: List[str], instruction: str, 
                       model: str = "local") -> Dict:
        """طلب تعديل كود عبر Aider"""
        if not self._available:
            return {"error": "Aider not available"}
        
        try:
            aider_dir = TOOLS_DIR / "aider"
            cmd = [
                sys.executable, "-m", "aider",
                "--message", instruction,
                "--model", model,
                "--no-auto-commits",
                "--yes",
            ] + files
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, 
                timeout=120, cwd=str(aider_dir)
            )
            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "errors": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}


# ══════════════════════════════════════════════════════════
# 10. OpenCode — Claude Code Alternative
# ══════════════════════════════════════════════════════════

class OpenCodeAdapter(BaseToolAdapter):
    """
    OpenCode — بديل مفتوح لـ Claude Code
    يدعم عدة موديلات: Anthropic, OpenAI, Gemini, Ollama
    """
    name = "OpenCode"
    tool_dir = "opencode"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        if result:
            # OpenCode is written in Go
            self._binary = TOOLS_DIR / "opencode" / "opencode"
            self._go_project = (TOOLS_DIR / "opencode" / "go.mod").exists()
        return result
    
    async def build(self) -> bool:
        """بناء OpenCode من السورس"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "go", "build", "-o", "opencode", ".",
                cwd=str(TOOLS_DIR / "opencode"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode == 0
        except Exception as e:
            logger.error(f"OpenCode build error: {e}")
            return False


# ══════════════════════════════════════════════════════════
# 11. Gemini ADK — Google Agent Development Kit
# ══════════════════════════════════════════════════════════

class GeminiADKAdapter(BaseToolAdapter):
    """
    Google ADK — Agent Development Kit
    أدوات مفتوحة لبناء Agents بالبايثون
    """
    name = "GeminiADK"
    tool_dir = "gemini-adk"
    
    async def initialize(self) -> bool:
        self._adk = None
        result = await super().initialize()
        return result
    
    def get_agent_patterns(self) -> Dict[str, str]:
        """أنماط ADK المتاحة"""
        return {
            "sequential_agent": "Steps executed in sequence",
            "parallel_agent": "Steps executed in parallel",
            "loop_agent": "Repeated execution with conditions",
            "llm_agent": "LLM-powered decision making",
            "custom_agent": "User-defined agent logic",
        }


# ══════════════════════════════════════════════════════════
# 12. Agents Course — HuggingFace Educational Resources
# ══════════════════════════════════════════════════════════

class AgentsCourseAdapter(BaseToolAdapter):
    """
    HuggingFace Agents Course — مصادر تعليمية
    دروس وأمثلة لبناء AI Agents
    """
    name = "AgentsCourse"
    tool_dir = "agents-course"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        if result:
            self._units_dir = TOOLS_DIR / "agents-course" / "units"
        return result
    
    def get_units(self) -> List[str]:
        """قائمة الوحدات التعليمية"""
        if self._units_dir and self._units_dir.exists():
            return sorted([d.name for d in self._units_dir.iterdir() if d.is_dir()])
        return []
    
    def get_unit_content(self, unit_name: str) -> str:
        """محتوى وحدة تعليمية"""
        unit_path = self._units_dir / unit_name
        if unit_path.exists():
            for md_file in unit_path.rglob("*.md"):
                return md_file.read_text(errors="ignore")[:2000]
        return ""


# ══════════════════════════════════════════════════════════
# 13. EvoAgentX — Self-Evolving Agent Framework
# ══════════════════════════════════════════════════════════

class EvoAgentXAdapter(BaseToolAdapter):
    """EvoAgentX — إطار تطور ذاتي للـ Agents
    بناء وتقييم وتطوير LLM Agents تلقائياً
    يدعم: Self-Evolution Engine, Workflow Autoconstruction, Built-in Evaluation
    """
    name = "EvoAgentX"
    tool_dir = "EvoAgentX"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        return result
    
    def get_evolution_config(self) -> Dict:
        """إعدادات محرك التطور"""
        config_path = TOOLS_DIR / self.tool_dir / "evoagentx"
        if not config_path.exists():
            return {"error": "EvoAgentX source not found"}
        modules = [f.stem for f in config_path.iterdir() if f.is_file() and f.suffix == '.py']
        return {
            "framework": "EvoAgentX",
            "source_dir": str(config_path),
            "modules": modules,
            "capabilities": [
                "agent_workflow_autoconstruction",
                "built_in_evaluation",
                "self_evolution_engine",
                "plug_and_play_llm",
                "memory_module",
                "human_in_the_loop",
            ]
        }
    
    def get_evolution_algorithms(self) -> List[str]:
        """خوارزميات التطور المدعومة"""
        return [
            "retrieval_augmentation",
            "mutation",
            "guided_search",
            "iterative_feedback_loops",
            "task_specific_evaluation",
        ]


# ══════════════════════════════════════════════════════════
# 14. Agent0 — Zero-Data Self-Evolution
# ══════════════════════════════════════════════════════════

class Agent0Adapter(BaseToolAdapter):
    """Agent0 — تطور ذاتي بدون بيانات بشرية
    Symbiotic Co-Evolution: Curriculum Agent + Executor Agent
    يتطور بدون datasets خارجية
    """
    name = "Agent0"
    tool_dir = "Agent0"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        return result
    
    def get_architecture(self) -> Dict:
        """بنية Agent0 ثنائية الـ Agent"""
        agent0_path = TOOLS_DIR / self.tool_dir / "Agent0"
        if not agent0_path.exists():
            return {"error": "Agent0 source not found"}
        modules = [f.stem for f in agent0_path.iterdir() if f.is_file() and f.suffix == '.py']
        return {
            "framework": "Agent0",
            "dual_agent_system": {
                "curriculum_agent": "يقترح تحديات متصاعدة الصعوبة",
                "executor_agent": "يتعلم حل التحديات باستخدام أدوات خارجية",
            },
            "capabilities": [
                "zero_data_self_evolution",
                "symbiotic_co_evolution",
                "enhanced_reasoning",
                "self_correction",
                "dynamic_feedback",
            ],
            "modules": modules,
        }
    
    def get_evolution_patterns(self) -> List[Dict]:
        """أنماط التطور من Agent0"""
        return [
            {"pattern": "curriculum_generation", "desc": "توليد مناهج تعليمية تصاعدية"},
            {"pattern": "symbiotic_coevolution", "desc": "تطور تكافلي بين agent"},
            {"pattern": "self_repair", "desc": "إصلاح ذاتي للأخطاء المنطقية"},
            {"pattern": "tool_augmented_reasoning", "desc": "استدلال معزز بأدوات"},
        ]


# ══════════════════════════════════════════════════════════
# 15. AI Hedge Fund — Multi-Agent Trading Simulation
# ══════════════════════════════════════════════════════════

class AIHedgeFundAdapter(BaseToolAdapter):
    """AI Hedge Fund — محاكاة تداول متعددة الـ Agents
    12 agent مستوحى من مستثمرين حقيقيين
    Warren Buffett, Charlie Munger, Ben Graham, etc.
    """
    name = "AIHedgeFund"
    tool_dir = "ai-hedge-fund"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        return result
    
    def get_trading_agents(self) -> List[Dict]:
        """قائمة agents التداول المتاحة"""
        return [
            {"name": "Warren Buffett", "style": "value_investing", "desc": "شركات ممتازة بسعر عادل"},
            {"name": "Charlie Munger", "style": "quality_investing", "desc": "أعمال ممتازة بأسعار عادلة"},
            {"name": "Ben Graham", "style": "deep_value", "desc": "شركات مقومة بأقل من قيمتها"},
            {"name": "Bill Ackman", "style": "activist", "desc": "مستثمر نشط بمراكز جريئة"},
            {"name": "Cathie Wood", "style": "growth_disruption", "desc": "إيمان بالابتكار والتغيير"},
            {"name": "Michael Burry", "style": "contrarian", "desc": "صيد القيمة العميقة"},
            {"name": "Peter Lynch", "style": "practical_growth", "desc": "ten-baggers من الأعمال اليومية"},
            {"name": "Stanley Druckenmiller", "style": "macro", "desc": "فرص غير متماثلة"},
            {"name": "Aswath Damodaran", "style": "valuation", "desc": "قصة + أرقام + تقييم منضبط"},
            {"name": "Mohnish Pabrai", "style": "dhandho", "desc": "مضاعفات بمخاطر منخفضة"},
            {"name": "Phil Fisher", "style": "scuttlebutt_growth", "desc": "بحث دقيق في النمو"},
            {"name": "Rakesh Jhunjhunwala", "style": "big_bull", "desc": "ثور الهند الكبير"},
        ]
    
    def get_functional_agents(self) -> List[Dict]:
        """الـ agents الوظيفية (تحليل، مخاطر، محفظة)"""
        return [
            {"name": "Valuation Agent", "role": "حساب القيمة الجوهرية"},
            {"name": "Sentiment Agent", "role": "تحليل المشاعر السوقية"},
            {"name": "Fundamentals Agent", "role": "تحليل البيانات الأساسية"},
            {"name": "Technicals Agent", "role": "تحليل المؤشرات الفنية"},
            {"name": "Risk Manager", "role": "حساب المخاطر وتحديد الحدود"},
            {"name": "Portfolio Manager", "role": "اتخاذ القرارات النهائية"},
        ]
    
    def get_source_modules(self) -> List[str]:
        """ملفات السورس"""
        src_path = TOOLS_DIR / self.tool_dir / "src"
        if not src_path.exists():
            return []
        return [f.name for f in src_path.rglob("*.py")]


# ══════════════════════════════════════════════════════════
# 16. Agent Zero — Self-Correcting Autonomous Agent
# ══════════════════════════════════════════════════════════

class AgentZeroAdapter(BaseToolAdapter):
    """Agent Zero — إطار Agent ذاتي التصحيح
    يستخدم الكمبيوتر كأداة، يكتب كوده، persistent memory
    Multi-agent hierarchy مع streamed terminal output
    """
    name = "AgentZero"
    tool_dir = "agent-zero"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        return result
    
    def get_architecture_insights(self) -> Dict:
        """أنماط معمارية من Agent Zero"""
        root = TOOLS_DIR / self.tool_dir
        # Check for key files
        key_files = ["agent.py", "initialize.py"]
        found = [f for f in key_files if (root / f).exists()]
        agents_dir = root / "agents"
        agent_types = []
        if agents_dir.exists():
            agent_types = [f.stem for f in agents_dir.iterdir() if f.suffix == '.py']
        return {
            "framework": "Agent Zero",
            "key_files": found,
            "agent_types": agent_types,
            "capabilities": [
                "computer_as_tool",
                "self_written_code",
                "terminal_interaction",
                "multi_agent_hierarchy",
                "persistent_memory_with_ai_recall",
                "prompt_based_customization",
                "real_time_streaming",
            ]
        }
    
    def get_prompts(self) -> Dict:
        """استخراج prompts المستخدمة"""
        prompts_dir = TOOLS_DIR / self.tool_dir / "conf"
        if not prompts_dir.exists():
            return {"error": "Prompts directory not found"}
        files = [f.name for f in prompts_dir.rglob("*") if f.is_file()]
        return {"prompt_files": files, "dir": str(prompts_dir)}


# ══════════════════════════════════════════════════════════
# 17. Open-R1 — HuggingFace RL Pipelines
# ══════════════════════════════════════════════════════════

class OpenR1Adapter(BaseToolAdapter):
    """HuggingFace Open-R1 — إعادة إنتاج DeepSeek R1
    أدوات مفتوحة المصدر لتكرار تقنيات RL
    GRPO pipelines، تدريب الكود، reasoning
    """
    name = "OpenR1"
    tool_dir = "open-r1"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        return result
    
    def get_training_scripts(self) -> List[str]:
        """سكربتات التدريب المتاحة"""
        scripts_dir = TOOLS_DIR / self.tool_dir / "scripts"
        if not scripts_dir.exists():
            return []
        return [f.name for f in scripts_dir.rglob("*.py")]
    
    def get_recipes(self) -> List[str]:
        """وصفات التدريب (recipes)"""
        recipes_dir = TOOLS_DIR / self.tool_dir / "recipes"
        if not recipes_dir.exists():
            return []
        return [f.name for f in recipes_dir.rglob("*.yaml")] + \
               [f.name for f in recipes_dir.rglob("*.yml")]
    
    def get_rl_capabilities(self) -> Dict:
        """إمكانيات RL المدعومة"""
        return {
            "techniques": [
                "GRPO (Group Relative Policy Optimization)",
                "DPO (Direct Preference Optimization)",
                "SFT (Supervised Fine-Tuning)",
                "RLHF (RL from Human Feedback)",
            ],
            "targets": ["code_generation", "reasoning", "math"],
            "scripts": self.get_training_scripts(),
            "recipes": self.get_recipes(),
        }


# ══════════════════════════════════════════════════════════
# 18. X-Coder-RL-40k — RL Training Dataset
# ══════════════════════════════════════════════════════════

class XCoderRLAdapter(BaseToolAdapter):
    """X-Coder-RL-40k — داتاسيت RL للبرمجة التنافسية
    40,000 مهمة برمجة مع test cases متحققة
    RLVR training — مكافآت قابلة للتحقق
    """
    name = "XCoderRL"
    tool_dir = "X-Coder-RL-40k"
    
    async def initialize(self) -> bool:
        result = await super().initialize()
        return result
    
    def get_dataset_info(self) -> Dict:
        """معلومات عن الداتاسيت"""
        root = TOOLS_DIR / self.tool_dir
        syn_data = root / "syn_rl_data"
        real_data = root / "real_rl_data"
        
        syn_files = list(syn_data.rglob("*.parquet")) if syn_data.exists() else []
        real_files = list(real_data.rglob("*.parquet")) if real_data.exists() else []
        
        return {
            "dataset": "X-Coder-RL-40k",
            "total_tasks": 40000,
            "type": "RLVR (Reinforcement Learning from Verifiable Rewards)",
            "synthetic_files": [f.name for f in syn_files],
            "real_files": [f.name for f in real_files],
            "total_files": len(syn_files) + len(real_files),
            "categories": ["competitive_programming", "leetcode", "codeforces", "taco"],
            "difficulty_levels": ["easiest", "easy", "medium", "hard", "hardest"],
        }
    
    def get_training_config(self) -> Dict:
        """إعدادات التدريب الموصى بها"""
        return {
            "training_paradigm": "RLVR",
            "stages": [
                {"stage": 1, "method": "SFT", "desc": "Supervised Fine-Tuning أولاً"},
                {"stage": 2, "method": "RL", "desc": "Reinforcement Learning مع مكافآت"},
            ],
            "verifier": "unit_test_execution",
            "reward_signal": "pass/fail on test cases",
            "compatible_with": ["VERL", "OpenR1", "TRL"],
        }


# ══════════════════════════════════════════════════════════
# Tools Hub — المركز الموحد (18 أداة)
# ══════════════════════════════════════════════════════════

class ToolsHub:
    """
    مركز تكامل الأدوات الخارجية مع NOOGH
    ═══════════════════════════════════════
    Singleton يربط 18 أداة AI بنظام NOOGH الموحد
    """
    
    def __init__(self):
        # === Original 12 ===
        self.shannon = ShannonAdapter()
        self.smolagents = SmolAgentsAdapter()
        self.mem0 = Mem0Adapter()
        self.langchain = LangChainAdapter()
        self.verl = VERLAdapter()
        self.composio = ComposioAdapter()
        self.autogpt = AutoGPTAdapter()
        self.openhands = OpenHandsAdapter()
        self.aider = AiderAdapter()
        self.opencode = OpenCodeAdapter()
        self.gemini_adk = GeminiADKAdapter()
        self.agents_course = AgentsCourseAdapter()
        
        # === New 6 (Feb 2026) ===
        self.evoagentx = EvoAgentXAdapter()
        self.agent0 = Agent0Adapter()
        self.ai_hedge_fund = AIHedgeFundAdapter()
        self.agent_zero = AgentZeroAdapter()
        self.open_r1 = OpenR1Adapter()
        self.xcoder_rl = XCoderRLAdapter()
        
        self._initialized = False
        self._adapters = {
            # Original 12
            "shannon": self.shannon,
            "smolagents": self.smolagents,
            "mem0": self.mem0,
            "langchain": self.langchain,
            "verl": self.verl,
            "composio": self.composio,
            "autogpt": self.autogpt,
            "openhands": self.openhands,
            "aider": self.aider,
            "opencode": self.opencode,
            "gemini_adk": self.gemini_adk,
            "agents_course": self.agents_course,
            # New 6
            "evoagentx": self.evoagentx,
            "agent0": self.agent0,
            "ai_hedge_fund": self.ai_hedge_fund,
            "agent_zero": self.agent_zero,
            "open_r1": self.open_r1,
            "xcoder_rl": self.xcoder_rl,
        }
    
    async def initialize(self) -> Dict[str, bool]:
        """تهيئة جميع الأدوات"""
        logger.info("🔧 ToolsHub: Initializing all adapters...")
        results = {}
        
        # Initialize all adapters in parallel
        tasks = {
            name: adapter.initialize() 
            for name, adapter in self._adapters.items()
        }
        
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                results[name] = False
                logger.error(f"❌ {name} init error: {e}")
        
        available = sum(1 for v in results.values() if v)
        total = len(results)
        
        logger.info(f"🔧 ToolsHub initialized: {available}/{total} adapters available")
        self._initialized = True
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """حالة جميع الأدوات"""
        return {
            "initialized": self._initialized,
            "tools_dir": str(TOOLS_DIR),
            "adapters": {
                name: adapter.status() 
                for name, adapter in self._adapters.items()
            }
        }
    
    def get_adapter(self, name: str) -> Optional[BaseToolAdapter]:
        """الحصول على adapter بالاسم"""
        return self._adapters.get(name)
    
    def list_available(self) -> List[str]:
        """قائمة الأدوات المتاحة"""
        return [name for name, adapter in self._adapters.items() 
                if adapter.available]
    
    async def run_security_audit(self, target_path: str = None) -> Dict:
        """
        تشغيل فحص أمني شامل باستخدام Shannon
        """
        if target_path is None:
            target_path = "/home/noogh/projects/noogh_unified_system/src"
        
        results = await self.shannon.scan_project(target_path)
        report = self.shannon.get_report(results)
        
        logger.info(f"🔒 Security audit complete: {len(results.get('vulnerabilities', []))} findings")
        return {
            "results": results,
            "report": report,
        }
    
    async def get_architecture_insights(self) -> Dict[str, Any]:
        """
        استخراج أنماط معمارية من كل الأدوات
        لتحسين بنية NOOGH
        """
        insights = {}
        
        if self.autogpt.available:
            insights["autogpt"] = self.autogpt.get_architecture_insights()
        
        if self.openhands.available:
            insights["openhands"] = self.openhands.get_agent_patterns()
        
        if self.gemini_adk.available:
            insights["gemini_adk"] = self.gemini_adk.get_agent_patterns()
        
        if self.verl.available:
            insights["verl_algorithms"] = self.verl.get_algorithms()
        
        if self.langchain.available:
            insights["langchain_modules"] = self.langchain.get_available_modules()
        
        if self.agents_course.available:
            insights["course_units"] = self.agents_course.get_units()
        
        # === New tools insights ===
        if self.evoagentx.available:
            insights["evoagentx"] = self.evoagentx.get_evolution_config()
        
        if self.agent0.available:
            insights["agent0"] = self.agent0.get_architecture()
        
        if self.ai_hedge_fund.available:
            insights["ai_hedge_fund"] = {
                "trading_agents": self.ai_hedge_fund.get_trading_agents(),
                "functional_agents": self.ai_hedge_fund.get_functional_agents(),
            }
        
        if self.agent_zero.available:
            insights["agent_zero"] = self.agent_zero.get_architecture_insights()
        
        if self.open_r1.available:
            insights["open_r1"] = self.open_r1.get_rl_capabilities()
        
        if self.xcoder_rl.available:
            insights["xcoder_rl"] = self.xcoder_rl.get_dataset_info()
        
        return insights
    
    def summary(self) -> str:
        """ملخص مقروء لحالة الأدوات"""
        lines = [
            "╔══════════════════════════════════════════════╗",
            "║     🔧 NOOGH Tools Hub — 18 Tools Status     ║",
            "╠══════════════════════════════════════════╣",
        ]
        
        for name, adapter in self._adapters.items():
            icon = "✅" if adapter.available else "❌"
            lines.append(f"║  {icon} {adapter.name:<20} {'READY' if adapter.available else 'UNAVAILABLE':>10}  ║")
        
        available = len(self.list_available())
        lines.append("╠══════════════════════════════════════════╣")
        lines.append(f"║  Total: {available}/{len(self._adapters)} adapters available        ║")
        lines.append("╚══════════════════════════════════════════╝")
        
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# Singleton
# ══════════════════════════════════════════════════════════

_hub_instance: Optional[ToolsHub] = None


def get_tools_hub() -> ToolsHub:
    """الحصول على مثيل ToolsHub (Singleton)"""
    global _hub_instance
    if _hub_instance is None:
        _hub_instance = ToolsHub()
    return _hub_instance
