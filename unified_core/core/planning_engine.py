"""
Strategic Planning Engine - Multi-Step Goal Decomposition

Transforms complex goals into executable action sequences with dependency management.

CAPABILITIES:
- Goal decomposition (break down into sub-goals)
- Dependency resolution (DAG construction)
- Specialist coordination (assign to appropriate specialists)
- Parallel execution (where dependencies allow)
- Progress tracking & failure recovery
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

from ..task_dispatcher import TaskStatus as DispatcherTaskStatus
logger = logging.getLogger("unified_core.core.planning_engine")


class TaskStatus(Enum):
    """Status of a task within a plan."""
    PENDING = "pending"
    READY = "ready"          # Dependencies satisfied
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"      # Dependencies failed


@dataclass
class SubTask:
    """A single executable task within a plan."""
    task_id: str
    description: str
    assigned_specialist: str
    dependencies: List[str] = field(default_factory=list)  # task_ids that must complete first
    task_type: Optional[str] = None                         # Specialist-specific task type
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)


@dataclass
class Plan:
    """A strategic plan for achieving a goal."""
    plan_id: str
    goal_description: str
    tasks: List[SubTask]
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal_description,
            "tasks": len(self.tasks),
            "completed": sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self.tasks if t.status == TaskStatus.FAILED),
            "success": self.success
        }


class PlanningEngine:
    """
    Strategic planning for multi-step goals.
    
    Capabilities:
    1. Goal Decomposition: Break complex goals into sub-tasks
    2. Dependency Analysis: Build execution DAG
    3. Specialist Assignment: Route tasks to appropriate specialists
    4. Parallel Execution: Execute independent tasks concurrently
    5. Failure Recovery: Handle task failures gracefully
    """
    
    def __init__(self, world_model=None, gravity_well=None, task_dispatcher=None, dispatcher=None, journal=None):
        from unified_core.core.world_model import WorldModel
        self._world = world_model or WorldModel()
        self._gravity = gravity_well
        self._dispatcher = task_dispatcher or dispatcher
        self._journal = journal  # Phase 19: Arabic Cognitive Journaling
        self._active_plans: Dict[str, Plan] = {}
        self._plan_history: List[Plan] = []
        
        logger.info("PlanningEngine initialized - strategic planning enabled")
    
    def create_plan(self, goal_description: str) -> Plan:
        """
        Create strategic plan for achieving a goal.
        
        Steps:
        1. Analyze goal requirements
        2. Decompose into sub-tasks
        3. Identify dependencies
        4. Assign to specialists
        5. Build execution DAG
        
        Returns: Executable plan
        """
        plan_id = hashlib.sha256(f"plan:{goal_description}:{time.time()}".encode()).hexdigest()[:16]
        
        # Step 1: Decompose goal into sub-tasks
        sub_tasks = self._decompose_goal(goal_description)
        
        # Step 2: Build dependency graph
        sub_tasks = self._build_dependencies(sub_tasks)
        
        # Step 3: Assign specialists
        sub_tasks = self._assign_specialists(sub_tasks)
        
        plan = Plan(
            plan_id=plan_id,
            goal_description=goal_description,
            tasks=sub_tasks
        )
        
        self._active_plans[plan_id] = plan
        logger.info(f"Plan created: {plan_id} with {len(sub_tasks)} tasks")
        
        # Phase 19B: Deep Reasoning Journaling
        if hasattr(self, '_journal') and self._journal:
            reasoning = f"لقد قمت بتحليل الهدف '{goal_description}' وتوصلت إلى ضرورة تقسيمه إلى {len(sub_tasks)} خطوات منطقية لضمان التنفيذ الدقيق."
            if "security" in goal_description.lower():
                reasoning += " التحليل الأمني المبدئي يشير إلى وجود نقاط حرجة تتطلب فحصاً معمقاً."
            
            self._journal.record_thought(reasoning, context=f"PlanID: {plan_id}")
            self._journal.record_plan(goal_description, sub_tasks)
            
        return plan

    async def propose_synthetic_goal(self, description: str, source: str, priority: str = "medium"):
        """
        API for Specialists to propose autonomous goals based on wisdom synthesis.
        """
        logger.warning(f"SYNTHETIC GOAL PROPOSED: '{description}' from {source} (Priority: {priority})")
        
        # Step 1: Create plan
        plan = self.create_plan(description)
        
        # Step 2: Mark as synthetic in metadata
        plan.goal_description = f"[Synthetic:{source}] {description}"
        
        # Step 3: Trigger autonomous execution in background
        logger.info(f"🚀 Queueing background execution for plan: {plan.plan_id}")
        asyncio.create_task(self.execute_plan(plan))
        
        return plan.plan_id

    async def generate_goals_from_intents(self):
        """
        PHASE 18: Ingest active intents and convert to plans.
        """
        from unified_core.intent_injector import IntelligentIntentInjector
        injector = IntelligentIntentInjector()
        active_intents = injector.get_active_intents()
        
        for intent in active_intents:
            payload = intent.get('payload', {})
            desc = payload.get('description', intent.get('intent_type'))
            priority = intent.get('priority', 0.5)
            
            # Check if we already have a plan for this
            existing = [p for p in self._active_plans.values() if desc in p.goal_description]
            if not existing and priority > 0.7:
                logger.info(f"🎯 Converting high-priority intent to goal: {desc}")
                await self.propose_synthetic_goal(desc, source="Autonomous-Intent", priority="high")
                # Mark as completed in injector to prevent duplication
                injector.mark_completed(intent['id'])
    
    def _decompose_goal(self, goal: str) -> List[SubTask]:
        """
        Decompose goal into sub-tasks using optimized strategy mapping.
        """
        goal_lower = goal.lower()
        
        # Strategy mapping: keyword list -> decomposition handler
        strategies = [
            (["security", "vulnerability", "patch", "cve"], self._security_decomposition),
            (["performance", "optimize", "bottleneck", "latency"], self._performance_decomposition),
            (["modernize", "outdated", "legacy", "upgrade"], lambda: self._modernize_decomposition(goal)),
            (["lga1700", "thermal", "power", "cpu"], self._lga1700_decomposition),
            (["database", "data", "integrity", "query"], self._database_decomposition),
        ]
        
        for keywords, handler in strategies:
            if any(k in goal_lower for k in keywords):
                return handler()
            
        # Fallback to Generic decomposition
        return self._generic_decomposition(goal)

    def _security_decomposition(self) -> List[SubTask]:
        return [
            SubTask(self._gen_task_id("security_scan"), "Scan system for vulnerabilities", "security", task_type="vulnerability_detected"),
            SubTask(self._gen_task_id("security_audit"), "Audit security configurations", "security", task_type="vulnerability_detected"),
            SubTask(self._gen_task_id("apply_patches"), "Apply security patches", "linux", task_type="system_update")
        ]

    def _performance_decomposition(self) -> List[SubTask]:
        return [
            SubTask(self._gen_task_id("profile_system"), "Profile system performance", "finops", task_type="resource_waste"),
            SubTask(self._gen_task_id("identify_bottlenecks"), "Identify performance bottlenecks", "network", task_type="network_latency"),
            SubTask(self._gen_task_id("apply_optimizations"), "Apply optimizations", "linux", task_type="disk_usage")
        ]

    def _modernize_decomposition(self, goal: str) -> List[SubTask]:
        packages = []
        if "addressing:" in goal.lower():
            addressing_part = goal.lower().split("addressing:")[1]
            parts = addressing_part.replace("(", ",").replace(")", ",").split(",")
            for p in parts:
                if " is " in p:
                    pkg = p.split(" is ")[0].strip()
                    if pkg and pkg not in packages:
                        packages.append(pkg)
        
        pkgs_str = ', '.join(packages) if packages else goal
        return [
            SubTask(self._gen_task_id("analyze_modernization"), f"Analyze requirements for modernizing: {pkgs_str}", "linux", task_type="system_update"),
            SubTask(self._gen_task_id("apply_updates"), f"Apply updates for: {pkgs_str}", "linux", task_type="system_update"),
            SubTask(self._gen_task_id("verify_modernization"), f"Verify system stability after updating: {pkgs_str}", "qa", task_type="regression_detected")
        ]

    def _lga1700_decomposition(self) -> List[SubTask]:
        return [
            SubTask(self._gen_task_id("science_analysis"), "Analyze LGA1700 thermal and power voltage patterns", "science", task_type="analyze_data"),
            SubTask(self._gen_task_id("thermal_prediction"), "Model thermal headroom and stability forecast", "pi", task_type="predictive_modeling"),
            SubTask(self._gen_task_id("ai_power_opt"), "Optimize AI-driven CPU power curves", "ai", task_type="optimize_model"),
            SubTask(self._gen_task_id("health_verification"), "Verify system stability and final load health", "linux", task_type="linux_health")
        ]

    def _database_decomposition(self) -> List[SubTask]:
        return [
            SubTask(self._gen_task_id("analyze_schema"), "Analyze database schema", "database", task_type="missing_index"),
            SubTask(self._gen_task_id("optimize_queries"), "Optimize database queries", "database", task_type="slow_query"),
            SubTask(self._gen_task_id("verify_data"), "Verify data integrity", "qa", task_type="regression_detected")
        ]

    def _generic_decomposition(self, goal: str) -> List[SubTask]:
        return [
            SubTask(self._gen_task_id("analyze"), f"Analyze requirements for: {goal}", "linux", task_type="system_update"),
            SubTask(self._gen_task_id("execute"), f"Execute actions for: {goal}", "linux", task_type="disk_usage"),
            SubTask(self._gen_task_id("verify"), f"Verify completion of: {goal}", "qa", task_type="regression_detected")
        ]
    
    def _build_dependencies(self, tasks: List[SubTask]) -> List[SubTask]:
        """
        Build dependency graph (DAG).
        
        Rules:
        - First task has no dependencies
        - Middle tasks depend on first
        - Last task depends on all middle tasks
        """
        if len(tasks) <= 1:
            return tasks
        
        # Simple sequential dependency for now
        for i in range(1, len(tasks)):
            tasks[i].dependencies = [tasks[i-1].task_id]
        
        return tasks
    
    def _assign_specialists(self, tasks: List[SubTask]) -> List[SubTask]:
        """
        Assign specialists based on task type (already done in decompose).
        This method is a placeholder for more sophisticated routing.
        """
        return tasks
    
    async def consult_brain(self, specialist_briefs: List[str]) -> Dict[str, Any]:
        """
        PHASE 17: Strategic Eye Protocol - Reflective Deliberation
        """
        logger.info(f"🧠 [STRATEGIC EYE] Initiating Reflective Deliberation with {len(specialist_briefs)} specialists...")
        
        prompt = self._format_deliberation_prompt(specialist_briefs)
        
        try:
            from unified_core.neural_bridge import get_neural_bridge, NeuralRequest
            bridge = get_neural_bridge()
            request = NeuralRequest(query=prompt, context={"mode": "reflective_deliberation"}, urgency=0.7, pre_fill="{\n    \"path\": \"")
            response = await bridge.think_with_authority(request)
            
            return await self._parse_and_record_deliberation(response.content, len(specialist_briefs))
                
        except Exception as e:
            logger.error(f"Brain consultation error: {e}")
            return {"path": "Emergency", "rationale": f"System error: {e}", "eye": "Recovery", "confidence": 0.1}

    def _format_deliberation_prompt(self, briefs: List[str]) -> str:
        briefs_text = "\n".join([f"- {b}" for b in briefs])
        return f"""<identity>
