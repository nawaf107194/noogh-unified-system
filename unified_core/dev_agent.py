"""
DevAgent - Autonomous Code Generation
Generates code from task specifications with iterative refinement
"""
import logging
import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

logger = logging.getLogger("unified_core.security.dev_agent")


class CodeLanguage(Enum):
    PYTHON = "python"
    RUST = "rust"
    CPP = "cpp"
    JAVASCRIPT = "javascript"
    GO = "go"
    SQL = "sql"


@dataclass
class CodeArtifact:
    """Generated code artifact."""
    language: CodeLanguage
    code: str
    filename: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    tests: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRequest:
    """Code generation request specification."""
    task_description: str
    language: CodeLanguage
    constraints: List[str] = field(default_factory=list)
    required_imports: List[str] = field(default_factory=list)
    context_code: Optional[str] = None
    max_lines: int = 500
    include_tests: bool = True
    include_docstrings: bool = True


@dataclass
class GenerationResult:
    """Result of code generation."""
    success: bool
    artifact: Optional[CodeArtifact] = None
    iterations: int = 0
    security_approved: bool = False
    security_issues: List[str] = field(default_factory=list)
    error: Optional[str] = None


class DevAgent:
    """
    Autonomous code generator that produces secure, tested code.
    Integrates with SecOpsAgent for security validation.
    """
    
    TEMPLATES = {
        CodeLanguage.PYTHON: '''"""
{docstring}
"""
{imports}

{code}

{tests}
''',
        CodeLanguage.RUST: '''//! {docstring}

{imports}

{code}

#[cfg(test)]
mod tests {{
    use super::*;
    
{tests}
}}
''',
    }
    
    def __init__(
        self,
        llm_generator: Optional[Callable] = None,
        secops_agent: Optional["SecOpsAgent"] = None,
        max_iterations: int = 3
    ):
        self.llm_generator = llm_generator or self._default_generator
        self.secops_agent = secops_agent
        self.max_iterations = max_iterations
        
        self._generation_history: List[GenerationResult] = []
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate code based on request specification.
        Iterates with SecOpsAgent until approved or max iterations.
        """
        iteration = 0
        current_code = None
        all_issues = []
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Generation iteration {iteration}/{self.max_iterations}")
            
            # Generate code
            try:
                artifact = await self._generate_code(request, current_code, all_issues)
                current_code = artifact.code
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                return GenerationResult(
                    success=False,
                    iterations=iteration,
                    error=str(e)
                )
            
            # Security validation
            if self.secops_agent:
                audit_result = await self.secops_agent.audit(artifact)
                
                if audit_result.approved:
                    logger.info("Code approved by SecOps")
                    result = GenerationResult(
                        success=True,
                        artifact=artifact,
                        iterations=iteration,
                        security_approved=True
                    )
                    self._generation_history.append(result)
                    return result
                else:
                    logger.warning(f"Security issues found: {audit_result.issues}")
                    all_issues.extend(audit_result.issues)
            else:
                # No SecOps, return as-is
                result = GenerationResult(
                    success=True,
                    artifact=artifact,
                    iterations=iteration,
                    security_approved=False
                )
                self._generation_history.append(result)
                return result
        
        # Max iterations reached
        result = GenerationResult(
            success=False,
            artifact=artifact if current_code else None,
            iterations=iteration,
            security_approved=False,
            security_issues=all_issues,
            error="Max iterations reached without security approval"
        )
        self._generation_history.append(result)
        return result
    
    async def _generate_code(
        self,
        request: GenerationRequest,
        previous_code: Optional[str],
        security_issues: List[str]
    ) -> CodeArtifact:
        """Generate or refine code based on request."""
        prompt = self._build_prompt(request, previous_code, security_issues)
        
        # Call LLM generator
        generated = await self.llm_generator(prompt)
        
        # Parse response
        code = self._extract_code(generated, request.language)
        tests = self._extract_tests(generated, request.language) if request.include_tests else None
        imports = self._extract_imports(code, request.language)
        
        # Build artifact
        return CodeArtifact(
            language=request.language,
            code=code,
            filename=self._generate_filename(request),
            description=request.task_description,
            dependencies=imports + request.required_imports,
            tests=tests
        )
    
    def _build_prompt(
        self,
        request: GenerationRequest,
        previous_code: Optional[str],
        issues: List[str]
    ) -> str:
        """Build prompt for code generation — XML-structured with engineering mindset."""
        # --- Core Task ---
        task_block = f"""<task>
Generate {request.language.value} code for: {request.task_description}
Max lines: {request.max_lines}
</task>"""

        # --- Engineering Mindset (from GPT-5 reference) ---
        engineering_block = """<engineering_mindset>
1. Define inputs and outputs clearly before writing code
2. Handle edge cases and error conditions FIRST (guard clauses)
3. Think about what could go wrong before implementing the happy path
4. Code must be immediately runnable — include all necessary imports
</engineering_mindset>"""

        # --- Anti-Fabrication Rules (from Claude Code + GPT-5) ---
        rules_block = """<rules>
