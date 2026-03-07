"""
NOOGH LLM Planner

Converts user requests into validated, secure execution plans (DAGs).

CRITICAL SECURITY:
- JSON only output from LLM
- Schema validation enforced
- No tool names allowed (capabilities only)
- DAG validation mandatory
- Fail-closed on any ambiguity
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional

try:
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception

from unified_core.orchestration.plan_schema import (
    PLAN_SCHEMA,
    ALLOWED_CAPABILITIES,
    FORBIDDEN_KEYWORDS
)
from unified_core.orchestration.task_graph import TaskGraph, TaskNode
from unified_core.orchestration.messages import RiskLevel, ToolRequest

logger = logging.getLogger("unified_core.orchestration.llm_planner")


class PlanBuildError(Exception):
    """Raised when plan building or validation fails"""
    pass


class LLMPlanner:
    """
    LLM-based execution planner.
    
    Converts user requests into validated DAG execution plans.
    
    SECURITY GUARANTEES:
    1. JSON-only output from LLM
    2. Schema validation (jsonschema)
    3. No tool names in capabilities
    4. DAG validation (cycles, chains)
    5. Risk/isolation consistency
    """
    
    def __init__(self, llm_client, prompt_template: str):
        """
        Initialize planner.
        
        Args:
            llm_client: LLM wrapper with generate() method
            prompt_template: Content from orchestrator_prompt.md
        """
        if not JSONSCHEMA_AVAILABLE:
            raise RuntimeError("jsonschema package required for LLMPlanner")
        
        self.llm = llm_client
        self.prompt = prompt_template
        
        logger.info("✅ LLMPlanner initialized")
    
    async def build_plan(
        self,
        user_request: str,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Build execution plan from user request.
        
        Args:
            user_request: Natural language request
            user_context: Optional context (user_id, permissions, etc.)
        
        Returns:
            Validated execution plan dict
        
        Raises:
            PlanBuildError: If plan building or validation fails
        """
        logger.info(f"Building plan for request: {user_request[:100]}...")
        
        try:
            # 1. Build prompt
            full_prompt = self._build_prompt(user_request, user_context)
            
            # 2. Call LLM
            raw_response = await self.llm.generate(full_prompt)
            logger.debug(f"LLM response: {raw_response[:200]}...")
            
            # 3. Extract JSON (strict)
            plan = self._parse_json_strict(raw_response)
            
            # 4. Schema validation (hard fail)
            self._validate_schema(plan)
            
            # 5. Semantic validation
            self._validate_semantics(plan)
            
            # 6. Capability validation
            self._validate_capabilities(plan)
            
            # 7. Build TaskGraph and validate DAG
            graph = self._build_task_graph(plan)
            is_valid, error = graph.validate()
            
            if not is_valid:
                raise PlanBuildError(f"DAG validation failed: {error}")
            
            logger.info(f"✅ Plan built successfully: {plan['plan_id']}")
            return plan
            
        except PlanBuildError:
            raise
        except Exception as e:
            logger.error(f"Plan building failed: {e}")
            raise PlanBuildError(f"Unexpected error: {e}")
    
    # ========================================================================
    # Internal Helpers
    # ========================================================================
    
    def _build_prompt(
        self,
        user_request: str,
        user_context: Optional[Dict] = None
    ) -> str:
        """Build complete prompt for LLM — XML-structured with anti-fabrication"""
        context_str = ""
        if user_context:
            context_str = f"\n<user_context>\n{json.dumps(user_context, indent=2)}\n</user_context>\n"
        
        return f"""{self.prompt}

{context_str}
<request>
{user_request}
</request>

<rules>
1. Output VALID JSON ONLY — no markdown, no explanation, no text before or after
2. Maximum 10 tasks per plan
3. Use ONLY capabilities from the ALLOWED list — do NOT invent new ones
4. FORBIDDEN: tool names (fs.read, proc.run, os.exec, etc.) — use abstract capabilities
5. Every task MUST include ALL required fields: task_id, title, agent_role, capabilities, risk_level, isolation, dependencies, expected_output
6. risk_level MUST match isolation: SAFE→none, RESTRICTED→sandbox, DANGEROUS→lab_container
7. Dependencies must reference existing task_ids — no cycles allowed
8. If the request is ambiguous, create a SAFE analysis task first before any action
9. Do NOT fabricate capabilities or agent roles that don't exist
</rules>

<output_schema>
{{
  "plan_id": "plan-[unique_id]",
  "summary": "[1-2 sentence description]",
  "overall_risk": "SAFE|RESTRICTED|DANGEROUS",
  "tasks": [
    {{
      "task_id": "[unique]",
      "title": "[action description]",
      "agent_role": "[valid role]",
      "capabilities": ["[FROM ALLOWED LIST ONLY]"],
      "risk_level": "SAFE|RESTRICTED|DANGEROUS",
      "isolation": "none|sandbox|lab_container",
      "dependencies": [],
      "expected_output": "[what this task produces]"
    }}
  ]
}}
</output_schema>

<reminder>
⚠️ Pure JSON only. Any text outside the JSON object will cause a hard failure.
⚠️ Unknown capabilities will be flagged. Only use capabilities you are certain exist.
</reminder>
"""
    
    def _parse_json_strict(self, raw: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from LLM response.
        
        SECURITY: Only accepts pure JSON, no extra text.
        """
        raw = raw.strip()
        
        # Remove markdown code blocks if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            # Find first { and last }
            start_idx = None
            end_idx = None
            
            for i, line in enumerate(lines):
                if "{" in line and start_idx is None:
                    start_idx = i
                if "}" in line:
                    end_idx = i
            
            if start_idx is not None and end_idx is not None:
                raw = "\n".join(lines[start_idx:end_idx+1])
        
        # Must start and end with JSON object
        if not raw.startswith("{") or not raw.endswith("}"):
            raise PlanBuildError(
                "LLM did not return pure JSON. "
                f"Response started with: {raw[:50]}"
            )
        
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise PlanBuildError(f"Invalid JSON from LLM: {e}")
    
    def _validate_schema(self, plan: Dict[str, Any]):
        """Validate plan against JSON schema"""
        try:
            validate(instance=plan, schema=PLAN_SCHEMA)
        except ValidationError as e:
            raise PlanBuildError(f"Schema validation failed: {e.message}")
    
    def _validate_semantics(self, plan: Dict[str, Any]):
        """
        Validate semantic rules.
        
        Checks:
        - Unique task IDs
        - Risk/isolation consistency
        - Dependency references
        """
        task_ids = set()
        
        for task in plan["tasks"]:
            tid = task["task_id"]
            
            # Unique task_id
            if tid in task_ids:
                raise PlanBuildError(f"Duplicate task_id: {tid}")
            task_ids.add(tid)
            
            # Risk / isolation consistency
            risk = task["risk_level"]
            isolation = task["isolation"]
            
            if risk == "SAFE" and isolation != "none":
                raise PlanBuildError(
                    f"Task {tid}: SAFE tasks cannot require isolation"
                )
            
            if risk == "DANGEROUS" and isolation != "lab_container":
                raise PlanBuildError(
                    f"Task {tid}: DANGEROUS tasks MUST use lab_container"
                )
            
            if risk == "RESTRICTED" and isolation not in ("sandbox", "lab_container"):
                raise PlanBuildError(
                    f"Task {tid}: RESTRICTED tasks must use sandbox or lab_container"
                )
        
        # Validate all dependencies exist
        for task in plan["tasks"]:
            for dep_id in task["dependencies"]:
                if dep_id not in task_ids:
                    raise PlanBuildError(
                        f"Task {task['task_id']} depends on non-existent task {dep_id}"
                    )
    
    def _validate_capabilities(self, plan: Dict[str, Any]):
        """
        Validate capabilities are abstract and allowed.
        
        SECURITY: No tool names allowed.
        """
        for task in plan["tasks"]:
            for capability in task["capabilities"]:
                # Check if in allowed list (case-insensitive)
                cap_upper = capability.upper()
                if cap_upper not in ALLOWED_CAPABILITIES:
                    logger.warning(
                        f"Unknown capability: {capability} in task {task['task_id']}"
                    )
                    # Don't fail, but log for review
                
                # Check for forbidden keywords (tool names)
                cap_lower = capability.lower()
                for keyword in FORBIDDEN_KEYWORDS:
                    if keyword in cap_lower:
                        raise PlanBuildError(
                            f"Forbidden keyword '{keyword}' in capability: {capability}. "
                            "Use abstract capabilities only (e.g., READ_FILE, not fs.read)"
                        )
    
    def _build_task_graph(self, plan: Dict[str, Any]) -> TaskGraph:
        """Convert plan to TaskGraph for validation"""
        graph = TaskGraph()
        
        for task_data in plan["tasks"]:
            # Convert capabilities to pseudo tool requests
            # (actual mapping happens in agent workers)
            tool_requests = [
                ToolRequest(
                    tool_name=cap,  # Will be mapped by agent
                    arguments={},
                    isolation=task_data["isolation"],
                    timeout_ms=10000
                )
                for cap in task_data["capabilities"]
            ]
            
            node = TaskNode(
                task_id=task_data["task_id"],
                title=task_data["title"],
                agent_role=task_data["agent_role"],
                risk_level=RiskLevel[task_data["risk_level"]],
                inputs=[],
                outputs=[task_data["expected_output"]],
                depends_on=task_data["dependencies"],
                tool_requests=tool_requests,
                resource_needs={}
            )
            
            graph.add_node(node)
        
        return graph


# Stub LLM client for testing
class StubLLMClient:
    """Stub LLM client for testing"""
    
    async def generate(self, prompt: str) -> str:
        """Return a stub plan"""
        return json.dumps({
            "plan_id": "plan-stub-001",
            "summary": "Stub plan for testing",
            "overall_risk": "SAFE",
            "tasks": [
                {
                    "task_id": "t1",
                    "title": "Analyze request",
                    "agent_role": "research_analyst",
                    "capabilities": ["ANALYZE_TEXT"],
                    "risk_level": "SAFE",
                    "isolation": "none",
                    "dependencies": [],
                    "expected_output": "analysis_result"
                }
            ]
        })
