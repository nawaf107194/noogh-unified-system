"""
Task Dispatcher - Phase 1: Agent Activation
Routes observations from WorldModel to appropriate specialist agents for execution.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("unified_core.task_dispatcher")


class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a task to be executed by a specialist agent."""
    task_id: str
    task_type: str  # e.g., "disk_cleanup", "code_refactor", "security_fix"
    specialist: str  # e.g., "linux", "code", "security"
    priority: TaskPriority
    data: Dict[str, Any]
    created_at: float
    status: TaskStatus = TaskStatus.PENDING
    assigned_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskDispatcher:
    """
    Central task routing and coordination system.
    
    Responsibilities:
    1. Monitor WorldModel for observations requiring action
    2. Route tasks to appropriate specialists
    3. Track task status and results
    4. Aggregate reports from agents
    """
    
    def __init__(self, world_model):
        self.world_model = world_model
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.specialist_registry: Dict[str, Any] = {}
        self._running = False
        self._task_counter = 0
        
        # Task routing rules
        self.routing_rules = {
            # Linux Specialist
            "disk_usage": "linux",
            "cpu_overload": "linux",
            "memory_pressure": "linux",
            "system_update": "linux",
            
            # Security Specialist
            "vulnerability_detected": "security",
            "suspicious_access": "security",
            "port_scan": "security",
            
            # Code Specialist
            "duplicate_code": "code",
            "performance_issue": "code",
            "missing_docs": "code",
            "code_smell": "code",
            
            # Research Specialist
            "knowledge_gap": "research",
            "knowledge_loop": "research",
            
            # AI Specialist
            "model_degradation": "ai",
            "memory_bloat": "ai",
            
            # Forensics Specialist
            "system_anomaly": "forensics",
            "failure_detected": "forensics",
            
            # Science Specialist
            "hypothesis_test": "science",
            "prediction_needed": "science",
            
            # NEW: Network Specialist
            "network_latency": "network",
            "bandwidth_saturation": "network",
            "connection_failure": "network",
            "dns_issue": "network",
            
            # NEW: Database Specialist
            "slow_query": "database",
            "connection_pool_exhausted": "database",
            "deadlock_detected": "database",
            "missing_index": "database",
            "analyze_data": "science",
            "predictive_modeling": "pi",
            "optimize_model": "ai",
            "linux_health": "linux",
            
            # NEW: UX Specialist
            "user_error": "ux",
            "slow_page_load": "ux",
            "failed_interaction": "ux",
            "accessibility_issue": "ux",
            
            # NEW: FinOps Specialist
            "resource_waste": "finops",
            "inefficient_query": "finops",
            "idle_resource": "finops",
            "over_provisioning": "finops",
            
            # NEW: QA Specialist
            "test_failure": "qa",
            "coverage_drop": "qa",
            "flaky_test": "qa",
            "regression_detected": "qa",
        }
    
    def register_specialist(self, name: str, specialist: Any):
        """Register a specialist agent for task assignment."""
        self.specialist_registry[name] = specialist
        logger.info(f"📋 Registered specialist: {name}")
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        self._task_counter += 1
        return f"task_{int(time.time())}_{self._task_counter:04d}"
    
    def classify_observation(self, observation: Any) -> Optional[Dict[str, Any]]:
        """
        Analyze observation and determine if action is needed.
        
        Returns:
            Dict with task_type, priority, and data if action needed
            None if no action needed
        """
        content = observation.content if hasattr(observation, 'content') else observation
        
        # Example classification logic
        if isinstance(content, dict):
            # Disk usage check
            if content.get("type") == "linux_health":
                disk_percent = content.get("disk_percent", 0)
                if disk_percent > 85:
                    return {
                        "task_type": "disk_usage",
                        "priority": TaskPriority.HIGH if disk_percent > 90 else TaskPriority.MEDIUM,
                        "data": {
                            "disk_percent": disk_percent,
                            "threshold": 85,
                            "observation": content
                        }
                    }
                
                # CPU overload check
                load_avg = content.get("load_avg", [0, 0, 0])
                if load_avg[0] > 8.0:
                    return {
                        "task_type": "cpu_overload",
                        "priority": TaskPriority.HIGH,
                        "data": {
                            "load_avg": load_avg,
                            "threshold": 8.0,
                            "observation": content
                        }
                    }
            
            # Security check
            elif content.get("type") == "security_audit":
                issues_count = content.get("issues_found", 0)
                if issues_count > 0:
                    return {
                        "task_type": "vulnerability_detected",
                        "priority": TaskPriority.CRITICAL if issues_count > 5 else TaskPriority.HIGH,
                        "data": {
                            "issues_count": issues_count,
                            "observation": content
                        }
                    }
            
            # Code quality check
            elif content.get("type") == "code_audit":
                if content.get("duplicate_code"):
                    return {
                        "task_type": "duplicate_code",
                        "priority": TaskPriority.MEDIUM,
                        "data": {
                            "duplicates": content.get("duplicate_code"),
                            "observation": content
                        }
                    }
            
            # Knowledge gaps
            elif content.get("type") == "knowledge_loop":
                return {
                    "task_type": "knowledge_loop",
                    "priority": TaskPriority.MEDIUM,
                    "data": {
                        "loop_info": content,
                        "observation": content
                    }
                }
        
        return None
    
    async def create_task(
        self,
        task_type: str,
        priority: TaskPriority,
        data: Dict[str, Any],
        specialist_override: Optional[str] = None
    ) -> Task:
        """Create and queue a new task."""
        # Determine specialist
        if specialist_override:
            specialist = specialist_override
        else:
            specialist = self.routing_rules.get(task_type, "unknown")
            if specialist == "unknown":
                logger.warning(f"⚠️ Unknown task type: {task_type}, skipping")
                return None
        
        # We no longer strictly enforce `self.specialist_registry` here 
        # because the Phase 7+ execution model uses the MessageBus.
        
        # Create task
        task = Task(
            task_id=self._generate_task_id(),
            task_type=task_type,
            specialist=specialist,
            priority=priority,
            data=data,
            created_at=time.time()
        )
        
        # Add to tracking
        self.active_tasks[task.task_id] = task
        
        # Add to execution queue
        await self.task_queue.put(task)
        
        logger.info(
            f"📝 Task created: {task.task_id} "
            f"[{task.task_type}] → {task.specialist} "
            f"(priority: {priority.name})"
        )
        
        return task
    
    async def process_observations(self):
        """Monitor WorldModel and create tasks from observations."""
        logger.info("👁️ Starting observation processor...")
        
        while self._running:
            try:
                # Get recent observations (Async)
                recent_obs = await self.world_model.get_recent_observations(limit=10)
                
                for obs in recent_obs:
                    # Check if already processed
                    obs_id = getattr(obs, 'id', str(hash(str(obs))))
                    if hasattr(self, '_processed_obs') and obs_id in self._processed_obs:
                        continue
                    
                    # Classify and create task if needed
                    task_spec = self.classify_observation(obs)
                    if task_spec:
                        await self.create_task(
                            task_type=task_spec["task_type"],
                            priority=task_spec["priority"],
                            data=task_spec["data"]
                        )
                    
                    # Mark as processed
                    if not hasattr(self, '_processed_obs'):
                        self._processed_obs = set()
                    self._processed_obs.add(obs_id)
                    
                    # Limit processed cache size
                    if len(self._processed_obs) > 1000:
                        self._processed_obs = set(list(self._processed_obs)[-500:])
                
            except Exception as e:
                logger.error(f"❌ Error processing observations: {e}", exc_info=True)
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def dispatch_tasks(self):
        """Dispatch tasks from queue. If no local specialist, use MessageBus via Orchestrator."""
        logger.info("🚀 Starting task dispatcher...")
        from unified_core.orchestration.agent_orchestrator import get_agent_orchestrator
        
        while self._running:
            try:
                # Get next task (with timeout)
                try:
                    task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Get local specialist if it exists
                local_specialist = self.specialist_registry.get(task.specialist)
                orchestrator = get_agent_orchestrator()
                
                # Update status
                task.status = TaskStatus.ASSIGNED
                task.assigned_at = time.time()
                
                target_desc = f"LOCAL:{task.specialist}" if local_specialist else f"BUS:{task.specialist}"
                logger.info(
                    f"🎯 Dispatching {task.task_id} to {target_desc} "
                    f"[{task.task_type}]"
                )
                
                # Execute task (non-blocking)
                asyncio.create_task(
                    self._execute_task(task, local_specialist, orchestrator)
                )
                
            except Exception as e:
                logger.error(f"❌ Error dispatching task: {e}", exc_info=True)
    
    async def _execute_task(self, task: Task, local_specialist: Any, orchestrator: Any):
        """Execute a task with a local specialist or via MessageBus."""
        try:
            task.status = TaskStatus.IN_PROGRESS
            result = None
            
            # 1. Local execution
            if local_specialist and hasattr(local_specialist, 'execute_task'):
                result = await local_specialist.execute_task(task)
            
            # 2. Remote (MessageBus) execution via Orchestrator
            elif orchestrator:
                # Map old dispatcher role abstract names to AgentWorker roles
                role_map = {
                    "linux": "code_executor",  # We'll use code_executor for linux ops
                    "code": "code_executor",
                    "security": "security_monitor",
                    "research": "research_agent",
                }
                mapped_role = role_map.get(task.specialist, task.specialist)
                capability = task.task_type.upper()
                
                # We extract the actual raw dict arguments if it contains them
                args = task.data.get("arguments", task.data)
                
                reply_payload = await orchestrator.request_agent(
                    role=mapped_role,
                    capability=capability,
                    arguments=args,
                    timeout_ms=60000
                )
                
                if reply_payload:
                    result = reply_payload.get("results")
                    if not reply_payload.get("success", False):
                        raise Exception(reply_payload.get("error", "Unknown agent bus error"))
                else:
                    raise Exception(f"Timeout waiting for {mapped_role} to execute {capability}")
            
            else:
                raise AttributeError(
                    f"No local specialist for {task.specialist} and Orchestrator unreachable"
                )
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()
            
            duration = task.completed_at - task.created_at
            logger.info(
                f"✅ Task completed: {task.task_id} "
                f"in {duration:.2f}s"
            )
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = time.time()
            
            logger.error(
                f"❌ Task failed: {task.task_id} - {e}",
                exc_info=True
            )
        
        finally:
            # Move to completed
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            self.completed_tasks.append(task)
            
            # Limit completed tasks history
            if len(self.completed_tasks) > 100:
                self.completed_tasks = self.completed_tasks[-100:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dispatcher statistics."""
        total_completed = len(self.completed_tasks)
        successful = sum(
            1 for t in self.completed_tasks 
            if t.status == TaskStatus.COMPLETED
        )
        failed = sum(
            1 for t in self.completed_tasks 
            if t.status == TaskStatus.FAILED
        )
        
        return {
            "active_tasks": len(self.active_tasks),
            "queue_size": self.task_queue.qsize(),
            "completed_total": total_completed,
            "completed_successful": successful,
            "completed_failed": failed,
            "success_rate": successful / total_completed if total_completed > 0 else 0,
            "registered_specialists": list(self.specialist_registry.keys())
        }
    
    async def start(self):
        """Start the task dispatcher."""
        self._running = True
        logger.info("🚀 Task Dispatcher starting...")
        
        # Start background tasks
        await asyncio.gather(
            self.process_observations(),
            self.dispatch_tasks()
        )
    
    async def stop(self):
        """Stop the task dispatcher."""
        self._running = False
        logger.info("🛑 Task Dispatcher stopping...")