أنت العقل الاستراتيجي لنظام NOOGH — تحلل رؤى المتخصصين وتحدد المسار الأمثل.
</identity>

<context>
Specialist Advisor Insights:
{briefs_text}
</context>

<methodology>
1. حلل كل رؤية متخصص بشكل مستقل
2. حدد التقاطعات والتناقضات بين الرؤى
3. رتب المسارات حسب: الأثر الأمني > الاستقرار > التطوير الذاتي
4. اختر المسار الذي يحقق أعلى عائد بأقل مخاطرة
</methodology>

<rules>
- لا تقترح مساراً لا يستند إلى بيانات من المتخصصين
- لا تختلق مقاييس أو أرقام — استند فقط إلى ما هو متاح
- إذا كانت البيانات غير كافية، اضبط الثقة تحت 0.5
- أخرج JSON فقط — بدون شرح أو نص إضافي
</rules>

<output_format>
{{ "path": "المجال التقني المحدد", "rationale": "لماذا هذا المسار", "eye": "المقياس الرئيسي للنجاح", "confidence": 0.0-1.0 }}
</output_format>

<reminder>
⚠️ JSON فقط. لا نص قبله أو بعده. الثقة يجب أن تعكس جودة البيانات المتاحة فعلاً.
</reminder>"""

    async def _parse_and_record_deliberation(self, content: str, briefs_count: int) -> Dict[str, Any]:
        import re, json, hashlib
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            return {"path": "Stability", "rationale": "Malformed brain output", "eye": "Uptime", "confidence": 0.5}
            
        try:
            decision = json.loads(json_match.group(0))
            logger.info(f"🚀 [STRATEGIC EYE] Deliberation Complete. Path: {decision.get('path')} | Eye: {decision.get('eye')}")
            
            evol_id = hashlib.sha256(f"evolve:{time.time()}".encode()).hexdigest()[:12]
            if hasattr(self, '_world') and self._world:
                await self._world.record_evolution_step(
                    evolution_id=evol_id,
                    path=decision.get("path", "Unknown"),
                    eye=decision.get("eye", "Observation"),
                    rationale=decision.get("rationale", "Autonomous deliberation"),
                    context={"briefs_count": briefs_count},
                    outcome="Strategic path confirmed by Neural Engine.",
                    success=True
                )
            return decision
        except Exception as e:
            logger.warning(f"Failed to process deliberation result: {e}")
            return {"path": "Stability", "rationale": "Processing error", "eye": "Uptime", "confidence": 0.5}

    def _gen_task_id(self, prefix: str) -> str:
        """Generate unique task ID."""
        return hashlib.sha256(f"{prefix}:{time.time()}".encode()).hexdigest()[:12]
    
    async def execute_plan(self, plan: Plan) -> bool:
        """Execute plan with parallel task execution."""
        plan.started_at = time.time()
        logger.warning(f"🚀 STARTING PLAN execution: {plan.plan_id} (Goal: {plan.goal_description})")
        
        completed_tasks: Set[str] = set()
        failed_tasks: Set[str] = set()
        
        while True:
            ready_tasks = self._get_ready_tasks(plan, completed_tasks)
            
            if not ready_tasks:
                if self._is_plan_finished(plan):
                    break
                logger.warning(f"Plan {plan.plan_id}: No ready tasks but incomplete tasks exist")
                break
            
            # Execute batch
            await self._run_task_batch(ready_tasks, completed_tasks, failed_tasks)
            self._update_dependency_blocks(plan, failed_tasks)
        
        return self._finalize_plan(plan)

    def _get_ready_tasks(self, plan: Plan, completed_tasks: Set[str]) -> List[SubTask]:
        """Identify tasks that are ready for execution."""
        ready = [
            task for task in plan.tasks
            if task.status == TaskStatus.PENDING and task.is_ready(completed_tasks)
        ]
        for t in ready:
            t.status = TaskStatus.READY
        return ready

    def _is_plan_finished(self, plan: Plan) -> bool:
        """Check if all tasks are in a terminal state."""
        return all(t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED] for t in plan.tasks)

    async def _run_task_batch(self, tasks: List[SubTask], completed_tasks: Set[str], failed_tasks: Set[str]):
        """Execute a batch of tasks in parallel."""
        logger.info(f"Executing {len(tasks)} tasks in parallel")
        results = await asyncio.gather(
            *[self._execute_task(task) for task in tasks],
            return_exceptions=True
        )
        
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                task.status = TaskStatus.FAILED
                task.error = str(result)
                failed_tasks.add(task.task_id)
                logger.error(f"Task {task.task_id} FAILED: {result}")
            else:
                task.status = TaskStatus.COMPLETED
                task.result = result
                completed_tasks.add(task.task_id)
                logger.info(f"Task {task.task_id} COMPLETED")

    def _update_dependency_blocks(self, plan: Plan, failed_tasks: Set[str]):
        """Mark tasks as blocked if their dependencies failed."""
        for task in plan.tasks:
            if task.status == TaskStatus.PENDING:
                if any(dep in failed_tasks for dep in task.dependencies):
                    task.status = TaskStatus.BLOCKED
                    logger.warning(f"Task {task.task_id} BLOCKED (dependency failed)")

    def _finalize_plan(self, plan: Plan) -> bool:
        """Mark plan as complete and record in history."""
        plan.completed_at = time.time()
        plan.success = all(t.status == TaskStatus.COMPLETED for t in plan.tasks)
        
        self._plan_history.append(plan)
        if plan.plan_id in self._active_plans:
            del self._active_plans[plan.plan_id]
            
        # Phase 22: Resolve the goal in GravityWell if we have a reference
        if self._gravity and hasattr(self._gravity, 'resolve_goal_by_description'):
            # Strip '[Synthetic:source]' prefix if present to match the original goal description
            import re
            goal_desc = re.sub(r'^\[Synthetic:[^\]]+\]\s*', '', plan.goal_description)
            resolved = self._gravity.resolve_goal_by_description(goal_desc)
            if resolved:
                logger.info(f"Successfully resolved GravityWell goal from plan {plan.plan_id}")
        
        logger.info(f"Plan {plan.plan_id} finished: success={plan.success}, duration={plan.completed_at - plan.started_at:.2f}s")
        return plan.success
    
    async def _execute_task(self, task: SubTask) -> Dict[str, Any]:
        """
        Execute a single task through the real TaskDispatcher.
        Auto-retries once on failure with backoff.
        """
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = time.time()
        
        logger.info(f"Task {task.task_id}: {task.description} (specialist: {task.assigned_specialist})")
        
        # Phase 19: Journaling
        if hasattr(self, '_journal') and self._journal:
            action_type = "analyze" if "Analyze" in task.description or "scan" in task.description.lower() else "execute"
            if "Verify" in task.description: action_type = "verify"
            if "Refactor" in task.description: action_type = "refactor"
            self._journal.record_step(action_type, task.description)
        
        max_attempts = 2
        last_error = None
        
        for attempt in range(max_attempts):
            # Real Execution via TaskDispatcher
            if self._dispatcher and hasattr(task, 'task_type'):
                try:
                    from unified_core.task_dispatcher import TaskPriority
                    
                    task_data = {
                        "description": task.description,
                        "goal_text": task.description
                    }
                    
                    real_task = await self._dispatcher.create_task(
                        task_type=task.task_type,
                        priority=TaskPriority.MEDIUM,
                        data=task_data,
                        specialist_override=task.assigned_specialist
                    )
                    
                    if real_task is None:
                        raise RuntimeError(f"TaskDispatcher failed to create task of type {task.task_type}")
                    
                    # Wait for task completion
                    while real_task.status not in [DispatcherTaskStatus.COMPLETED, DispatcherTaskStatus.FAILED]:
                        await asyncio.sleep(1.0)
                    
                    task.completed_at = time.time()
                    task.result = real_task.result
                    
                    if real_task.status == TaskStatus.FAILED:
                         raise RuntimeError(real_task.error or "Unknown dispatcher error")
                    
                    return real_task.result or {"success": True}
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        backoff = 2 ** attempt
                        logger.warning(f"Task {task.task_id} failed (attempt {attempt+1}), retrying in {backoff}s: {e}")
                        await asyncio.sleep(backoff)
                        continue
                    
                    # Final failure: publish event and raise
                    logger.error(f"PlanningEngine: Task failed after {max_attempts} attempts: {e}")
                    try:
                        from unified_core.integration.event_bus import get_event_bus, EventPriority
                        bus = get_event_bus()
                        bus.publish_sync(
                            "task_failed",
                            {
                                "task_id": task.task_id,
                                "description": task.description[:100],
                                "error": str(e),
                                "attempts": max_attempts,
                            },
                            "PlanningEngine",
                            EventPriority.HIGH
                        )
                    except Exception:
                        pass
                    
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    raise
            else:
                break
        
        # If we reach here, we are missing the dispatcher or task_type
        error_msg = f"Task {task.task_id} cannot be executed: No TaskDispatcher or task_type specified."
        logger.error(f"PlanningEngine: {error_msg}")
        task.status = TaskStatus.FAILED
        task.error = error_msg
        raise RuntimeError(error_msg)
    
    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a plan."""
        plan = self._active_plans.get(plan_id)
        if plan:
            return plan.to_dict()
        
        # Check history
        for p in self._plan_history:
            if p.plan_id == plan_id:
                return p.to_dict()
        
        return None
    
    def get_active_plans(self) -> List[Dict[str, Any]]:
        """Get all active plans."""
        return [p.to_dict() for p in self._active_plans.values()]
