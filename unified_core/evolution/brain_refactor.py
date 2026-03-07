"""
Brain-Assisted Refactoring - LLM-Powered Code Improvement
Version: 1.0.0
Part of: Self-Directed Layer (Phase 17.5)

Uses the Neural Engine (Brain) to generate intelligent code fixes
based on detected issues from CodeAnalyzer.
"""

import ast
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .code_analyzer import CodeIssue, CodeAnalyzer, get_code_analyzer
from .ledger import EvolutionProposal, ProposalType, ProposalStatus, get_evolution_ledger
from . import evolution_config as config
from .promoted_targets import get_promoted_targets

logger = logging.getLogger("unified_core.evolution.brain_refactor")


@dataclass
class RefactorRequest:
    """Request for code refactoring."""
    issue: CodeIssue
    file_content: str
    function_content: str
    request_id: str = field(default_factory=lambda: f"refactor_{int(time.time())}")


@dataclass
class RefactorResult:
    """Result of refactoring request."""
    success: bool
    original_code: str
    refactored_code: str
    explanation: str
    confidence: float
    issue: CodeIssue


class BrainAssistedRefactoring:
    """
    Uses the Brain (LLM) to generate intelligent code fixes.
    
    Flow:
    1. CodeAnalyzer detects issue
    2. Extract relevant code context
    3. Send to Brain with specific prompt
    4. Receive refactored code
    5. Create Evolution Proposal with the fix
    """
    
    # Prompts for different issue types — v13 XML-aligned format
    # Common indentation rule injected into ALL prompts
    _INDENT_RULE = (
        "\n- CRITICAL: Preserve EXACT indentation. If the original `def` starts at column 0, "
        "your output MUST start at column 0. If it starts at column 4 (class method), "
        "your output MUST start at column 4. DO NOT add or remove leading spaces.\n"
    )
    
    REFACTOR_PROMPTS = {
        "long_function": """Refactor this long Python function by extracting helper functions.
Problem: {description}

ORIGINAL CODE:
```python
{code}
```

RULES:
- Keep the EXACT same function name and signature
- CRITICAL: Preserve EXACT indentation — if `def` starts at column N, keep column N
- Each extracted helper does ONE thing
- Preserve the same return type and behavior
- Add brief docstrings
- Output ONLY the refactored code inside ```python block""",

        "high_complexity": """Simplify this complex Python function.
Problem: {description}
Current complexity: {complexity}

ORIGINAL CODE:
```python
{code}
```

RULES:
- Keep the EXACT same function name and signature
- CRITICAL: Preserve EXACT indentation — if `def` starts at column N, keep column N
- Use early returns to reduce nesting
- Extract complex conditions into named boolean variables
- Break nested loops where possible
- The refactored code must be AT LEAST as long as the original
- Output ONLY the refactored code inside ```python block""",

        "deep_nesting": """Reduce the nesting depth of this Python function.
Problem: Deep nesting ({nesting} levels)

ORIGINAL CODE:
```python
{code}
```

RULES:
- Keep the EXACT same function name and signature
- CRITICAL: Preserve EXACT indentation — if `def` starts at column N, keep column N
- Use guard clauses and early returns
- Extract deeply nested blocks into helper functions
- Output ONLY the refactored code inside ```python block""",

        "missing_docstring": """Add a docstring to this Python function.

ORIGINAL CODE:
```python
{code}
```

RULES:
- Keep the EXACT same function name and signature
- CRITICAL: Preserve EXACT indentation — if `def` starts at column N, keep column N
- Describe what the function does, its parameters, and return value
- Keep docstring concise (1-3 lines)
- Output ONLY the complete function with docstring inside ```python block""",

        "too_many_params": """Restructure this Python function to reduce its parameter count.
Problem: {params} parameters (too many)

ORIGINAL CODE:
```python
{code}
```

RULES:
- CRITICAL: Preserve EXACT indentation — if `def` starts at column N, keep column N
- Group related parameters into a dataclass or TypedDict
- Or use **kwargs with sensible defaults
- Keep the same behavior and return type
- Output ONLY the refactored code inside ```python block""",

        "cognitive_logic": """Improve this Python function's robustness and clarity.
Problem: {description}

ORIGINAL CODE:
```python
{code}
```

RULES:
- Keep the EXACT same function name and signature
- CRITICAL: Preserve the EXACT indentation level of the original code
  - If the original starts with 4 spaces (class method), your output MUST also start with 4 spaces
  - If the original starts with 0 spaces (module-level function), keep 0 spaces
  - Every line inside the function body must be indented relative to the def line
- Do NOT add new class definitions, import statements, or decorators

IMPROVE (things that add real value):
- Handle edge cases that would cause crashes (empty list, None, missing key)
- Replace silent failures with logged warnings
- Simplify complex conditionals using early returns
- Use guard clauses to reduce nesting depth
- Replace magic numbers/strings with named constants

DO NOT (these are anti-patterns):
- Do NOT add isinstance() checks on parameters typed by the function signature
- Do NOT add isinstance() checks on self.attributes set in __init__
- Do NOT wrap single lines in try/except — only wrap blocks that can actually fail
- Do NOT add try/except around .lower(), .strip(), or basic string ops
- Do NOT add "if not isinstance(x, object)" — everything is an object in Python
- Do NOT use print() for error logging — use logger.error() or logger.warning()
- Do NOT add redundant validation on internal/private attributes

EXAMPLE OF BAD refactoring (DO NOT do this):
```python
# BAD — this adds no value:
if not isinstance(query, str):
    raise TypeError("query must be a string")
try:
    query_lower = query.lower()
except Exception as e:
    raise ValueError(f"Failed: {{e}}")
```

EXAMPLE OF GOOD refactoring:
```python
# GOOD — this handles real edge cases:
if not query.strip():
    logger.warning("Empty query received, returning default")
    return default_result
```

Output ONLY the refactored function inside ```python block""",

        "cognitive_evolution": """<identity>
You are the NOOGH evolutionary brain. Your mission is to improve the autonomous system's performance.
</identity>

<task>
Analyze the system state and provide development recommendations.
Health data: {health_data}
Decision log: {decision_log}
</task>

<rules>
1. Focus on practical, actionable improvements
2. Prioritize recommendations by impact
3. Do not propose changes that break stability
</rules>

<output_format>
{{"recommendations": [...], "priority": "high/medium/low", "confidence": 0.0-1.0}}
</output_format>"""
    }
    
    def __init__(self, neural_bridge=None):
        """
        Initialize with optional NeuralBridge reference.
        
        If not provided, will attempt to get global instance.
        """
        self.neural_bridge = neural_bridge
        self.ledger = get_evolution_ledger()
        self.code_analyzer = get_code_analyzer()
        
        # Stats
        self.requests_made = 0
        self.successful_refactors = 0
        self.failed_refactors = 0
        
        # Reusable NeuralEngineClient (avoids session leak)
        self._neural_client = None
        self._neural_client_url = None  # Track for env-change detection
        self._neural_client_mode = None
        
        # 🧠 MEMORY: Track refactored files to avoid re-analyzing
        self._refactored_files: Dict[str, float] = {}  # filepath -> timestamp
        self._refactored_functions: Dict[str, float] = {}  # "file:function" -> timestamp
        self._refactor_cooldown = config.REFACTOR_COOLDOWN_SECONDS
        
        # v2.0: Warm-start from ledger — prevents re-proposing already-refactored functions
        self._warm_start_from_ledger()
        
        # v4.1: Persistent promoted targets (never expires)
        self._promoted_targets = get_promoted_targets()
        
        from .code_analyzer import ArchitectureMap
        self.arch_map = ArchitectureMap()
        
        logger.info(f"🧠 BrainAssistedRefactoring initialized (memory: {len(self._refactored_functions)} cooldown + {self._promoted_targets.count()} permanent)")
    
    def _get_neural_bridge(self):
        """Get or create NeuralBridge instance."""
        if self.neural_bridge is None:
            try:
                from ..neural_bridge import get_neural_bridge
                self.neural_bridge = get_neural_bridge()
            except Exception as e:
                logger.error(f"Failed to get NeuralBridge: {e}")
                return None
        return self.neural_bridge
    
    def _warm_start_from_ledger(self):
        """Populate _refactored_functions from ledger history.
        
        Reads promoted/executed proposals to rebuild the cooldown cache,
        ensuring Brain doesn't re-propose functions already refactored
        in previous sessions.
        """
        try:
            from .ledger import ProposalStatus
            for proposal in self.ledger.proposals.values():
                if proposal.status in (ProposalStatus.PROMOTED, ProposalStatus.EXECUTED):
                    target = proposal.targets[0] if proposal.targets else ''
                    func = proposal.metadata.get('function', '') if proposal.metadata else ''
                    if target and func:
                        ts = proposal.executed_at or proposal.created_at or 0
                        func_key = f"{target}:{func}"
                        # Keep the latest timestamp
                        if ts > self._refactored_functions.get(func_key, 0):
                            self._refactored_functions[func_key] = ts
        except Exception as e:
            logger.warning(f"Warm-start from ledger failed: {e}")
        
        # v1.4: Clean up old entries to prevent unbounded growth
        self._cleanup_old_refactors()
    
    def _cleanup_old_refactors(self):
        """Remove _refactored_functions entries older than 48h.
        
        Keeps the dict bounded while ensuring the cooldown window
        (typically 1h) is still respected.
        """
        import time
        cutoff = time.time() - (48 * 3600)  # 48 hours
        before = len(self._refactored_functions)
        self._refactored_functions = {
            k: v for k, v in self._refactored_functions.items()
            if v > cutoff
        }
        removed = before - len(self._refactored_functions)
        if removed > 0:
            logger.info(f"🧹 Cleaned {removed} stale entries from refactor memory")
    
    def _extract_function_code(self, filepath: str, start_line: int, end_line: int) -> str:
        """Extract function code from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Ensure we're within bounds
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            
            return ''.join(lines[start_idx:end_idx])
        except Exception as e:
            logger.error(f"Failed to extract code: {e}")
            return ""
    
    def _detect_indent_level(self, code: str) -> int:
        """Detect the indentation level (number of leading spaces) of the first 'def' line."""
        for line in code.split('\n'):
            stripped = line.lstrip()
            if stripped.startswith('def ') or stripped.startswith('async def '):
                return len(line) - len(stripped)
        return 0
    
    def _reindent_code(self, code: str, target_indent: int) -> str:
        """Re-indent code to match the target indentation level.
        
        If the refactored code starts at indent=0 but the original was at indent=4,
        this adds 4 spaces to every line.
        """
        current_indent = self._detect_indent_level(code)
        if current_indent == target_indent:
            return code
        
        delta = target_indent - current_indent
        lines = code.split('\n')
        result = []
        for line in lines:
            if not line.strip():  # Empty lines stay empty
                result.append(line)
            elif delta > 0:  # Need to add indentation
                result.append(' ' * delta + line)
            else:  # Need to remove indentation
                result.append(line[abs(delta):])
        return '\n'.join(result)
    
    def _resolve_import_path(self, module_path: str, source_file: str) -> Optional[str]:
        """Resolve a dotted import path to an actual file path.
        
        Example: '..core.world_model' from evolution/brain_refactor.py
                 → unified_core/core/world_model.py
        """
        import importlib.util
        try:
            # Try absolute import first
            spec = importlib.util.find_spec(module_path)
            if spec and spec.origin:
                return spec.origin
        except (ModuleNotFoundError, ValueError):
            pass
        
        # Fallback: resolve relative to source file's directory
        src_root = source_file
        if 'src/' in src_root:
            src_root = src_root[:src_root.index('src/') + 4]
        else:
            src_root = str(Path(source_file).parent.parent.parent)
        
        # Convert dots to path
        parts = module_path.replace('.', '/') + '.py'
        candidate = Path(src_root) / parts
        if candidate.exists():
            return str(candidate)
        
        # Try as package
        candidate = Path(src_root) / module_path.replace('.', '/') / '__init__.py'
        if candidate.exists():
            return str(candidate)
        
        return None
    
    def _resolve_dependencies(self, issue: CodeIssue, tree: ast.AST, source: str) -> List[str]:
        """Resolve and extract interfaces of dependencies used by the target function.
        
        Strategy:
        1. Find the target function's AST node
        2. Scan for attribute accesses (self.xxx.method())
        3. Trace self.xxx to __init__ assignments to find the type 
        4. Resolve the import to an actual file
        5. Extract class method signatures from that file
        
        Returns list of dependency context lines (max 3 dependencies).
        """
        dep_lines = []
        
        try:
            # Step 1: Collect all imports in the file
            import_map = {}  # name -> (module_path, original_name)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        local_name = alias.asname or alias.name
                        import_map[local_name] = (node.module, alias.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        local_name = alias.asname or alias.name
                        import_map[local_name] = (alias.name, alias.name.split('.')[-1])
            
            # Step 2: Find __init__ to map self.xxx = SomeClass(...)
            attr_types = {}  # attr_name -> class_name
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                            for stmt in ast.walk(item):
                                # Match: self.xxx = SomeClass(...) or self.xxx = get_something()
                                if (isinstance(stmt, ast.Assign) and 
                                    len(stmt.targets) == 1 and
                                    isinstance(stmt.targets[0], ast.Attribute) and
                                    isinstance(stmt.targets[0].value, ast.Name) and
                                    stmt.targets[0].value.id == 'self'):
                                    
                                    attr_name = stmt.targets[0].attr
                                    # Check if value is a Call to a known import
                                    if isinstance(stmt.value, ast.Call):
                                        if isinstance(stmt.value.func, ast.Name):
                                            attr_types[attr_name] = stmt.value.func.id
                                        elif isinstance(stmt.value.func, ast.Attribute):
                                            attr_types[attr_name] = stmt.value.func.attr
            
            # Step 3: Find the target function and scan for self.xxx usage
            used_attrs = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == issue.function:
                        for child in ast.walk(node):
                            # Match: self.xxx.method() or self.xxx.prop
                            if (isinstance(child, ast.Attribute) and
                                isinstance(child.value, ast.Attribute) and
                                isinstance(child.value.value, ast.Name) and
                                child.value.value.id == 'self'):
                                used_attrs.add(child.value.attr)
                        break
            
            # Step 4: For each used self.xxx, resolve the class and get its interface
            resolved = 0
            for attr_name in used_attrs:
                if resolved >= 3:  # Max 3 dependencies to stay within budget
                    break
                
                class_name = attr_types.get(attr_name)
                if not class_name or class_name not in import_map:
                    continue
                
                module_path, original_name = import_map[class_name]
                
                # Resolve to actual file
                file_path = self._resolve_import_path(module_path, issue.file)
                if not file_path or not Path(file_path).exists():
                    continue
                
                # Parse the dependency file and extract class signatures
                try:
                    with open(file_path, 'r') as f:
                        dep_source = f.read()
                    dep_tree = ast.parse(dep_source)
                    
                    methods = []
                    for dep_node in ast.walk(dep_tree):
                        if isinstance(dep_node, ast.ClassDef) and dep_node.name == original_name:
                            for item in dep_node.body:
                                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    if item.name.startswith('_') and item.name != '__init__':
                                        continue  # Skip private methods
                                    args = [a.arg for a in item.args.args[:4]]
                                    methods.append(f"{item.name}({', '.join(args)})")
                                    if len(methods) >= 8:
                                        break
                            break
                    
                    if methods:
                        dep_rel = file_path.split('src/')[-1] if 'src/' in file_path else Path(file_path).name
                        dep_lines.append(
                            f"[DEPENDENCY: self.{attr_name} → {original_name} from {dep_rel}]\n"
                            f"  Methods: {', '.join(methods)}"
                        )
                        resolved += 1
                        
                except Exception:
                    continue
            
            # Step 5: Also check direct function calls from imports used in the target
            # (e.g., get_bridge(), get_evolution_memory())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == issue.function:
                        for child in ast.walk(node):
                            if (isinstance(child, ast.Call) and 
                                isinstance(child.func, ast.Name) and
                                child.func.id in import_map and
                                resolved < 3):
                                func_name = child.func.id
                                module_path, original_name = import_map[func_name]
                                dep_lines.append(f"  Uses: {func_name}() from {module_path}")
                                resolved += 1
                        break
            
        except Exception as e:
            logger.debug(f"Dependency resolution failed: {e}")
        
        return dep_lines
    
    def _build_rich_context(self, issue: CodeIssue) -> str:
        """Build rich project context for the Brain (v5.0 + v5.1 deps).
        
        Extracts via AST:
        - Class name containing the function
        - Key imports from the file
        - Sibling method signatures (names + params)
        - Error history from EvolutionMemory
        - v5.1: Dependency interfaces (classes used by the function)
        """
        parts = []
        
        try:
            with open(issue.file, 'r') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # 1. Find containing class
            class_name = None
            sibling_sigs = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name == issue.function:
                                class_name = node.name
                            # Collect sibling signatures (max 10)
                            if len(sibling_sigs) < 10:
                                args = [a.arg for a in item.args.args[:4]]  # Max 4 params
                                sig = f"{item.name}({', '.join(args)})"
                                sibling_sigs.append(sig)
            
            # If not in a class, collect module-level functions
            if class_name is None:
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if len(sibling_sigs) < 10:
                            args = [a.arg for a in node.args.args[:4]]
                            sig = f"{node.name}({', '.join(args)})"
                            sibling_sigs.append(sig)
            
            # 2. Extract key imports (first 5 unique modules)
            imports = []
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names[:2]:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
                if len(imports) >= 8:
                    break
            imports = list(dict.fromkeys(imports))[:5]  # Unique, max 5
            
            # 3. Build context string
            rel_path = issue.file.split('src/')[-1] if 'src/' in issue.file else issue.file.split('/')[-1]
            
            parts.append("[PROJECT CONTEXT]")
            if class_name:
                parts.append(f"- Class: {class_name}")
            parts.append(f"- File: {rel_path}")
            if imports:
                parts.append(f"- Imports: {', '.join(imports)}")
            if sibling_sigs:
                # Show siblings but exclude the target function itself
                others = [s for s in sibling_sigs if not s.startswith(issue.function + '(')]
                if others:
                    parts.append(f"- Sibling methods: {', '.join(others[:8])}")
            
            # 4. Error history from EvolutionMemory
            try:
                from .evolution_memory import get_evolution_memory
                memory = get_evolution_memory()
                penalty = memory.get_scar_penalty(issue.file)
                if penalty > 0:
                    failures = penalty // 5
                    parts.append(f"- ⚠️ Error history: {failures} past failures on this file (penalty: {penalty})")
                
                # v9: Inject specific rejection reasons so Brain learns from past mistakes
                recent_failures = memory.get_recent_failures(issue.file, issue.function, limit=3)
                if recent_failures:
                    parts.append("- ⛔ PREVIOUS REJECTIONS (avoid these patterns):")
                    for reason in recent_failures:
                        parts.append(f"  • {reason}")
            except Exception:
                pass
            
            # 5. v5.1: Dependency interfaces — follow imports used in the function
            dep_lines = self._resolve_dependencies(issue, tree, source)
            if dep_lines:
                parts.append("")  # Blank line separator
                parts.extend(dep_lines)
            
        except Exception as e:
            logger.debug(f"Rich context failed for {issue.file}: {e}")
            return ""
        
        return '\n'.join(parts)
    
    def _build_prompt(self, issue: CodeIssue, code: str) -> str:
        """Build the appropriate prompt for the issue type."""
        template = self.REFACTOR_PROMPTS.get(
            issue.issue_type, 
            self.REFACTOR_PROMPTS.get("high_complexity")  # Default
        )
        
        # Detect original indentation and add to prompt context
        orig_indent = self._detect_indent_level(code)
        indent_hint = ""
        if orig_indent > 0:
            indent_hint = (
                f"\n[⚠️ INDENTATION — MANDATORY]\n"
                f"The `def` line starts at column {orig_indent} (it is a class method).\n"
                f"Your output MUST start `def` at exactly column {orig_indent}.\n"
                f"Every body line must be at column {orig_indent + 4} or deeper.\n"
                f"DO NOT move `def` to column 0 or column {orig_indent + 4}.\n"
            )
        else:
            indent_hint = (
                "\n[⚠️ INDENTATION — MANDATORY]\n"
                "The `def` line starts at column 0 (module-level function).\n"
                "Your output MUST start `def` at column 0. DO NOT indent it.\n"
            )
        
        # orig_indent is returned via the prompt and used by caller
        # (no longer stored on self — thread-safety fix v4.0)
        
        # Add Architectural Context
        layer = self.arch_map.get_layer_for_path(issue.file)
        arch_context = ""
        if layer is not None:
            layer_info = self.arch_map.layers.get(layer, {})
            arch_context = f"\n- Layer: {layer} ({layer_info.get('component', 'Unknown')} — {layer_info.get('focus', 'Unknown')})"
        
        # v5.0: Rich project context (class, imports, siblings, errors)
        rich_context = self._build_rich_context(issue)
        if rich_context:
            # Merge arch_context into rich_context
            rich_context = rich_context + arch_context
        elif arch_context:
            rich_context = f"\n[ARCHITECTURAL CONTEXT]{arch_context}"
        
        return template.format(
            code=code,
            description=issue.description,
            complexity=issue.metrics.get("complexity", "unknown"),
            nesting=issue.metrics.get("nesting", "unknown"),
            params=issue.metrics.get("params", "unknown")
        ) + indent_hint + "\n" + rich_context
    
    async def request_refactor(self, issue: CodeIssue) -> Optional[RefactorResult]:
        """
        Request code refactoring from the Brain.
        
        Returns RefactorResult with the suggested fix, or None if failed.
        """
        bridge = self._get_neural_bridge()
        if bridge is None:
            logger.error("No NeuralBridge available")
            return None
        
        self.requests_made += 1
        
        # Local indent tracking (v4.0: no longer on self — thread-safe)
        orig_indent = 0
        
        try:
            # Get the analysis for line numbers
            file_analysis = None
            for cached_path, analysis in self.code_analyzer._cache.items():
                if cached_path == issue.file:
                    file_analysis = analysis
                    break
            
            # Find the function
            start_line = issue.line
            end_line = start_line + 50  # Default
            
            if file_analysis:
                for func in file_analysis.functions:
                    if func.name == issue.function:
                        start_line = func.start_line
                        end_line = func.end_line
                        break
            
            # Extract function code
            original_code = self._extract_function_code(issue.file, start_line, end_line)
            if not original_code:
                logger.error("Could not extract code")
                return None
            
            # Detect original indentation for re-indentation after Brain response
            orig_indent = self._detect_indent_level(original_code)
            
            # Build prompt
            prompt = self._build_prompt(issue, original_code)
            
            # Request from Brain using direct completion (bypasses chatbot system prompt)
            logger.info(f"🧠 Requesting refactor for {issue.function} ({issue.issue_type})")
            
            if self._neural_client is None:
                from ..neural_bridge import NeuralEngineClient
                import os
                # Always use Teacher (32B) for evolution, not local 7B
                teacher_url = os.getenv("NOOGH_TEACHER_URL", os.getenv("NEURAL_ENGINE_URL"))
                teacher_mode = os.getenv("NOOGH_TEACHER_MODE", os.getenv("NEURAL_ENGINE_MODE", "local"))
                self._neural_client = NeuralEngineClient(base_url=teacher_url, mode=teacher_mode)
                self._neural_client_url = teacher_url
                self._neural_client_mode = teacher_mode
                logger.info(f"🧠 Brain client: {teacher_mode} → {teacher_url}")
            else:
                # v1.4: Recreate if env vars changed (hot reload support)
                import os
                current_url = os.getenv("NOOGH_TEACHER_URL", os.getenv("NEURAL_ENGINE_URL"))
                current_mode = os.getenv("NOOGH_TEACHER_MODE", os.getenv("NEURAL_ENGINE_MODE", "local"))
                if current_url != self._neural_client_url or current_mode != self._neural_client_mode:
                    from ..neural_bridge import NeuralEngineClient
                    logger.info(f"🔄 Brain client env changed: {self._neural_client_mode}→{current_mode}, recreating")
                    self._neural_client = NeuralEngineClient(base_url=current_url, mode=current_mode)
                    self._neural_client_url = current_url
                    self._neural_client_mode = current_mode
            client = self._neural_client
            
            # Build messages — NO pre-fill, let model output complete function
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert Python engineer specializing in production code quality. "
                        "You receive the function to refactor along with PROJECT CONTEXT showing "
                        "the class, imports, sibling methods, and error history. "
                        "Use this context to make informed improvements — respect the class structure, "
                        "use existing imports, and avoid patterns that previously failed. "
                        "Write clean, minimal refactoring — improve real edge cases but NEVER add "
                        "isinstance() on typed parameters, NEVER wrap single lines in try/except, "
                        "and NEVER use print() instead of logger. "
                        "Output ONLY the refactored code, no explanations."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            from .evolution_config import BRAIN_MAX_TOKENS, BRAIN_REQUEST_TIMEOUT, MAX_EXTRACTION_RETRIES
            # v1.3: Retry loop for truncated/broken responses
            refactored_code = ""
            code_source = ""
            
            for attempt in range(1 + MAX_EXTRACTION_RETRIES):
                result = await client.complete(
                    messages, 
                    max_tokens=BRAIN_MAX_TOKENS,
                    timeout=BRAIN_REQUEST_TIMEOUT
                )
                
                if not (result.get("success") and result.get("content")):
                    break  # LLM call itself failed — no retry
                
                code_source = result["content"]
                finish_reason = result.get("finish_reason", "unknown")
                logger.info(
                    f"🔍 complete() returned {len(code_source)} chars "
                    f"(attempt {attempt+1}, finish={finish_reason})"
                )
                logger.info(f"🔍 code_source preview: {code_source[:200]}")
                
                # v1.4: Skip extraction on known truncation — retry immediately
                if finish_reason == "length":
                    logger.warning(
                        f"⚠️ Response truncated (finish_reason=length) for "
                        f"{issue.function} — skipping extraction, retrying..."
                    )
                    if attempt < MAX_EXTRACTION_RETRIES:
                        continue
                    # Final attempt also truncated — log full response
                    logger.warning(
                        f"📋 Full truncated response ({len(code_source)} chars): "
                        f"{code_source[:2000]}"
                    )
                    break
                
                refactored_code = self._extract_code_from_response(
                    code_source, expected_indent=orig_indent
                )
                
                if refactored_code:
                    break  # Valid code extracted
                
                if attempt < MAX_EXTRACTION_RETRIES:
                    logger.warning(
                        f"⚠️ Extraction failed (attempt {attempt+1}/{1+MAX_EXTRACTION_RETRIES}) "
                        f"for {issue.function} — retrying..."
                    )
            
            # Re-indent to match original code's indentation level
            if refactored_code and orig_indent > 0:
                refactored_code = self._reindent_code(refactored_code, orig_indent)
            
            # CRITICAL: Reject if no valid Python code was extracted
            if not refactored_code:
                self.failed_refactors += 1
                error_reason = result.get('error', 'extraction failed') if not result.get("success") else "extraction failed after retries"
                logger.warning(f"Brain returned non-code response for {issue.function} — rejected ({error_reason})")
                return None
            
            # v1.4: Validate function signature matches original
            sig_ok, sig_msg = self._validate_function_signature(
                refactored_code, issue.function, original_code
            )
            if not sig_ok:
                self.failed_refactors += 1
                logger.warning(f"🚫 Signature mismatch for {issue.function}: {sig_msg}")
                return None
            
            self.successful_refactors += 1
            
            # 📚 Record for distillation (Teacher → Student training)
            try:
                from .distillation_collector import get_distillation_collector
                collector = get_distillation_collector()
                collector.record_refactor_success(
                    prompt=prompt,
                    response=code_source,
                    extracted_code=refactored_code,
                    issue_type=issue.issue_type,
                    function_name=issue.function,
                    file_path=issue.file
                )
            except Exception as dist_err:
                logger.debug(f"Distillation recording skipped: {dist_err}")
            
            # 🧠 Record in Cognitive Journal
            try:
                from ..cognitive_journal import get_cognitive_journal
                journal = get_cognitive_journal()
                journal.record(
                    entry_type="decision",
                    content=f"Refactored {issue.function} in {Path(issue.file).name}: {issue.issue_type}",
                    context={"issue": issue.description, "file": issue.file, "confidence": 0.8},
                    confidence=0.8,
                    tags=["refactoring", issue.issue_type],
                )
            except Exception:
                pass
            
            return RefactorResult(
                success=True,
                original_code=original_code,
                refactored_code=refactored_code,
                explanation="Refactored via direct LLM completion",
                confidence=0.8,
                issue=issue
            )
                
        except Exception as e:
            self.failed_refactors += 1
            logger.error(f"Refactor request failed: {e}")
            return None
    
    def _validate_function_signature(
        self, refactored_code: str, expected_name: str, original_code: str
    ) -> tuple:
        """v1.4: Verify the refactored function's signature matches the original.
        Returns (ok: bool, message: str).
        """
        import ast, textwrap
        
        try:
            new_tree = ast.parse(textwrap.dedent(refactored_code))
            orig_tree = ast.parse(textwrap.dedent(original_code))
        except SyntaxError:
            return True, "skip — parse error"  # Let compile() handle it
        
        # Find function defs in both
        new_funcs = [n for n in ast.walk(new_tree) if isinstance(n, ast.FunctionDef)]
        orig_funcs = [n for n in ast.walk(orig_tree) if isinstance(n, ast.FunctionDef)]
        
        if not new_funcs:
            return False, "no function definition found in refactored code"
        
        new_func = new_funcs[0]
        
        # Check name matches
        if new_func.name != expected_name:
            return False, f"name changed: {expected_name} → {new_func.name}"
        
        # Check parameter count (if we have the original)
        if orig_funcs:
            orig_func = orig_funcs[0]
            orig_args = len(orig_func.args.args)
            new_args = len(new_func.args.args)
            if orig_args != new_args:
                return False, f"arg count changed: {orig_args} → {new_args}"
        
        return True, "OK"
    
    def _extract_code_from_response(self, response: str, expected_indent: int = 0) -> str:
        """Extract Python code from LLM response, stripping boilerplate.
        
        Args:
            response: Raw LLM response text
            expected_indent: Expected indentation of the def line (v4.0: passed as param)
        
        Returns empty string if no valid code found.
        """
        code = ""
        
        # Try to find ```python code block
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end > start:
                code = response[start:end].strip()
        
        # Try generic code block
        if not code and "```" in response:
            start = response.find("```") + 3
            newline = response.find("\n", start)
            if newline > start and newline - start < 20:
                start = newline + 1
            end = response.find("```", start)
            if end > start:
                code = response[start:end].strip()
        
        # Fall back to raw response if it contains Python code
        if not code and ("def " in response or "async def " in response):
            code = response.strip()
        
        if not code:
            logger.warning("Brain response contained no valid Python code — rejected")
            return ""
        
        # --- Post-processing: strip boilerplate the 7B model tends to add ---
        cleaned_lines = []
        in_function = False
        
        for line in code.split("\n"):
            stripped = line.strip()
            
            # Skip standalone imports added by model (not part of function)
            if not in_function and (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            
            # Skip class declarations (model rewrites entire class)
            if not in_function and stripped.startswith("class ") and stripped.endswith(":"):
                continue
            
            # Skip if __name__ blocks
            if stripped.startswith('if __name__'):
                break
            
            # Skip logging.basicConfig
            if stripped.startswith("logging.basicConfig"):
                continue
            
            # Skip standalone exception class definitions before the function
            if not in_function and stripped.startswith("class ") and "Exception" in stripped:
                continue
            
            # Skip empty lines before function starts
            if not in_function and not stripped:
                continue
            
            # Skip decorator-like patterns and docstrings outside function
            if not in_function and stripped.startswith("@"):
                continue
            
            # Detect function start
            if stripped.startswith("def ") or stripped.startswith("async def "):
                in_function = True
            
            if in_function:
                cleaned_lines.append(line)
        
        result = "\n".join(cleaned_lines).strip()
        
        # Final validation: must contain a function definition
        if "def " not in result:
            logger.warning("Cleaned code contains no function definition — rejected")
            return ""
        
        # ── AUTO-INDENT-FIX ──────────────────────────────────────────────
        # If Brain shifted indentation, fix it automatically instead of 
        # letting it fail at canary stage (saves a full approval+canary cycle)
        # v4.0: expected_indent passed as parameter (thread-safe)
        if expected_indent > 0:
            # Detect current indent of the def line
            actual_indent = None
            for line in result.split('\n'):
                s = line.lstrip()
                if s.startswith(('def ', 'async def ')):
                    actual_indent = len(line) - len(s)
                    break
            
            if actual_indent is not None and actual_indent != expected_indent:
                drift = actual_indent - expected_indent
                logger.info(
                    f"🔧 Auto-fixing INDENT_DRIFT: col {actual_indent} → col {expected_indent} "
                    f"(shift={'−' if drift > 0 else '+'}{abs(drift)})"
                )
                fixed_lines = []
                for line in result.split('\n'):
                    if not line.strip():
                        fixed_lines.append(line)
                        continue
                    
                    current_spaces = len(line) - len(line.lstrip())
                    new_spaces = max(0, current_spaces - drift)
                    fixed_lines.append(' ' * new_spaces + line.lstrip())
                
                result = '\n'.join(fixed_lines)
        # ─────────────────────────────────────────────────────────────
        
        # Detect truncated output (model hit max_tokens)
        open_parens = result.count('(') - result.count(')')
        open_brackets = result.count('[') - result.count(']')
        if open_parens > 2 or open_brackets > 2:
            logger.warning(f"Code appears truncated (unmatched parens={open_parens}, brackets={open_brackets}) — rejected")
            return ""
        
        # Reject if last line ends with incomplete token
        last_line = result.strip().split('\n')[-1].strip()
        if last_line.endswith('\\') or last_line.endswith(',') or last_line.endswith('('):
            logger.warning(f"Code appears truncated (last line: '{last_line[:50]}') — rejected")
            return ""
        
        # v1.3: Syntax validation — catches truncated/broken code early
        # Note: dedent before compile — class methods at col 4+ are invalid as top-level code
        try:
            import textwrap
            compile(textwrap.dedent(result), '<brain_refactor>', 'exec')
        except SyntaxError as e:
            logger.warning(
                f"Code failed syntax check: {e.msg} at line {e.lineno} — rejected"
            )
            return ""
        
        return result
    
    def create_proposal_from_refactor(self, result: RefactorResult) -> Optional[EvolutionProposal]:
        """Create an Evolution Proposal from a refactor result."""
        if not result.success:
            return None
        
        diff = f"""# Refactoring: {result.issue.function}
