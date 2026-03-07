import ast
import re
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional


class ResponseType(Enum):
    """Types of agent responses."""

    THINKING = "thinking"
    ACTION = "action"
    REFLECTION = "reflection"
    ANSWER = "answer"
    UNSUPPORTED = "unsupported"
    PROTOCOL_ERROR = "protocol_error"


@dataclass
class ParsedResponse:
    """Parsed agent response."""

    response_type: ResponseType
    content: str
    code: Optional[str] = None
    is_final: bool = False
    is_unsupported: bool = False
    unsupported_reason: Optional[str] = None
    answer: Optional[str] = None
    # Backwards-compatible convenience fields expected by tests
    think: Optional[str] = None
    act: Optional[str] = None
    act_code: Optional[str] = None
    reflect: Optional[str] = None
    violations: List[str] = None


class ProtocolViolation(Exception):
    """Exception raised when agent violates protocol."""



class SecureReActParser:
    """
    Secure parser for ReAct protocol responses with strict validation.
    """

    # Block patterns
    # Block patterns (Relaxed for robustness)
    # Match content until the next keyword or end of string.
    # We use DOTALL in the search methods, so . matches newline.
    THINK_PATTERN = r"THINK:\s*(.*?)(?=\s*(?:ACT:|REFLECT:|ANSWER:|$))"
    ACT_PATTERN = r"ACT:\s*(.*?)(?=\s*(?:REFLECT:|ANSWER:|$))"
    REFLECT_PATTERN = r"REFLECT:\s*(.*?)(?=\s*(?:ANSWER:|$))"
    ANSWER_PATTERN = r"(?:ANSWER|Final Answer):\s*(.*?)(?=\s*(?:THINK:|ACT:|REFLECT:|ANSWER:|Final Answer:|$))"

    # Code block pattern within ACT
    CODE_PATTERN = r"```(?:python)?\n?(.*?)```"

    # Unsupported pattern
    UNSUPPORTED_PATTERN = r"(?:UNSUPPORTED|unsupported|NOT SUPPORTED|not supported)[:\s]*([^\n]+)"

    # Task completion indicators
    COMPLETION_INDICATORS = [
        r"Task complete\.",
        r"task is complete\.",
        r"Task completed\.",
        r"successfully completed\.",
        r"finished\.",
        r"done\.",
    ]

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def parse(self, response_text: str, strict: bool = True, allow_actions: bool = True) -> ParsedResponse:
        return self._parse_impl(response_text, strict=strict, allow_actions=allow_actions)

    def _parse_impl(self, response_text: str, strict: bool = True, allow_actions: bool = True) -> ParsedResponse:
        """Internal parse implementation with decomposed logic for maintainability."""
        # Phase 1: Normalize input
        response_text = self._normalize_text(response_text)

        # Phase 2: Check for unsupported declarations
        unsupported = self._check_unsupported(response_text)
        if unsupported:
            return unsupported

        # Phase 3: Extract all blocks
        blocks = self._extract_blocks(response_text)
        
        # Phase 4: Validate protocol and get violations
        violations = self._validate_protocol(blocks, allow_actions, strict)

        # Phase 5: Determine finality and extract answer
        is_final, final_answer = self._determine_finality(blocks)

        # Phase 6: Extract code from ACT block
        act_content, code_content = self._extract_code(blocks, strict)

        # Phase 7: Check action permissions
        if not allow_actions and code_content and code_content.upper() != "NONE":
            if strict:
                raise ProtocolViolation("Actions not allowed in planning mode")

        # Phase 8: Security checks
        violations.extend(self._security_checks(blocks, act_content, code_content, strict))

        # Phase 9: Determine response type
        response_type = self._determine_response_type(blocks, is_final)

        # Phase 10: Build and return parsed response
        return self._build_response(
            response_type, response_text, code_content, is_final, 
            final_answer, blocks, act_content, violations
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize whitespace and line endings."""
        text = text.strip()
        return re.sub(r"\r\n", "\n", text)

    def _check_unsupported(self, response_text: str) -> Optional[ParsedResponse]:
        """Check for unsupported declarations."""
        match = re.search(self.UNSUPPORTED_PATTERN, response_text, re.IGNORECASE | re.DOTALL)
        if match:
            return ParsedResponse(
                response_type=ResponseType.UNSUPPORTED,
                content=response_text,
                is_unsupported=True,
                unsupported_reason=match.group(1).strip(),
            )
        return None

    def _extract_blocks(self, response_text: str) -> Dict[str, Optional[re.Match]]:
        """Extract all protocol blocks from response."""
        return {
            "think": re.search(self.THINK_PATTERN, response_text, re.DOTALL),
            "act": re.search(self.ACT_PATTERN, response_text, re.DOTALL),
            "reflect": re.search(self.REFLECT_PATTERN, response_text, re.DOTALL),
            "answer": re.search(self.ANSWER_PATTERN, response_text, re.DOTALL),
        }

    def _validate_protocol(
        self, blocks: Dict, allow_actions: bool, strict: bool
    ) -> List[str]:
        """Validate protocol structure and return violations."""
        violations = []
        has_any_block = any(blocks.values())

        # Conversational fallback: no blocks = treat as answer
        if not has_any_block:
            if not allow_actions:
                violations.append("Missing THINK block (Planning mode requires structured thought)")
            return violations  # Fallback handled in _determine_response_type

        # Check for missing THINK
        if not blocks["think"] and has_any_block:
            violations.append("Missing THINK block")

        # Check block order
        violations.extend(self._check_block_order(blocks))

        if violations and strict:
            raise ProtocolViolation(f"Protocol violations: {', '.join(violations)}")

        return violations

    def _check_block_order(self, blocks: Dict) -> List[str]:
        """Verify blocks appear in correct relative order."""
        violations = []
        blocks_found = []
        
        # Define allowed relative order
        # We only care that IF both A and B exist, A comes before B.
        block_map = {
            "think": ("THINK", 0), 
            "act": ("ACT", 1), 
            "reflect": ("REFLECT", 2), 
            "answer": ("ANSWER", 3)
        }
        
        # Get found blocks with their positions
        for key, (name, order_idx) in block_map.items():
            if blocks[key]:
                blocks_found.append({
                    "name": name, 
                    "key": key,
                    "pos": blocks[key].start(), 
                    "order_idx": order_idx
                })

        # Sort by occurrence in text
        blocks_found.sort(key=lambda x: x["pos"])

        # Check if the text order matches the allowed logical order
        # i.e. strict ascending order of 'order_idx' is NOT required (can skip steps),
        # but we shouldn't see order_idx decreasing (e.g. ACT before THINK).
        
        last_idx = -1
        for block in blocks_found:
            curr_idx = block["order_idx"]
            if curr_idx < last_idx:
                violations.append(f"Wrong block order: {block['name']} appeared after a later step.")
            last_idx = curr_idx

        return violations

    def _determine_finality(self, blocks: Dict) -> tuple[bool, Optional[str]]:
        """Determine if this is a final answer."""
        is_final = False
        final_answer = None

        if blocks["answer"]:
            is_final = True
            final_answer = blocks["answer"].group(1).strip()
        elif blocks["reflect"]:
            reflection = blocks["reflect"].group(1).strip()
            for indicator in self.COMPLETION_INDICATORS:
                if re.search(indicator, reflection, re.IGNORECASE):
                    is_final = True
                    if not blocks["answer"]:
                        answer_sections = re.split(r"answer[:\s]*", reflection, flags=re.IGNORECASE)
                        if len(answer_sections) > 1:
                            final_answer = answer_sections[1].strip()
                    break

        return is_final, final_answer

    def _extract_code(self, blocks: Dict, strict: bool) -> tuple[Optional[str], Optional[str]]:
        """Extract code content from ACT block."""
        if not blocks["act"]:
            return None, None

        act_content = blocks["act"].group(1).strip()
        
        if act_content.upper() == "NONE":
            return act_content, None

        # Try to find code block
        code_match = re.search(self.CODE_PATTERN, act_content, re.DOTALL)
        if code_match:
            return act_content, code_match.group(1).strip()

        # Check for Python-like code
        lines = act_content.split("\n")
        python_indicators = ["import ", "def ", "print(", "= ", "for ", "if ", "return "]
        if any(any(ind in line for ind in python_indicators) for line in lines[:3]):
            return act_content, act_content

        # Try to parse as tool call
        return self._try_parse_tool_call(act_content, strict)

    def _try_parse_tool_call(self, act_content: str, strict: bool) -> tuple[str, Optional[str]]:
        """Try to parse ACT content as a tool call."""
        try:
            node = ast.parse(act_content, mode="eval")
            if isinstance(node.body, ast.Call) and isinstance(node.body.func, ast.Name):
                return act_content, None  # Valid tool call
        except Exception:
            pass
        
        if strict and act_content.upper() != "NONE":
            raise ProtocolViolation(
                "ACT block should contain code in triple backticks, a tool call, or 'NONE'"
            )
        return act_content, None

    def _security_checks(
        self, blocks: Dict, act_content: Optional[str], code_content: Optional[str], strict: bool
    ) -> List[str]:
        """Perform security checks on content."""
        violations = []

        # THINK block size
        if blocks["think"]:
            think_text = blocks["think"].group(1) or ""
            if len(think_text) > MAX_RESPONSE_SIZE:
                msg = "THINK block exceeds size limit"
                if strict:
                    raise ProtocolViolation(msg)
                violations.append(msg)

        # ACT block size
        if act_content and len(act_content) > MAX_BLOCK_SIZE:
            msg = "ACT block exceeds size limit"
            if strict:
                raise ProtocolViolation(msg)
            violations.append(msg)

        # Code content checks
        if code_content:
            violations.extend(self._check_code_security(code_content, strict))

        return violations

    def _check_code_security(self, code_content: str, strict: bool) -> List[str]:
        """Check code content for security issues."""
        violations = []

        if len(code_content) > MAX_CODE_SIZE:
            msg = "Code block exceeds size limit"
            if strict:
                raise ProtocolViolation(msg)
            violations.append(msg)

        code_lower = code_content.lower()
        
        # Forbidden patterns
        forbidden_checks = [
            ("__import__", "Forbidden use of __import__ detected"),
            ("eval(", "Forbidden use of eval() detected"),
            ("subprocess", "Forbidden subprocess usage detected"),
            ("os.system", "Forbidden subprocess usage detected"),
            ("open(", "Forbidden direct file open detected; use tools instead"),
        ]
        
        for pattern, message in forbidden_checks:
            if pattern in code_lower:
                violations.append(message)

        # Infinite loop detection
        if re.search(r"while\s+True\s*:", code_content):
            violations.append("Forbidden infinite loop suspected")

        return violations

    def _determine_response_type(self, blocks: Dict, is_final: bool) -> ResponseType:
        """Determine the response type based on blocks."""
        has_any_block = any(blocks.values())
        
        # Conversational fallback
        if not has_any_block:
            return ResponseType.ANSWER
            
        if is_final or blocks["answer"]:
            return ResponseType.ANSWER
        elif blocks["act"]:
            return ResponseType.ACTION
        elif blocks["reflect"]:
            return ResponseType.REFLECTION
        elif blocks["think"]:
            return ResponseType.THINKING
        else:
            return ResponseType.PROTOCOL_ERROR

    def _build_response(
        self, response_type: ResponseType, content: str, code_content: Optional[str],
        is_final: bool, final_answer: Optional[str], blocks: Dict,
        act_content: Optional[str], violations: List[str]
    ) -> ParsedResponse:
        """Build the final ParsedResponse object."""
        return ParsedResponse(
            response_type=response_type,
            content=content,
            code=code_content,
            is_final=is_final,
            answer=final_answer,
            is_unsupported=False,
            think=(blocks["think"].group(1).strip() if blocks["think"] else None),
            act=act_content,
            act_code=code_content,
            reflect=(blocks["reflect"].group(1).strip() if blocks["reflect"] else None),
            violations=violations,
        )

    def _safe_parse(self, response_text: str, strict: bool = True, allow_actions: bool = True):
        """Backward-compatible wrapper used by tests to avoid async/timeouts."""
        # Call the internal implementation directly to avoid recursion when
        # `parse` is monkeypatched by tests.
        return self._parse_impl(response_text, strict=strict, allow_actions=allow_actions)

    @lru_cache(maxsize=128)
    def generate_correction_prompt(self, violations: tuple) -> str:
        """Generate (and cache) a correction prompt for given violations."""
        vlist = "\n".join(violations)
        return (
            f"ERROR: Protocol violation(s) detected:\n{vlist}\nPlease follow THINK -> ACT -> REFLECT -> ANSWER format."
        )

    def extract_action(self, parsed_response: ParsedResponse) -> Optional[Dict[str, Any]]:
        """
        Extract action information from parsed response.

        Returns:
            Dict with keys: tool, args, code (for exec_python)
        """
        if parsed_response.response_type != ResponseType.ACTION:
            return None

        code = parsed_response.act_code or parsed_response.code

        if not code:
            return self._extract_ast_tool_call(parsed_response)

        return self._extract_code_action(parsed_response, code)

    def _extract_ast_tool_call(self, parsed_response: ParsedResponse) -> Dict[str, Any]:
        """Attempt to parse act content as a plain AST tool call (legacy/simple)."""
        act_text = (parsed_response.act or parsed_response.content or "").strip()
        if not act_text or act_text.upper() == "NONE":
            return {"tool": "none", "args": {}, "code": None, "metadata": {}}

        try:
            node = ast.parse(act_text, mode="eval")
            if isinstance(node.body, ast.Call) and isinstance(node.body.func, ast.Name):
                tool_name = node.body.func.id
                args: Dict[str, Any] = {}

                # Positional args -> arg0, arg1
                for i, a in enumerate(node.body.args):
                    try:
                        val = ast.literal_eval(a)
                    except Exception:
                        val = None
                    args[f"arg{i}"] = val

                # Keyword args
                for kw in node.body.keywords:
                    k = kw.arg
                    try:
                        v = ast.literal_eval(kw.value)
                    except Exception:
                        v = None
                    args[k] = v

                # Protocol Violations check
                if getattr(parsed_response, "violations", None):
                    return {
                        "tool": "reject",
                        "args": {},
                        "code": None,
                        "metadata": {
                            "reason": "; ".join(parsed_response.violations),
                            "violations": parsed_response.violations,
                        },
                    }

                return {"tool": tool_name, "args": args, "code": None, "metadata": {"toolcall": True}}
        except Exception:
            pass

        return {"tool": "none", "args": {}, "code": None, "metadata": {}}

    def _extract_code_action(self, parsed_response: ParsedResponse, code: str) -> Dict[str, Any]:
        """Build metadata and return dict for code-exec path."""
        metadata: Dict[str, Any] = {
            "code_length": len(code),
            "safe": bool(self.validate_code_safety(code)),
        }

        # If parser recorded violations, reject the action
        if getattr(parsed_response, "violations", None):
            return {
                "tool": "reject",
                "args": {},
                "code": code,
                "metadata": {
                    "reason": "; ".join(parsed_response.violations),
                    "violations": parsed_response.violations,
                },
            }

        return {"tool": "exec_python", "args": {"code": code}, "code": code, "metadata": metadata}

    def validate_code_safety(self, code: str) -> bool:
        """
        Basic safety validation for Python code.
        Returns True if code appears safe, False if potentially dangerous.
        """
        if not code:
            return True

        # Convert to lowercase for case-insensitive checks
        code_lower = code.lower()

        # Dangerous imports/patterns
        dangerous_patterns = [
            r"import\s+os\s*$",
            r"import\s+subprocess\s*$",
            r"from\s+os\s+import",
            r"from\s+subprocess\s+import",
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__\s*\(",
            r"open\s*\([^)]*\)",
            r"subprocess\.run",
            r"os\.system",
            r"os\.popen",
            r"os\.spawn",
            r"os\.fork",
            r"os\.kill",
            r"sys\.exit",
            r"quit\s*\(",
            r"exit\s*\(",
            r"while\s+True:",
            r"import\s+socket",
            r"import\s+requests",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code_lower, re.MULTILINE):
                return False

        # Check for infinite loops (simplistic check)
        lines = code.split("\n")
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.startswith("while") and ":" in line_stripped:
                # Check if loop has a break condition in the next few lines
                next_lines = lines[i + 1 : i + 4]
                if not any("break" in l.lower() for l in next_lines):
                    # Check for sleep calls that might prevent infinite CPU usage
                    if not any("time.sleep" in l.lower() for l in next_lines):
                        return False

        return True

    def sanitize_response(self, response_text: str) -> str:
        """
        Sanitize response by removing potentially harmful content.
        """
        # Remove code blocks that might contain dangerous code
        sanitized = re.sub(self.CODE_PATTERN, "[CODE BLOCK REMOVED]", response_text, flags=re.DOTALL)

        # Remove dangerous patterns even outside code blocks
        dangerous_patterns = [
            r"import\s+os\s*[\n;]",
            r"import\s+subprocess\s*[\n;]",
            r"eval\s*\(",
            r"exec\s*\(",
        ]

        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "[REMOVED]", sanitized, flags=re.IGNORECASE)

        # Limit response length
        MAX_LENGTH = 10000
        if len(sanitized) > MAX_LENGTH:
            sanitized = sanitized[:MAX_LENGTH] + "\n...[truncated]"

        return sanitized.strip()


# Security constants expected by tests
MAX_RESPONSE_SIZE = 50_000
MAX_BLOCK_SIZE = 10_000
MAX_CODE_SIZE = 20_000


def create_secure_parser(strict_mode: bool = True) -> SecureReActParser:
    """Factory helper used in tests to create a hardened parser."""
    return SecureReActParser(strict_mode=strict_mode)
