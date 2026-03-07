"""
Unified Core Bridge - Integration with NOOGH Gateway
Connects the unified_core subsystems with the existing gateway
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("unified_core.bridge")

from unified_core.state import get_state


class UnifiedCoreBridge:
    """
    Bridge between NOOGH Gateway and Unified Core.
    Provides unified access to all subsystems.
    """
    
    def __init__(self):
        self._unified_core = None
        self._initialized = False
        
        # Lazy imports to avoid circular dependencies
        self._data_router = None
        self._secops = None
        self._resource_monitor = None
        self._process_manager = None
        self._filesystem = None
        
        # External actuators for real-world effects
        self._actuator_hub = None
    
    async def initialize(self, config: Optional[Dict] = None) -> bool:
        """Initialize bridge with unified core components."""
        if self._initialized:
            return True
        
        try:
            # Initialize Data Router (with memory fallbacks if DBs unavailable)
            from unified_core.db import PostgresManager, VectorDBManager, GraphDBManager, DataRouter
            
            postgres = PostgresManager(
                host=config.get("postgres_host", "localhost") if config else "localhost",
                port=config.get("postgres_port", 5432) if config else 5432,
                database=config.get("postgres_db", "unified_core") if config else "unified_core"
            )
            
            vector_db = VectorDBManager(
                host=config.get("milvus_host", "localhost") if config else "localhost",
                use_memory_fallback=True
            )
            
            graph_db = GraphDBManager(
                uri=config.get("neo4j_uri", "bolt://localhost:7687") if config else "bolt://localhost:7687",
                use_memory_fallback=True
            )
            
            self._data_router = DataRouter(
                postgres=postgres,
                vector_db=vector_db,
                graph_db=graph_db
            )
            
            # Initialize Data Router (with graceful fallbacks)
            db_results = await self._data_router.initialize_all()
            logger.info(f"DataRouter init: {db_results}")
            
            # Initialize Security
            from unified_core.secops_agent import SecOpsAgent
            self._secops = SecOpsAgent()
            
            # Initialize Resource Monitor
            from unified_core.resources.monitor import ResourceMonitor
            self._resource_monitor = ResourceMonitor(gpu_enabled=True)
            await self._resource_monitor.initialize()
            
            # Initialize Process Manager
            from unified_core.resources.process_manager import ProcessManager
            self._process_manager = ProcessManager()
            await self._process_manager.initialize()
            
            # Initialize Secure Filesystem
            from unified_core.resources.filesystem import SecureFileSystem
            allowed_roots = config.get("allowed_roots", ["/app/data", "/tmp"]) if config else ["/app/data", "/tmp"]
            self._filesystem = SecureFileSystem(allowed_roots=allowed_roots)
            
            # ========================================
            # GENUINE AI CORE INITIALIZATION
            # ========================================
            
            # 1. WorldModel - Beliefs, predictions, falsification
            from unified_core.core.world_model import WorldModel
            self._world_model = WorldModel()
            logger.info("WorldModel initialized - beliefs can now be falsified")
            
            # 2. ConsequenceEngine - Irreversible state
            from unified_core.core.consequence import ConsequenceEngine
            self._consequence_engine = ConsequenceEngine()
            logger.info("ConsequenceEngine initialized - state is now irreversible")
            
            # 3. CoerciveMemory - Memory that blocks
            from unified_core.core.coercive_memory import CoerciveMemory
            self._coercive_memory = CoerciveMemory(consequence_engine=self._consequence_engine)
            logger.info("CoerciveMemory initialized - memory now blocks actions")
            
            # 4. ScarTissue - Permanent failure damage
            from unified_core.core.scar import ScarTissue
            self._scar_tissue = ScarTissue(
                memory=self._coercive_memory,
                world_model=self._world_model
            )
            logger.info("ScarTissue initialized - failures now leave permanent scars")
            
            # 5. GravityWell - Centralized decision authority
            from unified_core.core.gravity import GravityWell
            self._gravity_well = GravityWell(
                world_model=self._world_model,
                memory=self._coercive_memory,
                consequence_engine=self._consequence_engine,
                scar_tissue=self._scar_tissue
            )
            logger.info("GravityWell initialized - all decision authority centralized")
            
            # Initialize The Dreamer (now delegates to GravityWell)
            from unified_core.dreamer import Dreamer
            self._dreamer = Dreamer(interval_seconds=30.0)
            self._dreamer.set_gravity_well(self._gravity_well)  # Connect to genuine AI core
            self._dreamer.start()
            logger.info("Dreamer started - genuine goal synthesis active")
            
            # 6. ActuatorHub - External world effects
            from unified_core.core.actuators import ActuatorHub
            self._actuator_hub = ActuatorHub(
                consequence_engine=self._consequence_engine,
                scar_tissue=self._scar_tissue
            )
            logger.info("ActuatorHub initialized - external world access enabled")
            
            # 7. NeuralEngineBridge - Connect Neural Engine to AI Core
            from unified_core.neural_bridge import NeuralEngineBridge, NeuralEngineClient
            import os as _os
            neural_url = config.get("neural_url", _os.getenv("NEURAL_ENGINE_URL", "http://127.0.0.1:8002")) if config else _os.getenv("NEURAL_ENGINE_URL", "http://127.0.0.1:8002")
            self._neural_bridge = NeuralEngineBridge(
                gravity_well=self._gravity_well,
                consequence_engine=self._consequence_engine,
                coercive_memory=self._coercive_memory,
                scar_tissue=self._scar_tissue,
                neural_url=neural_url
            )
            logger.info("NeuralEngineBridge initialized - Neural Engine connected to AI Core")
            
            # Initialize Meta-Cognition (Self-Identity) - NULLIFIED, retained for API
            from unified_core.identity import SelfIdentity
            self._identity = SelfIdentity()
            
            # Initialize Innovation Lab (Code Synthesis) - NULLIFIED, retained for API
            try:
                from unified_core.innovation import InnovationLab
                self._innovation = InnovationLab(secops_agent=self._secops)
            except ImportError:
                self._innovation = None
                logger.info("InnovationLab not available — skipped")
            
            # LOAD PERSISTED EVOLVED TOOLS
            # This ensures evolution is permanent across restarts
            self._load_evolved_tools()

            # SEED WORLDMODEL WITH FOUNDATIONAL BELIEFS
            # This gives the AI core initial knowledge to work with
            from unified_core.core.world_init import seed_world_model
            seeded_beliefs = await seed_world_model(self._world_model)
            logger.info(f"WorldModel seeded with {len(seeded_beliefs)} foundational beliefs")

            self._initialized = True
            get_state().update("bridge_initialized", True)
            get_state().update("ai_core_active", True)
            get_state().update("worldmodel_beliefs", len(seeded_beliefs))
            logger.info("UnifiedCoreBridge initialized - GENUINE AI CORE ACTIVE")
            return True
            
        except Exception as e:
            logger.error(f"UnifiedCoreBridge init failed: {e}")
            return False

    def _load_evolved_tools(self):
        """Load tools that the system previously invented."""
        try:
            import os
            import importlib.util
            
            base_dir = "/home/noogh/projects/noogh_unified_system/src/unified_core/tools/evolved"
            if not os.path.exists(base_dir):
                return

            loaded_count = 0
            for filename in os.listdir(base_dir):
                if filename.endswith(".py"):
                    try:
                        # Dynamic import
                        tool_name = filename[:-3]
                        file_path = os.path.join(base_dir, filename)
                        
                        spec = importlib.util.spec_from_file_location(tool_name, file_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Register in Identity
                        if self._identity:
                             # Extract description from docstring if possible
                             desc = module.__doc__ or "Evolved tool from previous session"
                             self._identity.register_capability(tool_name, desc)
                             loaded_count += 1
                    except Exception as ex:
                        logger.warning(f"Failed to load evolved tool {filename}: {ex}")
            
            if loaded_count > 0:
                logger.info(f"Evolution Persistence: Loaded {loaded_count} self-evolved tools.")
                
        except Exception as e:
            logger.error(f"Error loading evolved tools: {e}")
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    # ========================================
    # Data Operations
    # ========================================
    
    async def query(self, input_data: Any, **kwargs) -> Dict:
        """Universal query through DataRouter with state-driven adaptation."""
        if not self._data_router:
            return {"success": False, "error": "DataRouter not initialized"}
        
        # ========================================
        # AGENCY CORE: Consult state before action
        # ========================================
        state = get_state()
        hint = state.get_adaptation_hint("query")
        
        # Apply adaptation based on state analysis
        adapted = False
        if hint.action.value == "use_fallback":
            kwargs["use_memory_fallback"] = True
            kwargs["timeout_multiplier"] = 2.0
            adapted = True
            logger.info(f"Query adapted: {hint.reason}")
        
        result = await self._data_router.query(input_data, **kwargs)
        state.update("last_query_success", result.success)
        
        # Record adaptation effectiveness and CLOSE THE LOOP
        if adapted:
            state.update("last_adaptation_effective", result.success)
            # Auto-tune thresholds based on this new data
            tuned = state.tune_thresholds()
            if tuned:
                logger.info(f"System auto-tuned thresholds: {tuned}")
        
        return {
            "success": result.success,
            "data_type": result.data_type.name,
            "sources": result.sources,
            "sql_data": result.sql_result.data if result.sql_result else None,
            "vector_results": [
                {"id": r.id, "score": r.score, "metadata": r.metadata}
                for r in (result.vector_result.results if result.vector_result else [])
            ],
            "graph_nodes": [
                {"id": n.id, "labels": n.labels, "properties": n.properties}
                for n in (result.graph_result.nodes if result.graph_result else [])
            ],
            "execution_time_ms": result.execution_time_ms,
            "adapted": adapted,
            "adaptation_hint": hint.reason if adapted else None
        }
    
    async def store(self, input_data: Any, **kwargs) -> Dict:
        """Universal store through DataRouter with state-driven adaptation."""
        if not self._data_router:
            return {"success": False, "error": "DataRouter not initialized"}
        
        # AGENCY: Consult state before action
        state = get_state()
        hint = state.get_adaptation_hint("store")
        
        adapted = False
        if hint.action.value == "use_fallback":
            kwargs["use_memory_fallback"] = True
            adapted = True
            logger.info(f"Store adapted: {hint.reason}")
        
        result = await self._data_router.store(input_data, **kwargs)
        state.update("last_store_success", result.success)
        
        return {
            "success": result.success,
            "data_type": result.data_type.name,
            "sources": result.sources,
            "error": result.error,
            "adapted": adapted
        }
    
    # ========================================
    # Security Operations
    # ========================================
    
    async def audit_code(self, code: str, language: str = "python") -> Dict:
        """Audit code for security vulnerabilities with state-driven risk awareness."""
        if not self._secops:
            return {"success": False, "error": "SecOps not initialized"}
        
        # AGENCY: Consult state for risk trends
        state = get_state()
        hint = state.get_adaptation_hint("audit")
        
        # Check if we're in a high-risk trend
        risk_alert = None
        if hint.action.value == "alert_high_risk":
            risk_alert = {
                "warning": "Risk trend increasing",
                "details": hint.reason,
                "recommendation": "Review recent code changes carefully"
            }
            logger.warning(f"High risk trend detected: {hint.reason}")
        
        from unified_core.dev_agent import CodeArtifact, CodeLanguage
        
        lang_map = {
            "python": CodeLanguage.PYTHON,
            "rust": CodeLanguage.RUST,
            "javascript": CodeLanguage.JAVASCRIPT,
        }
        
        artifact = CodeArtifact(
            language=lang_map.get(language, CodeLanguage.PYTHON),
            code=code,
            filename="audit_target.py",
            description="Code audit request"
        )
        
        result = await self._secops.audit(artifact)
        state.update("last_audit_risk", result.risk_score)
        
        # Detect if this audit confirms high risk trend
        trend, avg_risk = state.get_risk_trend()
        
        return {
            "approved": result.approved,
            "risk_score": result.risk_score,
            "issues": result.issues,
            "detailed_issues": [
                {
                    "category": i.category.value,
                    "severity": i.severity.name,
                    "message": i.message,
                    "line": i.line_number,
                    "recommendation": i.recommendation
                }
                for i in result.detailed_issues
            ],
            "execution_time_ms": result.execution_time_ms,
            "risk_trend": trend,
            "average_risk": avg_risk,
            "risk_alert": risk_alert
        }
    
    # ========================================
    # Resource Operations
    # ========================================
    
    async def get_system_snapshot(self) -> Dict:
        """Get complete system resource snapshot."""
        if not self._resource_monitor:
            return {"success": False, "error": "ResourceMonitor not initialized"}
        
        snapshot = await self._resource_monitor.get_snapshot()
        
        return {
            "success": True,
            "timestamp": snapshot.timestamp.isoformat(),
            "cpu": {
                "usage_percent": snapshot.cpu.usage_percent,
                "cores": snapshot.cpu.core_count,
                "load_1m": snapshot.cpu.load_1m
            },
            "memory": {
                "total_gb": snapshot.memory.total_bytes / (1024**3),
                "used_gb": snapshot.memory.used_bytes / (1024**3),
                "usage_percent": snapshot.memory.usage_percent
            },
            "gpus": [
                {
                    "id": g.device_id,
                    "name": g.name,
                    "memory_total_mb": g.memory_total_mb,
                    "memory_used_mb": g.memory_used_mb,
                    "memory_percent": g.memory_percent,
                    "utilization": g.gpu_utilization,
                    "temperature_c": g.temperature_c
                }
                for g in snapshot.gpus
            ],
            "disks": [
                {
                    "path": d.path,
                    "usage_percent": d.usage_percent,
                    "free_gb": d.free_bytes / (1024**3)
                }
                for d in snapshot.disks
            ],
            "process_count": snapshot.process_count,
            "uptime_hours": snapshot.uptime_seconds / 3600
        }
    
    async def free_memory(self, target_mb: float, include_gpu: bool = False) -> Dict:
        """Free memory by killing low-priority processes."""
        if not self._process_manager:
            return {"success": False, "error": "ProcessManager not initialized"}
        
        result = await self._process_manager.free_memory(target_mb, include_gpu)
        get_state().update("memory_freed_mb", result.get("freed_mb", 0))
        return result
    
    # ========================================
    # Filesystem Operations
    # ========================================
    
    def read_file(self, path: str, agent_id: str = "gateway") -> Dict:
        """Read file through secure filesystem."""
        if not self._filesystem:
            return {"success": False, "error": "Filesystem not initialized"}
        
        result = self._filesystem.read_file(path, agent_id)
        get_state().update("last_fs_read_success", result.success)
        return {
            "success": result.success,
            "content": result.content,
            "error": result.error,
            "metadata": result.metadata
        }
    
    def write_file(self, path: str, content: str, agent_id: str = "gateway") -> Dict:
        """Write file through secure filesystem."""
        if not self._filesystem:
            return {"success": False, "error": "Filesystem not initialized"}
        
        result = self._filesystem.write_file(path, content, agent_id)
        get_state().update("last_fs_write_success", result.success)
        return {
            "success": result.success,
            "error": result.error,
            "metadata": result.metadata
        }
    
    def list_dir(self, path: str, agent_id: str = "gateway") -> Dict:
        """List directory through secure filesystem."""
        if not self._filesystem:
            return {"success": False, "error": "Filesystem not initialized"}
        
        result = self._filesystem.list_directory(path, agent_id)
        get_state().update("last_fs_list_success", result.success)
        return {
            "success": result.success,
            "files": result.metadata.get("files", []) if result.success else [],
            "error": result.error
        }
    
    def get_audit_log(self, agent_id: Optional[str] = None) -> List[Dict]:
            """Get filesystem audit log."""
            if not self._filesystem:
                return []

            if agent_id is not None and not isinstance(agent_id, str):
                raise ValueError("Agent ID must be a string or None")

            try:
                entries = self._filesystem.get_audit_log(agent_id=agent_id)
            except Exception as e:
                logging.error(f"Failed to retrieve audit log: {e}")
                return []

            result = []
            for e in entries:
                entry = {
                    "operation": e.operation.value,
                    "path": e.path,
                    "agent_id": e.agent_id,
                    "timestamp": e.timestamp.isoformat(),
                    "success": e.success,
                    "error": e.error
                }
                result.append(entry)

            return result

    # ========================================
    # COGNITION & INNOVATION
    # ========================================

    async def introspection(self) -> Dict:
        """
        Perform system introspection (Meta-Cognition).
        Checks if capabilities match current goals.
        """
        if not self._identity:
            return {"error": "No Identity module"}
        
        goals = get_state().get_goals()
        assessment = self._identity.introspect(goals)
        
        # AGENCY LOOP LEVEL 3: INNOVATION & PLANNING
        if assessment.get("needs_innovation"):
             if not self._innovation:
                 return assessment

             # Initialize Planner if needed
             # Lazy import to avoid circular dependency issues at top level
             from unified_core.reasoning import StrategicPlanner
             if not hasattr(self, "_planner"):
                 self._planner = StrategicPlanner()

             logger.info("Introspection revealed gap. Triggering Strategic Planning.")
             
             for gap in assessment["gaps"]:
                 # gap string example: "Goal 'Cleanup Logs' requires capabilities I may lack."
                 goal_desc = gap.split("'")[1] if "'" in gap else "unknown"
                 
                 # 1. PLAN: Decompose the complex goal
                 plan = self._planner.decompose(goal_desc, "Auto-generated plan")
                 assessment["plan"] = str(plan)
                 
                 # 2. INNOVATE: Generate tools for EACH step
                 for step in plan.steps:
                     # Check if we already have a tool (simple name match)
                     # In real system, we'd check capabilities. Here we assume we need to make it.
                     
                     proposal = self._innovation.propose_tool(step.description)
                     if proposal["success"]:
                         logger.info(f"Innovation Lab: Created tool '{proposal['tool_name']}' for step '{step.description}'")
                         
                         # Register capability
                         self._identity.register_capability(proposal['tool_name'], step.description)
                         step.tool_name = proposal['tool_name']
                     else:
                         logger.warning(f"Failed to create tool for step: {step.description}")
                         
                 assessment["proposed_innovation"] = f"Generated plan with {len(plan.steps)} tools."

    # ========================================
    # GENUINE AI CORE INTERFACE
    # ========================================

    async def decide(self, query: str, urgency: float = 0.5) -> Dict:
        """
        Make a decision through the GravityWell.
        
        This is the GENUINE decision-making interface.
        Decisions are:
        - Based on beliefs from WorldModel
        - Constrained by CoerciveMemory
        - Filtered through ScarTissue
        - Committed irreversibly to ConsequenceEngine
        """
        if not hasattr(self, '_gravity_well') or not self._gravity_well:
            return {"success": False, "error": "GravityWell not initialized"}
        
        from unified_core.core.gravity import DecisionContext
        
        context = DecisionContext(query=query, urgency=urgency)
        decision = self._gravity_well.decide(context)
        
        return {
            "success": True,
            "decision_id": decision.decision_id,
            "decision_type": decision.decision_type.value,
            "content": decision.content,
            "commitment_hash": decision.commitment_hash,
            "based_on_beliefs": decision.based_on_beliefs,
            "constrained_by": decision.constrained_by,
            "cost_paid": decision.cost_paid
        }

    def get_ai_core_status(self) -> Dict:
        """
        Get status of the genuine AI core components.
        
        Returns metrics for:
        - WorldModel: beliefs, falsifications
        - ConsequenceEngine: consequences, constraints
        - CoerciveMemory: blockers, penalties
        - ScarTissue: scars, depth
        - GravityWell: decisions made
        """
        status = {
            "ai_core_active": hasattr(self, '_gravity_well') and self._gravity_well is not None,
            "components": {}
        }
        
        if hasattr(self, '_world_model') and self._world_model:
            status["components"]["world_model"] = self._world_model.get_belief_state()
        
        if hasattr(self, '_consequence_engine') and self._consequence_engine:
            status["components"]["consequence_engine"] = {
                "consequence_count": self._consequence_engine.get_consequence_count(),
                "constraint_count": self._consequence_engine.get_constraint_count(),
                "blocked_patterns": self._consequence_engine.get_blocked_patterns()
            }
        
        if hasattr(self, '_coercive_memory') and self._coercive_memory:
            status["components"]["coercive_memory"] = {
                "blocker_count": self._coercive_memory.get_blocked_count(),
                "penalty_count": self._coercive_memory.get_penalty_count(),
                "destroyed_logic": list(self._coercive_memory.get_destroyed_logic())
            }
        
        if hasattr(self, '_scar_tissue') and self._scar_tissue:
            status["components"]["scar_tissue"] = self._scar_tissue.get_summary()
        
        if hasattr(self, '_gravity_well') and self._gravity_well:
            status["components"]["gravity_well"] = {
                "decision_count": self._gravity_well.get_decision_count(),
                "active_goals": len(self._gravity_well.get_active_goals()),
                "is_predictable": self._gravity_well.is_predictable()
            }
        
        return status

    def report_failure(self, action_type: str, error_message: str, params: Dict = None) -> Dict:
            """
            Report a failure to the ScarTissue.
            This creates a permanent scar that blocks future similar actions.
            """
            if not hasattr(self, '_scar_tissue') or not self._scar_tissue:
                return {"success": False, "error": "ScarTissue not initialized"}
        
            from unified_core.core.scar import Failure
            import hashlib
            import time
            import logging

            # Input validation
            if not isinstance(action_type, str):
                logging.error("Action type must be a string")
                return {"success": False, "error": "Invalid action type"}
        
            if not isinstance(error_message, str):
                logging.error("Error message must be a string")
                return {"success": False, "error": "Invalid error message"}
        
            if params is not None and not isinstance(params, dict):
                logging.error("Params must be a dictionary or None")
                return {"success": False, "error": "Invalid params"}

            try:
                failure = Failure(
                    failure_id=hashlib.sha256(
                        f"reported:{action_type}:{time.time()}".encode()
                    ).hexdigest()[:16],
                    action_type=action_type,
                    action_params=params or {},
                    error_message=error_message
                )

                scar = self._scar_tissue.inflict(failure)
            
                logging.info(f"Scar created with ID {scar.scar_id}")
            
                return {
                    "success": True,
                    "scar_id": scar.scar_id,
                    "actions_blocked": scar.actions_blocked,
                    "scar_depth": self._scar_tissue.get_scar_depth()
                }
            except Exception as e:
                logging.error(f"Failed to report failure: {str(e)}")
                return {"success": False, "error": "Failed to report failure"}

    # ========================================
    # EXTERNAL ACTUATORS (REAL-WORLD EFFECTS)
    # ========================================
    
    async def actuator_write_file(self, path: str, content: str, auth_context: Optional[Any] = None) -> Dict:
        """
        Write file using external actuator (ASYNC).
        THIS IS IRREVERSIBLE - content is written to disk.
        Failures inflict scars. Requires 'fs:write' scope.
        """
        if not self._actuator_hub:
            return {"success": False, "error": "ActuatorHub not initialized"}
        
        # Security: Force AuthContext if missing
        if not auth_context:
            from unified_core.auth import AuthContext
            auth_context = AuthContext(user_id="bridge_system", scopes={"fs:write"})
            
        result = await self._actuator_hub.filesystem.write_file(path, content, auth_context=auth_context)
        return result.to_dict()
    
    async def actuator_delete_file(self, path: str, auth_context: Optional[Any] = None) -> Dict:
        """
        Delete file using external actuator (ASYNC).
        THIS IS IRREVERSIBLE - file is permanently deleted.
        Failures inflict scars. Requires 'fs:delete' scope.
        """
        if not self._actuator_hub:
            return {"success": False, "error": "ActuatorHub not initialized"}

        # Security: Force AuthContext if missing
        if not auth_context:
            from unified_core.auth import AuthContext
            auth_context = AuthContext(user_id="bridge_system", scopes={"fs:delete"})
            
        result = await self._actuator_hub.filesystem.delete_file(path, auth_context=auth_context)
        return result.to_dict()
    
    async def actuator_http_request(
        self, 
        method: str, 
        url: str, 
        headers: Dict = None,
        body: str = None,
        auth_context: Optional[Any] = None
    ) -> Dict:
        """
        Send HTTP request using external actuator (ASYNC).
        THIS CANNOT BE UNSENT - the request will reach the server.
        Failures inflict scars. Requires 'network:http' scope.
        """
        if not self._actuator_hub:
            return {"success": False, "error": "ActuatorHub not initialized"}
        
        # Security: Force AuthContext if missing
        if not auth_context:
            from unified_core.auth import AuthContext
            auth_context = AuthContext(user_id="bridge_system", scopes={"network:http"})
            
        result = await self._actuator_hub.network.http_request(
            url=url, 
            method=method, 
            headers=headers, 
            body=body,
            auth_context=auth_context
        )
        return result.to_dict()
    
    async def actuator_spawn_process(self, cmd: List[str], cwd: str = None, auth_context: Optional[Any] = None) -> Dict:
        """
        Spawn subprocess using external actuator (ASYNC).
        THIS IS A REAL SYSTEM EFFECT - the process will execute.
        Failures inflict scars. Requires 'process:spawn' scope.
        """
        if not self._actuator_hub:
            return {"success": False, "error": "ActuatorHub not initialized"}
            
        # Security: Force AuthContext if missing
        if not auth_context:
            from unified_core.auth import AuthContext
            auth_context = AuthContext(user_id="bridge_system", scopes={"process:spawn"})
        
        result = await self._actuator_hub.process.spawn(cmd, auth_context=auth_context, cwd=cwd)
        return result.to_dict()
    
    async def actuator_kill_process(self, pid: int, auth_context: Optional[Any] = None) -> Dict:
        """
        Kill process using external actuator (ASYNC).
        THIS IS IRREVERSIBLE - the process will be terminated.
        Failures inflict scars. Requires 'process:kill' scope.
        """
        if not self._actuator_hub:
            return {"success": False, "error": "ActuatorHub not initialized"}

        # Security: Force AuthContext if missing
        if not auth_context:
            from unified_core.auth import AuthContext
            auth_context = AuthContext(user_id="bridge_system", scopes={"process:kill"})
            
        result = await self._actuator_hub.process.kill(pid, auth_context=auth_context)
        return result.to_dict()
    
    def get_actuator_stats(self) -> Dict:
        """Get statistics from all actuators."""
        if not self._actuator_hub:
            return {"error": "ActuatorHub not initialized"}
        
        return self._actuator_hub.get_stats()

    # ========================================
    # NEURAL ENGINE BRIDGE (AI CORE PIPELINE)
    # ========================================

    async def neural_think(self, query: str, context: Dict = None, urgency: float = 0.5) -> Dict:
        """
        Think through Neural Engine with GravityWell authority.
        
        This routes the request through:
        1. CoerciveMemory (block check)
        2. GravityWell (decision authority)
        3. Neural Engine (thinking)
        4. ConsequenceEngine (commitment)
        5. ScarTissue (on failure)
        
        DECISIONS ARE IRREVERSIBLE.
        """
        if not hasattr(self, '_neural_bridge') or not self._neural_bridge:
            return {"success": False, "error": "NeuralEngineBridge not initialized"}
        
        from unified_core.neural_bridge import NeuralRequest
        
        request = NeuralRequest(
            query=query,
            context=context,
            urgency=urgency
        )
        
        response = await self._neural_bridge.think_with_authority(request)
        
        return {
            "success": response.success,
            "content": response.content,
            "blocked": response.blocked,
            "block_reason": response.block_reason,
            "decision_id": response.decision_id,
            "commitment_hash": response.commitment_hash,
            "thinking_process": response.thinking_process,
            "confidence": response.confidence
        }
    
    def get_neural_bridge_stats(self) -> Dict:
            """Get NeuralEngineBridge statistics."""
            if not hasattr(self, '_neural_bridge') or not self._neural_bridge:
                logger.warning("NeuralEngineBridge not initialized")
                return {"error": "NeuralEngineBridge not initialized"}
        
            return self._neural_bridge.get_stats()


# Global singleton instance
_bridge_instance: Optional[UnifiedCoreBridge] = None


def get_bridge() -> UnifiedCoreBridge:
    """Get or create global bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        logger.info("Creating new instance of UnifiedCoreBridge.")
        _bridge_instance = UnifiedCoreBridge()
    return _bridge_instance


async def init_bridge(config: Optional[Dict] = None) -> UnifiedCoreBridge:
    """Initialize and return global bridge instance."""
    bridge = get_bridge()
    await bridge.initialize(config)
    return bridge
