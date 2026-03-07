import datetime
import uuid
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """A single step in the execution plan."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique 8-char ID for the step")
    description: str = Field(..., description="Clear instruction of what to do in this step")
    tool: Literal["code", "command", "research", "browser", "sub_agent"] = Field(
        ..., description="Primary capability needed"
    )
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    result: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list, description="IDs of steps that must complete first")
    attempt_count: int = 0
    max_retries: int = 3
    error_history: List[str] = Field(default_factory=list, description="History of errors for resilience")


class ExecutionPlan(BaseModel):
    """A structured plan containing multiple steps."""

    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    objective: str = Field(..., description="High-level goal of this plan")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    steps: List[PlanStep]
    status: Literal["planning", "executing", "completed", "failed"] = "planning"
    current_step_index: int = 0

    def get_next_step(self) -> Optional[PlanStep]:
            """Returns the next pending step whose dependencies are met."""
            from typing import Set
            import logging

            logger = logging.getLogger(__name__)

            if not isinstance(self.steps, list):
                logger.error("self.steps is not a list")
                raise ValueError("self.steps must be a list")

            completed_ids: Set[str] = {s.id for s in self.steps if s.status == "completed"}

            for step in self.steps:
                if not isinstance(step, PlanStep):
                    logger.error(f"Invalid step type: {type(step)}")
                    raise ValueError("All steps must be instances of PlanStep")

                if step.status == "pending":
                    # Check dependencies
                    if all(isinstance(dep, str) for dep in step.dependencies):
                        if all(dep in completed_ids for dep in step.dependencies):
                            logger.info(f"Returning next step: {step.id}")
                            return step
                    else:
                        logger.error("Dependencies must be a list of strings")
                        raise ValueError("Dependencies must be a list of strings")
            logger.info("No pending step found with all dependencies met.")
            return None