# Issue: {result.issue.issue_type}
# File: {result.issue.file}
# Confidence: {result.confidence:.0%}

--- ORIGINAL ---
{result.original_code}

+++ REFACTORED +++
{result.refactored_code}
"""
        
        # Dynamic risk calculation
        risk = self._calculate_risk(result)
        
        proposal = EvolutionProposal(
            proposal_id=f"brain_refactor_{int(time.time())}_{hash(result.issue.file) % 10000:04d}_{hash(result.issue.function) % 10000:04d}",
            proposal_type=ProposalType.CODE,
            description=f"[BRAIN] Refactor {result.issue.function}: {result.issue.issue_type}",
            scope="code",
            targets=[result.issue.file],
            diff=diff,
            risk_score=risk,
            expected_benefit=f"Fix {result.issue.issue_type}, improve code quality",
            rollback_plan=f"Revert to original code",
            rationale=f"Brain-generated fix with {result.confidence:.0%} confidence (risk={risk})"
        )
        
        # Store full refactored code in metadata
        proposal.metadata = {
            "original_code": result.original_code,
            "refactored_code": result.refactored_code,
            "start_line": result.issue.line,
            "function": result.issue.function,
            "confidence": result.confidence
        }
        
        return proposal
    
    def _calculate_risk(self, result: RefactorResult) -> float:
        """Calculate dynamic risk score for a refactoring proposal.
        
        Factors:
        - Issue severity: LOW=15, MEDIUM=25, HIGH=35, CRITICAL=45
        - Confidence: higher confidence → lower risk
        - Code size: larger diffs are riskier
        - Core file: core/ files get +10 risk
        """
        severity_risk = {
            "LOW": 15, "MEDIUM": 25, "HIGH": 35, "CRITICAL": 45
        }.get(result.issue.severity, 30)
        
        # Confidence reduces risk (0.8 confidence → -8 risk)
        confidence_bonus = int(result.confidence * 10)
        
        # Larger code changes are riskier 
        diff_lines = len(result.refactored_code.split('\n'))
        size_risk = min(diff_lines // 10, 10)  # Cap at +10
        
        # Core files get extra scrutiny
        core_risk = 10 if '/core/' in result.issue.file else 0
        
        risk = severity_risk - confidence_bonus + size_risk + core_risk
        return max(10, min(90, risk))  # Clamp 10-90
    
    async def process_critical_issues(self, max_issues: int = 5, target_area: str = "all") -> List[EvolutionProposal]:
        """
        Process code issues and generate refactoring proposals.
        
        Scans ALL project files and generates intelligent improvements.
        Limited to max_issues per cycle to avoid overwhelming the Brain.
        """
        proposals = []
        
        # v1.5: Periodic cleanup of stale refactor memory (every 10 cycles)
        if self.requests_made % 10 == 0:
            self._cleanup_old_refactors()
        
        # Get project analysis (now scans entire src/)
        project = self.code_analyzer.analyze_project()
        critical = self.code_analyzer.get_critical_issues(project)
        
        # Filter to supported issue types with function names
        supported = [
            i for i in critical 
            if i.function
        ]
        
        # PRIORITY FILTERING
        priority_issues = []
        secondary_issues = []
        
        ai_keywords = ['reasoner', 'world_model', 'governor', 'bridge', 'planning', 'prediction']
        important_dirs = ['unified_core/core/', 'gateway/app/', 'neural_engine/', 'unified_core/evolution/']
        
        for issue in supported:
            path = issue.file.lower()
            
            # Skip test, verify, audit files
            if any(skip in path for skip in ['test', 'verify', 'audit', 'cache', '_backup', '.orig', '.rej']):
                continue
            
            # v4.1: Check persistent promoted targets (permanent skip)
            if self._promoted_targets.contains(issue.file, issue.function):
                logger.debug(f"⏭️ Skipping permanently promoted: {issue.file.split('/')[-1]}:{issue.function}")
                continue
            
            # Check if already refactored recently (cooldown-based)
            func_key = f"{issue.file}:{issue.function}"
            if time.time() - self._refactored_functions.get(func_key, 0) < self._refactor_cooldown:
                continue
            
            # Categorize by priority
            is_ai = any(k in path for k in ai_keywords)
            is_important = any(d in issue.file for d in important_dirs)
            
            if is_ai:
                priority_issues.insert(0, issue)  # Top priority
            elif is_important:
                priority_issues.append(issue)  # High priority
            else:
                secondary_issues.append(issue)
        
        # === SMART TARGET SELECTION (v5.0: Diversity-Aware) ===
        # Use evolution memory to prioritize files that historically succeed
        # v5.0: Boost undiscovered files + enforce file diversity
        try:
            from .evolution_memory import get_evolution_memory
            memory = get_evolution_memory()
            
            # v5.0: Build set of files already in ledger for novelty detection
            ledger_files = set()
            try:
                for p in self.ledger.proposals.values():
                    for t in getattr(p, 'targets', []):
                        ledger_files.add(t)
            except Exception:
                pass  # If ledger structure differs, skip
            
            def _score_issue(issue):
                """Score issue by historical success + priority + novelty."""
                base_score = 0
                path = issue.file.lower()
                
                # Priority boost
                is_ai = any(k in path for k in ai_keywords)
                is_important = any(d in issue.file for d in important_dirs)
                
                if is_ai:
                    base_score += 30
                elif is_important:
                    base_score += 15
                
                # Skip fragile files
                if memory.should_skip_target(issue.file):
                    return -1  # Will be filtered out
                
                # Historical success penalty/boost
                scar_penalty = memory.get_scar_penalty(issue.file)
                base_score -= scar_penalty  # More failures = lower score
                
                # v5.0: Novelty boost — files never proposed before get +20
                if issue.file not in ledger_files:
                    base_score += 20
                
                # v5.0: Random tiebreaker (prevents same files winning every cycle)
                base_score += random.randint(0, 15)
                
                return base_score
            
            # Score all issues
            scored = [(issue, _score_issue(issue)) for issue in (priority_issues + secondary_issues)]
            
            # Filter out fragile (score = -1) and sort by score descending
            prioritized = [
                issue for issue, score in sorted(scored, key=lambda x: x[1], reverse=True)
                if score >= 0
            ]
            
            logger.info(f"🎯 Smart targeting: {len(prioritized)} candidates "
                        f"({len(scored) - len(prioritized)} skipped as fragile/scarred)")
            
        except Exception as e:
            # Fallback to simple random if memory unavailable
            logger.debug(f"Smart targeting unavailable, using random: {e}")
            random.shuffle(priority_issues)
            random.shuffle(secondary_issues)
            prioritized = priority_issues + secondary_issues
        
        # === v5.0: FILE DIVERSITY ENFORCEMENT ===
        # Select at most 1 target per file to prevent concentration
        seen_files = set()
        diverse_batch = []
        for issue in prioritized:
            basename = issue.file.split('/')[-1]
            if basename not in seen_files:
                diverse_batch.append(issue)
                seen_files.add(basename)
                if len(diverse_batch) >= max_issues:
                    break
        
        logger.info(f"🧠 Processing {len(diverse_batch)}/{len(prioritized)} issues "
                     f"(Focus: {target_area}, diverse files: {len(seen_files)})")
        
        # === PARALLEL EXECUTION ===
        # Send all Brain requests concurrently instead of one-by-one
        batch = diverse_batch
        
        # Prepare tasks
        async def _process_one(issue):
            """Process a single issue and return (issue, result) or None."""
            logger.info(f"🎯 Selected: {issue.file.split('/')[-1]}:{issue.function}")
            
            # Force cognitive prompt for AI components
            if any(k in issue.file.lower() for k in ai_keywords):
                issue.issue_type = "cognitive_logic"
            
            result = await self.request_refactor(issue)
            return (issue, result) if result else None
        
        # Fire all requests in parallel
        import asyncio
        tasks = [_process_one(issue) for issue in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful proposals
        for res in results:
            if isinstance(res, Exception):
                logger.warning(f"🧠 Parallel refactor failed: {res}")
                continue
            if res is None:
                continue
            
            issue, result = res
            proposal = self.create_proposal_from_refactor(result)
            if proposal:
                success, _ = self.ledger.record_proposal(proposal)
                if success:
                    proposals.append(proposal)
                    func_key = f"{issue.file}:{issue.function}"
                    self._refactored_functions[func_key] = time.time()
        
        return proposals
    
    async def trigger_self_improvement(self) -> Dict[str, Any]:
        """
        Trigger UC3 self-improvement cycle via /self/auto-improve endpoint.
        
        This uses the built-in Neural Engine improvement capabilities.
        """
        import aiohttp
        import os
        
        try:
            token = os.getenv("NOOGH_INTERNAL_TOKEN", "dev-token-noogh-2026")
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8001/self/auto-improve",
                    json={},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"🧠 Self-improvement triggered: {data.get('status')}")
                        return {
                            "success": True,
                            "status": data.get("status"),
                            "message": data.get("message")
                        }
                    else:
                        error = await resp.text()
                        logger.warning(f"Self-improvement failed: {error}")
                        return {"success": False, "error": error}
                        
        except Exception as e:
            logger.error(f"Self-improvement request failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def research_for_issue(self, issue: CodeIssue) -> str:
        """
        Search the web for context on a complex code issue.
        
        Only used for HIGH/CRITICAL issues to avoid slowing down
        the refactoring pipeline. Returns a context string to 
        inject into the Brain prompt.
        """
        if issue.severity not in ("HIGH", "CRITICAL"):
            return ""
        
        try:
            from .brain_web import search_web
            query = f"Python {issue.issue_type} fix best practice {issue.description[:50]}"
            results = await search_web(query, max_results=3)
            
            if not results:
                return ""
            
            context = "\n[WEB RESEARCH]\n"
            for r in results[:3]:
                context += f"• {r.get('title', '')}: {r.get('snippet', '')[:100]}\n"
            
            logger.info(f"🌐 Web research found {len(results)} refs for {issue.function}")
            return context
            
        except Exception as e:
            logger.debug(f"Web research for issue skipped: {e}")
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get refactoring statistics."""
        return {
            "requests_made": self.requests_made,
            "successful": self.successful_refactors,
            "failed": self.failed_refactors,
            "success_rate": (
                self.successful_refactors / self.requests_made 
                if self.requests_made > 0 else 0
            )
        }


# Singleton
_refactor_instance = None

def get_brain_refactor() -> BrainAssistedRefactoring:
    """Get the global BrainAssistedRefactoring instance."""
    global _refactor_instance
    if _refactor_instance is None:
        _refactor_instance = BrainAssistedRefactoring()
    return _refactor_instance
