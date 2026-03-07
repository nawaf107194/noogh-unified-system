import logging
import re
from typing import Any, Dict, List, Optional

from neural_engine.module_interface import (
    ModuleInterface,
    ModuleMetadata,
    ModulePriority,
    ModuleStatus,
    ProcessingResult,
)
from unified_core.tool_definitions import SecurityLevel
from unified_core.tool_registry import get_unified_registry
from unified_core.core.actuators import ActuatorHub

logger = logging.getLogger(__name__)

class ToolExecutionBridge(ModuleInterface):
    """
    Orchestrator module that parses reasoning output and executes tools.
    Bridges THINK -> ACT in the Neural Pipeline.
    """

    def __init__(self):
            super().__init__()
            self.registry = None
            self.actuators = None
            try:
                self._metadata = ModuleMetadata(
                    name="ToolExecutionBridge",
                    version="1.1.0",
                    description="Executes tools with XAI justification enforcement",
                    dependencies=["unified_core.tool_registry", "unified_core.core.actuators"],
                    priority=ModulePriority.CRITICAL,
                    capabilities=["execution", "actuation", "system_control", "governance"],
                )
                if not isinstance(self._metadata.name, str):
                    raise TypeError("The 'name' field in _metadata must be a string.")
                if not isinstance(self._metadata.version, str):
                    raise TypeError("The 'version' field in _metadata must be a string.")
                if not isinstance(self._metadata.description, str):
                    raise TypeError("The 'description' field in _metadata must be a string.")
                if not isinstance(self._metadata.dependencies, list) or not all(isinstance(dep, str) for dep in self._metadata.dependencies):
                    raise TypeError("The 'dependencies' field in _metadata must be a list of strings.")
                if not isinstance(self._metadata.priority, ModulePriority):
                    raise TypeError("The 'priority' field in _metadata must be an instance of ModulePriority.")
                if not isinstance(self._metadata.capabilities, list) or not all(isinstance(cap, str) for cap in self._metadata.capabilities):
                    raise TypeError("The 'capabilities' field in _metadata must be a list of strings.")
            except Exception as e:
                print(f"Error initializing metadata: {e}")

    def get_metadata(self) -> ModuleMetadata:
        return self._metadata

    async def initialize(self, config: Dict[str, Any]) -> bool:
        self.set_status(ModuleStatus.INITIALIZING)
        try:
            self.registry = get_unified_registry()
            self.actuators = ActuatorHub()
            self.set_status(ModuleStatus.READY)
            logger.info("✅ ToolExecutionBridge initialized with XAI Governance.")
            return True
        except Exception as e:
            self.log_error("Failed to initialize ToolExecutionBridge", e)
            return False

    async def validate_input(self, input_data: Any) -> tuple[bool, Optional[str]]:
        if isinstance(input_data, str):
            return True, None
        return False, "Input must be a string containing possible tool calls"

    async def process(self, input_data: Any, context: Dict[str, Any]) -> ProcessingResult:
        """
        Parses THINK output for ACT: markers and executes tools with governance.
        """
        if not self.is_ready():
            return ProcessingResult(False, None, {}, errors=["Module not ready"])

        # 1. Check for execution authorization
        # Nested path: context -> immediate -> parameters
        immediate = context.get("immediate", {})
        parameters = immediate.get("parameters", {})
        execution_authorized = context.get("execution_authorized") or \
                               parameters.get("execution_authorized", False)
        
        # 2. Extract Data
        text = str(input_data)
        tool_calls = self._extract_tool_calls(text)
        justification = self._extract_justification(text)
        
        if not tool_calls:
            return ProcessingResult(True, text, {"execution_triggered": False})

        if not execution_authorized:
            warning_msg = "\n\n⚠️ **تنبيه أمني:** تم اكتشاف محاولة تنفيذ أمر للنظام، ولكن 'وضع التنفيذ' غير مفعّل. يرجى تفعيله وإدخال كلمة السر للمتابعة."
            return ProcessingResult(True, text + warning_msg, {"execution_blocked": "not_authorized"})

        # 3. Execute Tools with Governance
        results = []
        for call in tool_calls:
            tool_name = call['name']
            tool_params = call['params']
            
            # GOVERNANCE: Check Tool Security Level
            tool_def = self.registry.get_schema(tool_name)
            is_high_risk = False
            if tool_def:
                sec_level = tool_def.get("security_level")
                is_high_risk = sec_level in [SecurityLevel.HIGH.value, SecurityLevel.CRITICAL.value]

            # XAI ENFORCEMENT: Enforce justification for high-risk tools
            if is_high_risk:
                # Count words in justification
                words = [w for w in justification.split() if len(w) > 1] # ignore single chars/punctuation
                word_count = len(words)
                
                if word_count < 15:
                    logger.warning(f"Blocking {tool_name}: Insufficient justification ({word_count} words)")
                    results.append({
                        "tool": tool_name,
                        "success": False,
                        "error": f"XAI_GOVERNANCE_BLOCK: Insufficient justification in THINK block ({word_count}/15 words). High-risk actions require clear reasoning.",
                        "blocked": True
                    })
                    continue

            logger.info(f"🚀 Executing tool from chat: {tool_name} (Risk: {is_high_risk})")
            
            try:
                from gateway.app.core.auth import AuthContext
                auth = AuthContext(token="bridge_internal", scopes=["*"]) 
                
                exec_result = await self.registry.execute(tool_name, tool_params, auth_context=auth)
                results.append({
                    "tool": tool_name,
                    "success": exec_result.get("success", False),
                    "output": exec_result.get("output", "Done"),
                    "error": exec_result.get("error")
                })
            except Exception as e:
                logger.error(f"Tool execution failed: {tool_name} -> {e}")
                results.append({
                    "tool": tool_name,
                    "success": False,
                    "error": str(e)
                })

        # 4. Integrate results
        final_text = text
        if any(r.get("blocked") for r in results):
            final_text += "\n\n⛔ **منع التنفيذ (XAI):** تم حجز الأمر لأن تبرير النظام (THINK) غير كافٍ للعمليات عالية الخطورة. يجب أن يقدم الوكيل مبرراً أمنياً أكثر تفصيلاً."

        return ProcessingResult(
            success=True,
            data=final_text,
            metadata={"execution_triggered": True, "results": results, "xai_enforced": True},
        )

    async def get_status(self) -> Dict[str, Any]:
        return {"status": self._status.value, "tools_count": len(self.registry.get_tools()) if self.registry else 0}

    async def shutdown(self) -> bool:
        self.set_status(ModuleStatus.SHUTDOWN)
        return True

    def _extract_justification(self, text: str) -> str:
            """Extracts the content between THINK: and ACT: (or end of string)"""
            if not text:
                return ""
        
            pattern = r"THINK:(.*?)(ACT:|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
            if match:
                return match.group(1).strip()
            else:
                return ""

    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        Regex search for tool calls.
        Prioritizes structured formats over plain markers.
        """
        calls = []
        
        # Combined regex to find all ACT: markers and their associated info
        # Format 1: ACT: tool(args)
        # Format 2: ACT: tool {json}
        # Format 3: ACT: tool
        
        # We search once for all ACT: markers and use the most specific match
        # To avoid duplicates, we'll find all ACT: occurrences and then parse them.
        
        marker_matches = list(re.finditer(r"(ACT|ACTION):\s*([a-zA-Z0-9_\.]+)", text, re.IGNORECASE))
        
        for match in marker_matches:
            name = match.group(2)
            start_pos = match.end()
            remaining = text[start_pos:start_pos + 1000].strip() # Look ahead
            
            params = {}
            # Check for immediate (args)
            if remaining.startswith("("):
                # Try to find matching )
                end_paren = remaining.find(")")
                if end_paren != -1:
                    args_raw = remaining[1:end_paren]
                    # Simple k=v parser
                    for pair in args_raw.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            params[k.strip()] = v.strip().strip("'\"")
            
            # Check for immediate {json}
            elif remaining.startswith("{"):
                # Try to find matching }
                end_json = remaining.find("}")
                if end_json != -1:
                    import json
                    try:
                        params = json.loads(remaining[:end_json+1])
                    except:
                        pass
            
            calls.append({"name": name, "params": params})
        
        return calls
