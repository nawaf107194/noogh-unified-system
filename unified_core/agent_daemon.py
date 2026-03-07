# unified_core/agent_daemon.py
"""
Autonomous Agent Daemon - Modular Refactored Version v5.1
System Rebuilt from Ground Up — Now with Cognitive Journal
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

# v21: Load .env so RunPod/DeepSeek API keys and URLs are available
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_path, override=False)
except ImportError:
    pass  # dotenv not required if env vars are set externally

# Configure logging
logging.basicConfig(level=logging.INFO)
from .evolution.controller import get_evolution_controller
from .evolution.evolution_triggers import EvolutionTriggerSystem
from .cognitive_journal import get_cognitive_journal
try:
    from .evolution.project_analyzer import get_project_analyzer
except ImportError:
    get_project_analyzer = None

logger = logging.getLogger("unified_core.agent_daemon")

class CoreLoop:
    """الحلقة الأساسية المنفصلة"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.handlers = []
        self.running = False
        
    def add_handler(self, name: str, handler_func):
        """إضافة معالج لدورة"""
        self.handlers.append((name, handler_func))
        logger.info(f"Added handler: {name}")
        
    async def run(self):
        """تشغيل الحلقة"""
        self.running = True
        cycle_count = 0
        
        while self.running:
            cycle_start = time.time()
            cycle_count += 1
            
            logger.info(f"=== CYCLE {cycle_count} ===")
            
            # تنفيذ جميع المعالجات بشكل متوازي
            tasks = []
            for name, handler in self.handlers:
                task = asyncio.create_task(
                    self._safe_handler(name, handler, cycle_count)
                )
                tasks.append(task)
            
            # انتظار اكتمال جميع المهام
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # حساب الوقت المتبقي
            elapsed = time.time() - cycle_start
            sleep_time = max(0, self.interval - elapsed)
            
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                
    async def _safe_handler(self, name: str, handler, cycle_count: int):
        """تنفيذ معالج بأمان"""
        try:
            start = time.time()
            if cycle_count % 10 == 0:
                logger.info(f"  ▶ {name} START (cycle {cycle_count})")
            if asyncio.iscoroutinefunction(handler):
                await handler(cycle_count)
            else:
                handler(cycle_count)
            elapsed = time.time() - start
            if cycle_count % 10 == 0 or elapsed > 5:
                logger.info(f"  ✅ {name} DONE ({elapsed:.1f}s)")
        except Exception as e:
            logger.error(f"Handler '{name}' failed: {e}")

class ComponentManager:
    """مدير المكونات الديناميكي"""
    
    def __init__(self):
        self.components = {}
        self.dependencies = {}
        
    def register(self, name: str, component, depends_on: list = None):
        """تسجيل مكون جديد"""
        self.components[name] = component
        self.dependencies[name] = depends_on or []
        logger.info(f"Registered component: {name}")
        
    async def initialize_all(self):
        """تهيئة جميع المكونات مع مراعاة الاعتماديات"""
        # فرز طوبولوجي للاعتماديات
        order = self._topological_sort()
        
        for name in order:
            if hasattr(self.components[name], 'initialize'):
                logger.info(f"Initializing: {name}")
                try:
                    if asyncio.iscoroutinefunction(self.components[name].initialize):
                        await self.components[name].initialize()
                    else:
                        self.components[name].initialize()
                except Exception as e:
                    logger.error(f"Failed to initialize {name}: {e}")
                    
    def _topological_sort(self):
        """الفرز الطوبولوجي للاعتماديات"""
        visited = set()
        stack = []
        
        def visit(component):
            if component not in visited:
                visited.add(component)
                for dep in self.dependencies.get(component, []):
                    if dep in self.components:
                        visit(dep)
                stack.append(component)
                
        for component in self.components:
            visit(component)
            
        return stack