1. Do NOT invent APIs, libraries, or functions that don't exist
2. Do NOT guess import paths — use only confirmed packages
3. Use ONLY standard library or explicitly requested dependencies
4. If unsure about an API, write a clear TODO comment instead of guessing
5. NEVER generate placeholder code or stubs — write real implementations
6. Defensive security only — no offensive or exploit code
</rules>"""

        # --- Code Style (from GPT-5 Agent CLI) ---
        style_block = """<code_style>
- Use descriptive variable names (not single letters): numItems, userData, responseTime
- Functions are verbs: calculateTotal, validateInput, fetchUserData
- Guard clauses and early returns — avoid deep nesting beyond 2 levels
- Comments explain WHY, not WHAT — omit trivial comments
- Match existing code style when context_code is provided
</code_style>"""

        # --- Quality Gate ---
        quality_block = """<quality_gate>
Before finalizing, mentally verify:
1. All imports are real and available
2. All edge cases are handled
3. No hardcoded secrets or credentials
4. Code follows the constraints specified
</quality_gate>"""

        # --- Dynamic Context ---
        context_parts = []
        if request.constraints:
            context_parts.append(f"<constraints>{', '.join(request.constraints)}</constraints>")
        if request.required_imports:
            context_parts.append(f"<required_imports>{', '.join(request.required_imports)}</required_imports>")
        if request.context_code:
            context_parts.append(f"<existing_code>\n{request.context_code}\n</existing_code>")
        if previous_code and issues:
            issues_str = "\n".join(f"- {issue}" for issue in issues[-5:])
            context_parts.append(f"<security_issues>\n{issues_str}\n</security_issues>")
            context_parts.append(f"<code_to_fix>\n{previous_code}\n</code_to_fix>")

        context_block = "\n".join(context_parts)

        # --- Output Requirements ---
        output_parts = []
        if request.include_docstrings:
            output_parts.append("Include docstrings.")
        if request.include_tests:
            output_parts.append("Include unit tests.")
        output_block = f"<output_requirements>{' '.join(output_parts)}</output_requirements>" if output_parts else ""

        return f"""{task_block}

{engineering_block}

{rules_block}

{style_block}

{context_block}

{output_block}

{quality_block}"""
    
    def _extract_code(self, response: str, language: CodeLanguage) -> str:
        """Extract code block from response."""
        lang_markers = {
            CodeLanguage.PYTHON: ("python", "py"),
            CodeLanguage.RUST: ("rust", "rs"),
            CodeLanguage.CPP: ("cpp", "c++"),
            CodeLanguage.JAVASCRIPT: ("javascript", "js"),
            CodeLanguage.GO: ("go", "golang"),
            CodeLanguage.SQL: ("sql",),
        }
        
        markers = lang_markers.get(language, (language.value,))
        
        for marker in markers:
            pattern = rf'```{marker}\n(.*?)```'
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: try generic code block
        match = re.search(r'```\n(.*?)```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        return response.strip()
    
    def _extract_tests(self, response: str, language: CodeLanguage) -> Optional[str]:
        """Extract test code from response."""
        test_patterns = {
            CodeLanguage.PYTHON: r'(def test_.*?(?=\ndef |\Z))',
            CodeLanguage.RUST: r'(#\[test\].*?fn .*?\{.*?\})',
        }
        
        pattern = test_patterns.get(language)
        if pattern:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                return "\n\n".join(matches)
        return None
    
    def _extract_imports(self, code: str, language: CodeLanguage) -> List[str]:
        """Extract import statements."""
        patterns = {
            CodeLanguage.PYTHON: r'^(?:import|from)\s+(\S+)',
            CodeLanguage.RUST: r'^use\s+(\S+)',
            CodeLanguage.CPP: r'#include\s*[<"]([^>"]+)',
            CodeLanguage.JAVASCRIPT: r"(?:import|require)\s*\(?['\"]([^'\"]+)",
            CodeLanguage.GO: r'import\s+"([^"]+)"',
        }
        
        pattern = patterns.get(language)
        if pattern:
            return re.findall(pattern, code, re.MULTILINE)
        return []
    
    def _generate_filename(self, request: GenerationRequest) -> str:
        """Generate filename from task description."""
        extensions = {
            CodeLanguage.PYTHON: ".py",
            CodeLanguage.RUST: ".rs",
            CodeLanguage.CPP: ".cpp",
            CodeLanguage.JAVASCRIPT: ".js",
            CodeLanguage.GO: ".go",
            CodeLanguage.SQL: ".sql",
        }
        
        # Clean task description for filename
        name = request.task_description.lower()[:40]
        name = re.sub(r'[^a-z0-9]+', '_', name)
        name = name.strip('_')
        
        return f"{name}{extensions.get(request.language, '.txt')}"
    
    async def _default_generator(self, prompt: str) -> str:
        """Default generator - returns template code."""
        # This would normally call an LLM
        return f'''```python
def generated_function():
    """Auto-generated from: {prompt[:50]}..."""
    pass

def test_generated_function():
    assert generated_function() is None
```'''
    
    def get_history(self) -> List[GenerationResult]:
        """Get generation history."""
        return self._generation_history.copy()
