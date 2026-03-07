import asyncio
import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext
from gateway.app.core.capabilities import Capability, CapabilityRequirement
from gateway.app.core.policy_engine import PolicyEngine
from gateway.app.core.refusal import RefusalResponse
from gateway.app.core.routing import intelligent_router
from gateway.app.core.session_store import get_session_store
from gateway.app.core.task_lifecycle import TaskLifecycle, TaskState

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Standard result format for AgentController."""
    success: bool
    answer: str
    steps: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def outputs(self) -> Dict[str, Any]:
        """Compatibility for unified_core base agents."""
        return {"answer": self.answer}


class AgentController:
    def __init__(self, kernel: AgentKernel, secrets: Dict[str, str]):
        self.kernel = kernel
        self.secrets = secrets
        data_dir = secrets.get("NOOGH_DATA_DIR")
        self.session_store = get_session_store(data_dir=data_dir)
        self.router = intelligent_router  # decoupled router (returns None)

    async def _run_kernel_process(self, *args, **kwargs) -> AgentResult:
        """
        Kernel.process is async.
        This wrapper makes it safe.
        """
        try:
            # kernel.process_task هو التسمية الصحيحة في AgentKernel v2.2
            result_data = await self.kernel.process_task(*args, **kwargs)
            
            # تحويل Dict إلى AgentResult
            if isinstance(result_data, dict):
                return AgentResult(
                    success=result_data.get("success", False),
                    answer=result_data.get("answer", ""),
                    steps=result_data.get("steps", 0),
                    error=result_data.get("error"),
                    metadata=result_data.get("metadata", {})
                )
            return result_data
        except Exception as e:
            logger.error(f"Error in _run_kernel_process: {e}")
            raise

    def process_task(
        self,
        task: str,
        auth: AuthContext,
        force_mode: str = None,
        session_id: str = None,
        mfa_verified: bool = False,
    ) -> AgentResult:
        """Process a task with policy enforcement."""
        # يجب تشغيل الدالة async في event loop
        return asyncio.run(self._process_task_async(
            task, auth, force_mode, session_id, mfa_verified
        ))

    async def _process_task_async(
        self,
        task: str,
        auth: AuthContext,
        force_mode: str = None,
        session_id: str = None,
        mfa_verified: bool = False,
    ) -> AgentResult:
        """Async version of process_task."""
        # Phase 1: Sanitize input
        task = self._sanitize_task_input(task)
        if not task:
            return AgentResult(
                success=False,
                answer="Error: Empty request.",
                steps=0,
                error="EMPTY_TASK",
            )

        # Phase 2: Ensure session exists
        session_id = self._ensure_session(session_id)

        # Phase 3: Initialize task lifecycle
        task_id = str(uuid.uuid4())
        data_dir = self.secrets.get("NOOGH_DATA_DIR")
        lifecycle = TaskLifecycle(task_id, session_id, task, data_dir=data_dir)

        # Phase 4: Get policy decision
        decision = PolicyEngine.decide(task, mode_hint=force_mode)
        lifecycle.transition(
            TaskState.CLASSIFIED, info=f"Decision: {type(decision).__name__}"
        )

        # Phase 5: Handle refusal
        if isinstance(decision, RefusalResponse):
            return self._handle_refusal(decision, lifecycle)

        # Phase 6: Handle capability requirement
        if isinstance(decision, CapabilityRequirement):
            result = await self._handle_capability_requirement(
                task, decision, auth, lifecycle, mfa_verified
            )
            if result:
                return self._finalize_result(
                    result, task_id, session_id, task, decision, lifecycle
                )

        # Phase 7: Handle Deterministic Results (e.g. MATH_DETERMINISTIC)
        if isinstance(decision, dict) and decision.get("__math_result__"):
            result = AgentResult(
                success=True,
                answer=decision.get("answer", "Error calculating math"),
                steps=1,
                metadata={"mode": "math_deterministic", "expression": decision.get("expression")}
            )
            # Use a dummy CapabilityRequirement for finalization
            dummy_decision = CapabilityRequirement(
                required=set(),
                forbidden=set(),
                mode="EXECUTE",
                reason="Deterministic Math result"
            )
            return self._finalize_result(
                result, task_id, session_id, task, dummy_decision, lifecycle
            )

        return AgentResult(
            success=False,
            answer="System Error",
            steps=0,
            error="UnknownDecisionType",
        )

    async def _handle_capability_requirement(
        self,
        task: str,
        decision: CapabilityRequirement,
        auth: AuthContext,
        lifecycle: TaskLifecycle,
        mfa_verified: bool,
    ) -> AgentResult:
        """Handle capability requirement decision."""

        # Update scopes if MFA verified
        if mfa_verified:
            auth.scopes.update(
                {"exec", "fs:read", "fs:write", "tools:use", "memory:rw"}
            )

        # Check MFA requirement for sensitive operations
        mfa_error = self._check_mfa_requirement(decision, mfa_verified)
        if mfa_error:
            return mfa_error

        # Execute based on mode
        if decision.mode == "PLAN":
            return await self._execute_plan_mode(task, decision, auth, lifecycle)
        elif decision.mode == "EXECUTE":
            return await self._execute_exec_mode(task, auth, lifecycle)

        return None

    async def _execute_plan_mode(
        self,
        task: str,
        decision: CapabilityRequirement,
        auth: AuthContext,
        lifecycle: TaskLifecycle,
    ) -> AgentResult:
        """Execute task in planning mode."""
        lifecycle.transition(TaskState.PLANNED, info="Starting Planning")

        planning_instruction = (
            "\n\n[SYSTEM INSTRUCTION: PLANNING MODE ACTIVE]\n"
            "Lead Architect Mode. DO NOT EXECUTE CODE.\n"
            "Produce a detailed EXECUTION PLAN."
        )

        result = await self._run_kernel_process(
            task + planning_instruction, auth
        )

        if result.success:
            lifecycle.transition(TaskState.COMPLETED)
            lifecycle.save_artifact("plan.md", result.answer)
        else:
            lifecycle.transition(TaskState.FAILED)

        return result

    async def _execute_exec_mode(
        self, task: str, auth: AuthContext, lifecycle: TaskLifecycle
    ) -> AgentResult:
        """Execute task in execution mode."""
        lifecycle.transition(TaskState.EXECUTED, info="Starting Execution")

        # Decoupled router: returns None for now
        agent_id = self.router(task)

        result = await self._run_kernel_process(task, auth)

        if not hasattr(result, "metadata") or result.metadata is None:
            result.metadata = {}
        result.metadata["assigned_agent"] = agent_id or "local-kernel"

        if result.success:
            lifecycle.transition(TaskState.COMPLETED)
            lifecycle.save_artifact("report.md", result.answer)
        else:
            lifecycle.transition(TaskState.FAILED)

        return result

    def _sanitize_task_input(self, task: str) -> str:
        """Remove debug/junk patterns from task input."""
        junk_patterns = [
            r"===\s*POLICY DEBUG\s*===",
            r"Matched Triggers:",
            r"Required Capabilities:",
            r"Forbidden Capabilities:",
            r"Simulated PolicyEngine.decide\(\)",
            r"Intent: [A-Z_]+",
            r"Reason: .*",
            r"Confidence: .*",
        ]
        for pattern in junk_patterns:
            task = re.sub(pattern, "", task, flags=re.IGNORECASE).strip()
        return task

    def _ensure_session(self, session_id: str) -> str:
        """Ensure a valid session exists, create if needed."""
        if not session_id:
            session = self.session_store.create_session()
            return session.session_id

        if not self.session_store.get_session(session_id):
            session = self.session_store.create_session()
            return session.session_id

        return session_id

    def _handle_refusal(
        self, decision: RefusalResponse, lifecycle: TaskLifecycle
    ) -> AgentResult:
        """Handle policy refusal."""
        lifecycle.transition(TaskState.REJECTED, info=decision.code)
        return AgentResult(
            success=False,
            answer=f"UNSUPPORTED: {decision.message}",
            steps=0,
            error=decision.code,
        )

    def _check_mfa_requirement(
        self, decision: CapabilityRequirement, mfa_verified: bool
    ) -> AgentResult:
        """Check if MFA is required but not verified."""
        is_sensitive = (
            Capability.CODE_EXEC in decision.required
            or Capability.FS_WRITE in decision.required
            or Capability.REPORT_WRITE in decision.required
        )
        if is_sensitive and not mfa_verified:
            return AgentResult(
                success=False,
                answer="UNSUPPORTED: Security Policy Violation. MFA Required.",
                steps=0,
                error="MFA_REQUIRED",
            )
        return None

    def _finalize_result(
        self,
        result: AgentResult,
        task_id: str,
        session_id: str,
        task: str,
        decision: CapabilityRequirement,
        lifecycle: TaskLifecycle,
    ) -> AgentResult:
        """Finalize result with metadata and session tracking."""
        if not hasattr(result, "metadata") or result.metadata is None:
            result.metadata = {}

        result.metadata["task_id"] = task_id
        result.metadata["session_id"] = session_id
        result.metadata["lifecycle"] = lifecycle.get_lifecycle_list()

        self.session_store.add_task(
            session_id, task, result.answer, decision.mode
        )

        return result

    def _classify_task(self, task: str) -> Any:
        return PolicyEngine.decide(task)