class AgentDaemon:
    """النسخة المعيارية من الوكيل المستقل"""
    
    def __init__(self):
        self.loop = CoreLoop(interval=2.0)
        self.components = ComponentManager()
        self.state = "initializing"
        self.evolution_triggers = EvolutionTriggerSystem()  # v3.0
        self._loaded_agents = {}  # v3.4: Dynamically loaded agents
        
    async def initialize(self):
        """التهيئة المعيارية"""
        logger.info("🚀 AgentDaemon Modular v5.0 Initializing...")
        
        # تسجيل المكونات الأساسية
        await self._register_core_components()
        
        # تهيئة المكونات
        await self.components.initialize_all()
        
        # إضافة معالجات الحلقة
        await self._setup_loop_handlers()
        
        # v3.4: Auto-discover and load generated agents
        await self._discover_and_load_agents()
        
        self.state = "running"
        logger.info("✅ AgentDaemon initialized successfully")
        
    async def _register_core_components(self):
        """تسجيل المكونات الأساسية"""
        # WorldModel
        from unified_core.core.world_model import WorldModel
        world_model = WorldModel()
        self.components.register("world_model", world_model)
        
        # Observation Stream
        from unified_core.core.observation_stream import ObservationStream
        obs_stream = ObservationStream(world_model)
        self.components.register("observation_stream", obs_stream, ["world_model"])
        
        # Task Dispatcher
        from unified_core.task_dispatcher import TaskDispatcher
        dispatcher = TaskDispatcher(world_model)
        self.components.register("task_dispatcher", dispatcher, ["world_model"])
        
        # Planning Engine
        from unified_core.core.planning_engine import PlanningEngine
        planner = PlanningEngine(world_model, dispatcher)
        self.components.register("planning_engine", planner, ["world_model", "task_dispatcher"])
        
        # Meta Governor
        from unified_core.core.meta_governor import MetaGovernor
        governor = MetaGovernor(self)
        self.components.register("meta_governor", governor)
        
        # Security Hardener
        from unified_core.core.security_hardening import EnhancedSecurityHardener
        security = EnhancedSecurityHardener()
        self.components.register("security_hardener", security)
        
        # Wire ASAA & AMLA to real WorldModel memory store
        try:
            from unified_core.core.asaa import get_asaa
            from unified_core.core.amla import get_amla
            
            asaa = get_asaa()
            amla = get_amla()
            
            # Pass real memory store (has sync methods _get_belief_sync, etc.)
            asaa.set_belief_store(world_model._memory)
            amla.set_belief_store(world_model._memory)
            amla.set_advisory_memory(world_model._memory)
            amla.set_asaa(asaa)
            
            self.components.register("asaa", asaa)
            self.components.register("amla", amla, ["world_model"])
            logger.info("🛡️ ASAA + AMLA wired to real WorldModel memory store")
        except Exception as e:
            logger.warning(f"ASAA/AMLA wiring skipped: {e}")
        
        # Intent Injector
        from .intent_injector import IntelligentIntentInjector
        intent_injector = IntelligentIntentInjector()
        self.components.register("intent_injector", intent_injector)
        
        # Noogh Wisdom
        from .noogh_wisdom import AdvancedNooghWisdom
        wisdom = AdvancedNooghWisdom()
        self.components.register("noogh_wisdom", wisdom)
        
        # Evolution Controller
        from .evolution.controller import get_evolution_controller
        evolution = get_evolution_controller()
        self.components.register("evolution", evolution)
        
        # Cognitive Journal — persistent memory (Windsurf pattern)
        journal = get_cognitive_journal()
        self.components.register("cognitive_journal", journal)
        journal.record("observation", "Daemon v5.1 initialized", cycle=0, tags=["startup"])
        
        # v3.0: Wire cognitive components to evolution
        evolution.set_journal(journal)
        evolution.set_world_model(world_model)
        self.evolution_triggers.set_journal(journal)
        self.evolution_triggers.set_world_model(world_model)

        # v5.2: Trading Agent — Autonomous Paper Trading
        try:
            from agents.autonomous_trading_agent import AutonomousTradingAgent
            from .neural_bridge import NeuralEngineClient

            # v21: Initialize Neural Bridge — reads URL from NEURAL_ENGINE_URL env
            # DeepSeek R1 API (primary) or local Ollama (fallback)
            neural_bridge = NeuralEngineClient(
                mode="vllm"  # vllm mode uses OpenAI-compatible /v1/chat/completions
            )

            trading_agent = AutonomousTradingAgent(
                neural_bridge=neural_bridge,
                mode='hybrid'  # Hybrid: Live trading ONLY at 100% confidence
            )
            self.components.register("trading_agent", trading_agent)
            logger.info("🤖 Trading Agent registered (Hybrid Mode: Live @ 100% confidence)")
        except Exception as e:
            logger.warning(f"⚠️ Trading Agent registration failed: {e}")
            
        # CodeExecutor Agent - System execution capability enabling pip installs and file edits natively
        try:
            from agents.code_executor_agent import CodeExecutorAgent
            code_agent = CodeExecutorAgent()
            # Start the agent listening loop in the background (start is synchronous but spawns async tasks)
            code_agent.start()
            self.components.register("code_executor_agent", code_agent)
            logger.info("🛠️ CodeExecutorAgent background process spawned for dynamic Task Execution")
        except Exception as e:
            logger.warning(f"⚠️ CodeExecutorAgent registration failed: {e}")
        
        # Wire ConsequenceEngine if available
        try:
            from unified_core.core.consequence import ConsequenceEngine
            consequence_engine = ConsequenceEngine()
            evolution.set_consequence_engine(consequence_engine)
        except Exception as e:
            logger.debug(f"ConsequenceEngine wiring skipped: {e}")
        
        # Wire ScarTissue/FailureRecord if available
        try:
            from unified_core.core.scar import FailureRecord
            scars = FailureRecord()
            evolution.set_scar_tissue(scars)
        except Exception as e:
            logger.debug(f"FailureRecord wiring skipped: {e}")
        
        # NeuronFabric — الشبكة العصبية السيادية
        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric, seed_initial_neurons
            neuron_fabric = get_neuron_fabric()
            seed_initial_neurons(neuron_fabric)  # يزرع العصبونات الأولية لو فارغة
            self.components.register("neuron_fabric", neuron_fabric)
            self._neuron_fabric = neuron_fabric
            logger.info(f"🧬 NeuronFabric wired: {neuron_fabric.get_stats()['total_neurons']} neurons")
        except Exception as e:
            logger.warning(f"NeuronFabric initialization skipped: {e}")
            self._neuron_fabric = None
        
        # LinuxIntelligence — فهم النظام
        try:
            from unified_core.core.linux_intelligence import get_linux_intelligence
            self._linux_intel = get_linux_intelligence(auto_fix=True)
            self.components.register("linux_intelligence", self._linux_intel)
            logger.info("🐧 LinuxIntelligence wired (auto_fix=ON)")
        except Exception as e:
            logger.warning(f"LinuxIntelligence initialization skipped: {e}")
            self._linux_intel = None
        
        # SpatialSpecialist — فهم بنية المشروع
        try:
            from unified_core.core.spatial_specialist import SpatialSpecialist
            spatial = SpatialSpecialist(
                root_path="/home/noogh/projects/noogh_unified_system/src"
            )
            spatial_map = await spatial.generate_map()
            self.components.register("spatial_specialist", spatial)
            
            # Wire to ObservationStream
            obs_stream.set_components(spatial_specialist=spatial)
            
            # Feed spatial beliefs to WorldModel
            beliefs = spatial.get_spatial_belief_propositions()
            if beliefs:
                for belief in beliefs[:10]:  # Top 10 beliefs
                    try:
                        await world_model.add_belief(belief, initial_confidence=0.85)
                    except Exception:
                        pass
            
            logger.info(f"🗺️ SpatialSpecialist wired: {len(spatial_map.get('nodes', []))} nodes mapped")
        except Exception as e:
            logger.warning(f"SpatialSpecialist initialization skipped: {e}")
        
        # ToolsHub — 12 أداة AI خارجية مدمجة
        try:
            from unified_core.tools_hub import get_tools_hub
            self._tools_hub = get_tools_hub()
            hub_results = await self._tools_hub.initialize()
            available = sum(1 for v in hub_results.values() if v)
            self.components.register("tools_hub", self._tools_hub)
            logger.info(f"🔧 ToolsHub wired: {available}/{len(hub_results)} adapters available")
        except Exception as e:
            logger.warning(f"ToolsHub initialization skipped: {e}")
            self._tools_hub = None
        
        logger.info("🧬 Evolution v3.0 cognitive wiring complete")
        
        # AgentOrchestrator — wires agents to the loop via MessageBus
        try:
            from unified_core.orchestration.agent_orchestrator import get_agent_orchestrator
            self._agent_orchestrator = get_agent_orchestrator()
            self.components.register("agent_orchestrator", self._agent_orchestrator)
            logger.info("🔌 AgentOrchestrator wired — agents will receive tasks")
        except Exception as e:
            logger.warning(f"AgentOrchestrator initialization skipped: {e}")
            self._agent_orchestrator = None
        
    async def _setup_loop_handlers(self):
        """إعداد معالجات الحلقة"""
        # مراقبة النظام
        self.loop.add_handler("system_monitor", self._monitor_system)
        
        # معالجة النوايا
        self.loop.add_handler("intent_processor", self._process_intents)
        
        # المراقبة الأمنية
        self.loop.add_handler("security_monitor", self._monitor_security)
        
        # توليد الأهداف
        self.loop.add_handler("goal_generator", self._generate_goals)
        
        # حكمة التداول
        self.loop.add_handler("wisdom_cycle", self._run_wisdom_cycle)
        
        # حلقة التطور الذكائي
        self.loop.add_handler("evolution_cycle", self._run_evolution_cycle)
        
        # حلقة الشبكة العصبية
        self.loop.add_handler("neuron_cycle", self._run_neuron_cycle)
        
        # فحص صحة لينكس
        self.loop.add_handler("linux_health", self._run_linux_health)
        
        # v3.4: Hot-reload وكلاء جدد (كل 50 دورة)
        self.loop.add_handler("agent_hot_reload", self._hot_reload_agents)
        
        # v20: Orchestrator — يوزّع مهام على الوكلاء
        self.loop.add_handler("agent_orchestrator", self._run_agent_orchestrator)

        # v5.2: Trading Agent — Paper Trading Cycle
        self.loop.add_handler("trading_cycle", self._run_trading_cycle)
    
    async def _discover_and_load_agents(self):
        """v3.4: Auto-discover and load generated agents from registry.
        
        Reads agents/agent_registry.json, dynamically imports each agent module,
        instantiates the class, and calls .start() to subscribe to MessageBus.
        """
        import importlib
        import json
        from pathlib import Path
        
        agents_dir = Path(__file__).parent.parent / "agents"
        registry_path = agents_dir / "agent_registry.json"
        
        if not registry_path.exists():
            logger.debug("No agent_registry.json found — skipping agent discovery")
            return
        
        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read agent registry: {e}")
            return
        
        loaded = 0
        for entry in registry:
            agent_name = entry.get("name", "Unknown")
            role = entry.get("role", "unknown")
            file_path = entry.get("file", "")
            
            # Skip if already loaded
            if role in self._loaded_agents:
                continue
            try:
                # Dynamic import using file path directly
                if not Path(file_path).is_absolute():
                    file_path = str(Path(__file__).parent.parent / file_path)

                if not Path(file_path).exists():
                    logger.warning(f"🤖 Agent file not found: {file_path} — skipping")
                    continue

                module_name = Path(file_path).stem
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None or spec.loader is None:
                    logger.warning(f"🤖 Failed to create spec for {file_path}")
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                
                # Use a separate thread for exec_module to avoid blocking if possible, 
                # but careful with sys.modules
                spec.loader.exec_module(module)

                # Find the agent class
                agent_class = getattr(module, agent_name, None)
                if agent_class is None:
                    # Fallback: find any class ending with "Agent"
                    for attr_name in dir(module):
                        obj = getattr(module, attr_name)
                        if isinstance(obj, type) and attr_name.endswith("Agent") and attr_name != "AgentWorker":
                            agent_class = obj
                            break
                
                if agent_class is None:
                    logger.warning(f"🤖 No agent class found in {module_name} — skipping")
                    continue
                
                # Instantiate
                try:
                    agent = agent_class()
                except TypeError:
                    # Try with neural_bridge if possible
                    try:
                        bridge = self.components.components.get("neural_bridge")
                        agent = agent_class(neural_bridge=bridge)
                    except Exception:
                        logger.warning(f"🤖 Failed to instantiate {agent_class.__name__} (missing arguments)")
                        continue

                # Start the agent (Support sync/async start/initialize)
                started = False
                for method_name in ["start", "initialize"]:
                    method = getattr(agent, method_name, None)
                    if method:
                        if asyncio.iscoroutinefunction(method):
                            await method()
                        else:
                            method()
                        started = True
                        break
                
                if not started:
                    logger.info(f"🤖 Agent {agent_class.__name__} has no start/initialize method — registering as passive component")

                # Register as component & loaded agent
                self._loaded_agents[role] = {
                    "instance": agent,
                    "class": agent_class.__name__,
                    "file": file_path
                }
                
                # Also register in component manager if not already there
                if not self.components.components.get(role):
                    self.components.register(role, agent)

                loaded += 1
                logger.info(f"🤖 Agent loaded and started: {agent_class.__name__} [{role}]")

            except Exception as e:
                logger.error(f"❌ Failed to load agent {agent_name} from {file_path}: {e}", exc_info=True)
        
        if loaded > 0:
            logger.warning(f"🏭 Agent discovery complete: {loaded} agents loaded")
        else:
            logger.debug("No new agents to load")
    
    async def _hot_reload_agents(self, cycle: int):
        """v3.4: Periodically check for new agents and load them.
        
        Runs every 50 cycles (~100 seconds). Calls _discover_and_load_agents
        which skips already-loaded agents automatically.
        """
        if cycle % 50 != 0:
            return
        
        try:
            before = len(self._loaded_agents)
            await self._discover_and_load_agents()
            after = len(self._loaded_agents)
            
            if after > before:
                logger.warning(
                    f"🔄 Hot-reload: {after - before} new agent(s) loaded "
                    f"(total: {after})"
                )
        except Exception as e:
            logger.debug(f"Agent hot-reload check failed: {e}")
        
    async def _run_agent_orchestrator(self, cycle: int):
        """v20: Dispatch scheduled tasks to agents via MessageBus."""
        if not self._agent_orchestrator:
            return
        try:
            await self._agent_orchestrator.tick(cycle)
        except Exception as e:
            logger.error(f"🔌 AgentOrchestrator tick failed: {e}")

    async def _monitor_system(self, cycle: int):
        """مراقبة النظام الحقيقية — CPU, الذاكرة, القرص, GPU, الجسر العصبي"""
        if cycle % 10 == 0:
            try:
                import psutil
                import shutil
                
                # CPU + Memory + Disk
                cpu = psutil.cpu_percent(interval=0.5)
                mem = psutil.virtual_memory()
                disk = shutil.disk_usage("/")
                
                # GPU check (nvidia-smi)
                gpu_info = await self._check_gpu()
                
                # Neural engine health — v21: use requests for HTTPS (aiohttp hangs on RunPod proxy)
                neural_alive = False
                neural_mode = "unknown"
                try:
                    import os as _os
                    import requests as _requests
                    _teacher_url = _os.getenv("NOOGH_TEACHER_URL")
                    _neural_url = _os.getenv("NEURAL_ENGINE_URL", "http://127.0.0.1:8002")
                    _neural_mode = _os.getenv("NEURAL_ENGINE_MODE", "local")
                    neural_mode = _neural_mode
                    
                    # Try Teacher first (local Ollama)
                    if _teacher_url:
                        try:
                            r = _requests.get(f"{_teacher_url}/v1/models", timeout=3)
                            neural_alive = r.status_code == 200
                        except Exception:
                            pass
                    # Fallback to main Neural Engine URL
                    if not neural_alive:
                        try:
                            check_url = f"{_neural_url}/v1/models" if _neural_mode == "vllm" else f"{_neural_url}/health"
                            r = _requests.get(check_url, timeout=5)
                            neural_alive = r.status_code == 200
                        except Exception:
                            pass
                except Exception:
                    pass
                
                health = {
                    "cpu_percent": cpu,
                    "memory_percent": mem.percent,
                    "memory_used_gb": round(mem.used / (1024**3), 1),
                    "memory_total_gb": round(mem.total / (1024**3), 1),
                    "disk_free_gb": round(disk.free / (1024**3), 1),
                    "disk_percent": round(disk.used / disk.total * 100, 1),
                    "neural_alive": neural_alive,
                    "gpu": gpu_info,
                    "cycle": cycle,
                    "timestamp": time.time()
                }
                
                # Store in WorldModel (Windsurf pattern: proactive memory)
                world_model = self.components.components.get("world_model")
                if world_model and hasattr(world_model, 'update_belief'):
                    world_model.update_belief("system_health", health)
                
                # Alert thresholds
                alerts = []
                if cpu > 85:
                    alerts.append(f"⚠️ CPU HIGH: {cpu}%")
                if mem.percent > 80:
                    alerts.append(f"⚠️ MEMORY HIGH: {mem.percent}%")
                if disk.free < 5 * (1024**3):
                    alerts.append(f"⚠️ DISK LOW: {health['disk_free_gb']}GB free")
                if not neural_alive:
                    alerts.append("⚠️ NEURAL ENGINE OFFLINE")
                
                if alerts:
                    for alert in alerts:
                        logger.warning(alert)
                else:
                    logger.info(f"📊 System OK | CPU:{cpu}% MEM:{mem.percent}% DISK:{health['disk_free_gb']}GB Neural:{'✅' if neural_alive else '❌'}")
                
                # Record to CognitiveJournal
                journal = self.components.components.get("cognitive_journal")
                if journal:
                    if alerts:
                        journal.record("observation", f"System alerts: {'; '.join(alerts)}",
                                      context=health, confidence=0.9, cycle=cycle,
                                      tags=["monitor", "alert"])
                    elif cycle % 50 == 0:  # Full snapshot every 50 cycles
                        journal.record("observation",
                                      f"System healthy: CPU:{cpu}% MEM:{mem.percent}% Neural:{'✅' if neural_alive else '❌'}",
                                      context=health, confidence=0.95, cycle=cycle,
                                      tags=["monitor", "snapshot"])
                
                # Feed observations to NeuronFabric
                if self._neuron_fabric and cycle % 20 == 0:
                    try:
                        from unified_core.core.neuron_fabric import NeuronType
                        # إنشاء عصبون حسّي من الملاحظة
                        obs_text = f"CPU:{cpu}% RAM:{mem.percent}% Neural:{'ON' if neural_alive else 'OFF'} @cycle{cycle}"
                        sensory = self._neuron_fabric.create_neuron(
                            proposition=obs_text,
                            neuron_type=NeuronType.SENSORY,
                            confidence=0.7,
                            domain="monitoring",
                            tags=["system", "observation", "auto"],
                            energy=0.6,
                        )
                        self._neuron_fabric.auto_connect(sensory.neuron_id, max_connections=3)
                        
                        # 🔥 تنشيط العصبونات دائماً — مش بس لما CPU عالي
                        activated = self._neuron_fabric.activate_by_query(
                            f"مراقبة CPU RAM Neural نظام", top_k=5
                        )
                        
                        # تنشيط إضافي لو فيه ضغط
                        if cpu > 50 or mem.percent > 65:
                            stress_activated = self._neuron_fabric.activate_by_query(
                                "ضغط عالي GPU مورد ثمين حماية", top_k=3
                            )
                            if stress_activated:
                                logger.debug(f"🧠 Stress neurons fired: {len(stress_activated)}")
                        
                        # تنشيط لو Neural Engine مطفي
                        if not neural_alive:
                            self._neuron_fabric.activate_by_query(
                                "Neural Engine الدماغ بدونه لا تفكير", top_k=3
                            )
                    except Exception:
                        pass
                    
            except ImportError:
                logger.warning("📊 psutil not installed — monitoring limited")
            except Exception as e:
                logger.error(f"📊 Monitor error: {e}")

    async def _check_gpu(self) -> dict:
        """فحص حالة GPU عبر nvidia-smi"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "nvidia-smi", "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
            if proc.returncode == 0 and stdout:
                parts = stdout.decode().strip().split(", ")
                if len(parts) >= 4:
                    return {
                        "temp_c": int(parts[0]),
                        "util_percent": int(parts[1]),
                        "mem_used_mb": int(parts[2]),
                        "mem_total_mb": int(parts[3]),
                        "available": True
                    }
        except Exception:
            pass
        return {"available": False}
            
    async def _process_intents(self, cycle: int):
        """معالجة النوايا النشطة والرد عليها"""
        if cycle % 5 == 0:
            injector = self.components.components.get("intent_injector")
            if not injector:
                return
                
            intents = injector.get_active_intents()
            if not intents:
                return
                
            logger.info(f"📋 Processing {len(intents)} active intents")
            for intent in intents:
                intent_type = intent.get('intent_type')
                
                # Logic for reacting to specific intents
                if intent_type == "WISDOM_CHECK":
                    logger.info(f"🎯 Intent Trigger: Manual Wisdom Check Requested")
                    await self._run_wisdom_cycle(cycle, force=True)
                    injector.mark_completed(intent['id'])
                
                elif intent_type == "SECURITY_SCAN":
                    logger.info(f"🛡️ Intent Trigger: Manual Security Scan Requested")
                    await self._monitor_security(cycle, force=True)
                    injector.mark_completed(intent['id'])

    async def _monitor_security(self, cycle: int, force: bool = False):
        """المراقبة الأمنية"""
        if force or cycle % 30 == 0:
            security = self.components.components.get("security_hardener")
            if security:
                await security.run_full_audit()
                
    async def _generate_goals(self, cycle: int):
        """توليد الأهداف"""
        if cycle % 20 == 0:
            planner = self.components.components.get("planning_engine")
            if planner:
                await planner.generate_goals_from_intents()
                
                # Phase 22: Link GravityWell goals to PlanningEngine
                try:
                    from unified_core.bridge import get_bridge
                    bridge = get_bridge()
                    if hasattr(bridge, '_gravity_well') and bridge._gravity_well:
                        active_goals = bridge._gravity_well.get_active_goals()
                        for goal_id, goal in active_goals.items():
                            # Ensure we don't duplicate active plans
                            existing = [
                                p for p in planner.get_active_plans() 
                                if goal.description in p.get("goal", "")
                            ]
                            if not existing:
                                logger.info(f"📍 HIGH PRIORITY GOAL: Submitting GravityWell goal: {goal.description}")
                                await planner.propose_synthetic_goal(
                                    goal.description, 
                                    source="GravityWell", 
                                    priority="high"
                                )
                except Exception as e:
                    logger.warning(f"Failed to harvest GravityWell goals: {e}")
                
    async def _run_wisdom_cycle(self, cycle: int, force: bool = False):
        """دورة الحكمة"""
        if force or cycle % 20 == 0:  # Every ~3 min (was 60)
            wisdom = self.components.components.get("noogh_wisdom")
            if wisdom:
                await wisdom.run_advanced_analysis()
                
    async def _run_evolution_cycle(self, cycle: int):
        """دورة التطور المعرفي v3.0 (بالتحفيز الذكي + ربط عصبي)"""
        # Check triggers every 10 cycles (~20s at 2s interval) — lightweight
        if cycle % 10 == 0:
            try:
                # v21: Timeout to prevent infinite blocking (Ollama brain can hang)
                await asyncio.wait_for(
                    self._run_evolution_inner(cycle),
                    timeout=300  # 5 minutes max (DeepSeek brain calls ~45s each)
                )
            except asyncio.TimeoutError:
                logger.warning("⚠️ Evolution cycle timed out (>300s) — skipping")
            except Exception as e:
                logger.error(f"Evolution cycle error: {e}")
    
    async def _run_evolution_inner(self, cycle: int):
        """Inner evolution logic (can be timed out)."""
        logger.info("  📍 evolution_inner: getting evolution component")
        evolution = self.components.components.get("evolution")
        if not evolution:
            logger.info("  📍 evolution_inner: no evolution, returning")
            return
        
        journal = self.components.components.get("cognitive_journal")
        
        try:
            # 🧠 تنشيط عصبونات التطور قبل القرار
            pre_activation = {}
            if self._neuron_fabric:
                logger.info("  📍 evolution_inner: activating neuron fabric")
                pre_activation = self._neuron_fabric.activate_by_query(
                    "التطور الذاتي Canary Test كود جديد تحسين", top_k=5
                )
                logger.info(f"  📍 evolution_inner: neuron activation done ({len(pre_activation)} neurons)")
            
            # Check all triggers
            logger.info("  📍 evolution_inner: checking triggers")
            events = await self.evolution_triggers.check_all()
            logger.info(f"  📍 evolution_inner: triggers done ({len(events)} events)")
            
            if events:
                logger.info(f"🎯 {len(events)} evolution trigger(s) fired")
                
                for event in events:
                    try:
                        cycle_start = time.time()
                        result = await evolution.handle_trigger(event)
                        cycle_duration = time.time() - cycle_start
                        
                        # v5.1: Feed cycle duration to adaptive scheduler
                        self.evolution_triggers.report_cycle_duration(cycle_duration)
                        
                        # 🧠 تعلم هبّي من نتائج التطور
                        promoted = result.get("promoted", 0) if isinstance(result, dict) else 0
                        processed = result.get("processed", 0) if isinstance(result, dict) else 0
                        
                        if self._neuron_fabric and pre_activation:
                            if promoted > 0:
                                # نجاح → قوّي الوصلات
                                self._neuron_fabric.learn_from_outcome(
                                    pre_activation, success=True, impact=0.8
                                )
                                logger.info(f"🧠 Hebbian: {len(pre_activation)} neurons reinforced (promoted={promoted})")
                            elif processed > 0 and promoted == 0:
                                # جرّب بس ما نجح → ضعّف قليل
                                self._neuron_fabric.learn_from_outcome(
                                    pre_activation, success=False, impact=0.3
                                )
                        
                        if journal:
                            journal.record(
                                "success",
                                f"Evolution trigger handled: {event.trigger_type.value}",
                                context={"trigger": event.to_dict(), "result_status": result.get('status') if isinstance(result, dict) else 'ok'},
                                confidence=0.85, cycle=cycle,
                                tags=["evolution", "trigger", event.trigger_type.value]
                            )
                    except Exception as e:
                        logger.error(f"🧬 Trigger handling failed: {e}")
                        
                        # 🧠 فشل تطوري → Anti-Hebbian
                        if self._neuron_fabric and pre_activation:
                            self._neuron_fabric.learn_from_outcome(
                                pre_activation, success=False, impact=0.6
                            )
                            logger.info(f"🧠 Anti-Hebbian: {len(pre_activation)} neurons weakened (failure)")
                        
                        if journal:
                            journal.record(
                                "failure",
                                f"Evolution trigger failed: {event.trigger_type.value}: {str(e)[:100]}",
                                context={"error": str(e)[:200]},
                                confidence=0.7, cycle=cycle,
                                tags=["evolution", "error"]
                            )
        except Exception as e:
            logger.error(f"🧬 Evolution trigger check failed: {e}")

    async def _run_neuron_cycle(self, cycle: int):
        """دورة الشبكة العصبية v3.0 — NeuronPulse: تنشيط كل العصبونات"""
        if not self._neuron_fabric:
            return
        
        fabric = self._neuron_fabric
        
        # ⚡ NeuronPulse — activate ALL domains EVERY cycle
        try:
            from unified_core.core.neuron_pulse import get_neuron_pulse
            pulse = get_neuron_pulse()
            
            # Build system state from current monitoring data
            system_state = {
                "neural_alive": bool(self.components.components.get("neural_bridge")),
                "trading_active": bool(self.components.components.get("wisdom")),
                "agents_dispatched": bool(self._agent_orchestrator),
            }
            # Add CPU/mem if available
            try:
                import psutil
                system_state["cpu_percent"] = psutil.cpu_percent(interval=0)
                system_state["mem_percent"] = psutil.virtual_memory().percent
            except Exception:
                pass
            
            pulse.pulse(cycle, system_state)
        except Exception as e:
            if cycle % 50 == 0:
                logger.debug(f"NeuronPulse error: {e}")
        
        # كل 30 دورة: حالة الشبكة
        if cycle % 30 == 0 and cycle > 0:
            stats = fabric.get_stats()
            logger.info(
                f"🧬 NeuronFabric: {stats['total_neurons']} neurons "
                f"({stats['alive_neurons']} alive), "
                f"{stats['total_synapses']} synapses, "
                f"E̅={stats['avg_energy']:.2f}, "
                f"activations={stats['total_activations']}, "
                f"learnings={stats['total_learnings']}"
            )
        
        # كل 100 دورة: تقليم + حفظ
        if cycle % 100 == 0 and cycle > 0:
            pruned = fabric.prune()
            fabric.save()
            if pruned > 0:
                logger.info(f"🧹 NeuronFabric pruned {pruned} dead elements, state saved")
        
        # كل 50 دورة: تعلم من journal
        if cycle % 50 == 0 and cycle > 0:
            try:
                from unified_core.core.neuron_fabric import NeuronType
                journal = self.components.components.get("cognitive_journal")
                
                if journal:
                    recent = journal.get_recent(limit=10)
                    for entry in recent:
                        entry_type = entry.get("type", "")
                        content = entry.get("content", "")
                        tags = entry.get("tags", [])
                        
                        if "evolution" in tags:
                            if entry_type == "success":
                                neuron = fabric.create_neuron(
                                    proposition=f"تطور ناجح: {content[:100]}",
                                    neuron_type=NeuronType.COGNITIVE,
                                    confidence=0.8,
                                    domain="evolution",
                                    tags=["evolution", "success", "learned"],
                                    energy=0.9,
                                )
                                fabric.auto_connect(neuron.neuron_id, max_connections=4)
                                related = fabric.activate_by_query(content[:50], top_k=5)
                                fabric.learn_from_outcome(related, success=True, impact=0.8)
                                
                            elif entry_type == "failure":
                                neuron = fabric.create_neuron(
                                    proposition=f"⚠️ فشل: {content[:100]}",
                                    neuron_type=NeuronType.EMOTIONAL,
                                    confidence=0.7,
                                    domain="evolution",
                                    tags=["evolution", "failure", "scar"],
                                    energy=0.7,
                                )
                                fabric.auto_connect(neuron.neuron_id, max_connections=3)
                                related = fabric.activate_by_query(content[:50], top_k=5)
                                fabric.learn_from_outcome(related, success=False, impact=0.6)
            except Exception as e:
                logger.debug(f"Neuron learning cycle error: {e}")
    
    async def _run_linux_health(self, cycle: int):
        """فحص صحة لينكس — تشخيص وإصلاح تلقائي"""
        if not self._linux_intel:
            return
        
        # كل 60 دورة (~2 دقيقة): فحص شامل
        if cycle % 60 == 0 and cycle > 0:
            try:
                result = await self._linux_intel.run_health_check()
                
                journal = self.components.components.get("cognitive_journal")
                
                if result.get("diagnoses"):
                    # وجد مشاكل — سجّل
                    for diag in result["diagnoses"]:
                        logger.warning(
                            f"🐧 Issue: {diag['problem']} → {diag['root_cause']} "
                            f"(fix: {diag['suggested_fix']})"
                        )
                        
                        if journal:
                            journal.record(
                                "observation",
                                f"Linux issue: {diag['problem']} — {diag['root_cause']}",
                                context=diag,
                                confidence=diag.get("confidence", 0.5),
                                cycle=cycle,
                                tags=["linux", "diagnosis", diag.get("severity", "warning")]
                            )
                    
                    # تنشيط عصبونات الحماية
                    if self._neuron_fabric:
                        activated = self._neuron_fabric.activate_by_query(
                            "حماية النظام خطأ service فشل إصلاح", top_k=5
                        )
                        if activated:
                            # مشكلة وجدناها → تعلم سلبي لو ما انحلت
                            fixed = len(result.get("actions_taken", []))
                            if fixed > 0:
                                self._neuron_fabric.learn_from_outcome(
                                    activated, success=True, impact=0.5
                                )
                                logger.info(f"🧠 Linux fix success → Hebbian ({len(activated)} neurons)")
                            else:
                                self._neuron_fabric.learn_from_outcome(
                                    activated, success=False, impact=0.2
                                )
                
                # Actions taken
                for action in result.get("actions_taken", []):
                    logger.info(
                        f"🐧 Action: {action['description']} — "
                        f"{'✅' if action['success'] else '❌'}"
                    )
                    if journal:
                        journal.record(
                            "success" if action["success"] else "failure",
                            f"Linux auto-fix: {action['description']}",
                            context=action,
                            confidence=0.8 if action["success"] else 0.5,
                            cycle=cycle,
                            tags=["linux", "auto_fix", action["type"]]
                        )
                
                # Log stats periodically
                stats = self._linux_intel.get_stats()
                if stats["total_actions"] > 0 or stats["total_diagnoses"] > 0:
                    logger.info(
                        f"🐧 LinuxIntel stats: "
                        f"actions={stats['total_actions']}, "
                        f"fixes={stats['total_fixes']}, "
                        f"diagnoses={stats['total_diagnoses']}"
                    )
            
            except Exception as e:
                logger.debug(f"Linux health check error: {e}")
    
    async def run(self):
        """تشغيل النظام"""
        await self.initialize()
        await self.loop.run()
        
    async def shutdown(self):
        """إيقاف النظام"""
        # حفظ الشبكة العصبية قبل الإيقاف
        if self._neuron_fabric:
            self._neuron_fabric.save()
            logger.info("🧬 NeuronFabric state saved before shutdown")
        
        # Log Linux stats
        if self._linux_intel:
            stats = self._linux_intel.get_stats()
            logger.info(f"🐧 LinuxIntelligence final stats: {stats}")
        
        self.loop.running = False
        self.state = "stopped"
        logger.info("🛑 AgentDaemon stopped")

# Singleton instance
    async def _run_trading_cycle(self, cycle: int):
        """دورة التداول - كل 150 دورة (5 دقائق)"""
        if cycle % 150 != 0:
            return

        trading_agent = self.components.components.get("trading_agent")
        if not trading_agent:
            return

        try:
            # تشغيل دورة تداول واحدة
            await trading_agent.run_cycle()

            # كل 10 دورات (50 دقيقة): عرض التعلم
            if cycle % 1500 == 0:
                insights = await trading_agent.get_learning_insights()
                performance = insights.get('performance', {})

                logger.info(f"📊 Trading Performance: "
                          f"{performance.get('total_trades', 0)} trades | "
                          f"Win Rate: {performance.get('win_rate', 0):.1f}% | "
                          f"Balance: ${performance.get('balance', 0):.2f} | "
                          f"ROI: {performance.get('roi', 0):+.1f}%")

                # حفظ في Journal
                journal = self.components.components.get("cognitive_journal")
                if journal:
                    journal.record(
                        "trading_performance",
                        json.dumps(performance, ensure_ascii=False),
                        cycle=cycle,
                        tags=["trading", "performance", "learning"]
                    )

        except Exception as e:
            logger.error(f"❌ Trading cycle error: {e}")


_daemon_instance = None

def get_daemon():
    """الحصول على نسخة الوكيل"""
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = AgentDaemon()
    return _daemon_instance

async def main():
    """الدالة الرئيسية"""
    daemon = get_daemon()
    
    try:
        await daemon.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await daemon.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
