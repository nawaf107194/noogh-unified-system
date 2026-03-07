"""
Reasoning Module - Hierarchical Task Planning
Transforms high-level goals into executable plans.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("unified_core.reasoning")

@dataclass
class PlanStep:
    step_id: str
    description: str
    tool_name: Optional[str] = None
    status: str = "pending" # pending, in_progress, completed, failed

@dataclass
class Plan:
    plan_id: str
    goal_name: str
    steps: List[PlanStep]
    current_step_index: int = 0

class StrategicPlanner:
    """
    COGNITIVE AUTHORITY REMOVED.
    
    This class previously simulated planning via keyword matching.
    That is NOT intelligence. It was template selection.
    
    All decision authority now flows through unified_core.core.GravityWell.
    This class is retained only for API compatibility.
    """
    
    async def decompose(self, goal_name: str, goal_description: str) -> Plan:
        """
        Decompose a goal using real Neural Engine reasoning.
        """
        logger.info(f"🧠 [StrategicPlanner] Decomposing goal: {goal_name}")
        
        try:
            from unified_core.neural_bridge import get_neural_bridge
            bridge = get_neural_bridge()
            
            prompt = f"Decompose this high-level goal into a sequence of executable steps: {goal_name}\nDescription: {goal_description}\nReturn steps as a bulleted list."
            
            # Consult neural engine for real breakdown
            response = await bridge.think_with_authority(
                prompt=prompt,
                context={"action": "goal_decomposition", "goal": goal_name},
                source="strategic_planner_decomposition"
            )
            
            raw_solution = response.get("decision", f"Execute action for {goal_name}")
            
            # Simple parsing of bullet points into PlanSteps
            steps = []
            lines = [l.strip().lstrip('-').lstrip('*').strip() for l in raw_solution.split('\n') if l.strip()]
            
            if lines:
                for line in lines:
                    steps.append(PlanStep(str(uuid.uuid4()), line))
            else:
                steps.append(PlanStep(str(uuid.uuid4()), raw_solution))
                
            return Plan(
                plan_id=str(uuid.uuid4()),
                goal_name=goal_name,
                steps=steps
            )
            
        except Exception as e:
            logger.error(f"Reasoning failure: {e}. Falling back to atomic execution.")
            return Plan(
                plan_id=str(uuid.uuid4()),
                goal_name=goal_name,
                steps=[PlanStep(str(uuid.uuid4()), f"Execute primary objective: {goal_name}")]
            )

    def get_next_step(self, plan: Plan) -> Optional[PlanStep]:
        """Get the next pending step."""
        if plan.current_step_index < len(plan.steps):
            return plan.steps[plan.current_step_index]
        return None

    def mark_step_complete(self, plan: Plan):
        """Advance plan."""
        if plan.current_step_index < len(plan.steps):
            plan.steps[plan.current_step_index].status = "completed"
            plan.current_step_index += 1
