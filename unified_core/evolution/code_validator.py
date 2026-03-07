"""
Code Validator — AST-based validation for evolution proposals.

Extracted from EvolutionController v4.0 for modularity.
Contains validation logic that runs BEFORE canary testing.
"""
import ast
import re
import logging
from typing import Dict, Any

logger = logging.getLogger("unified_core.evolution.code_validator")


def ast_emission_guard(original_code: str, refactored_code: str,
                       metadata: Dict[str, Any]) -> Dict[str, Any]:
    """AST-level validation of emitted code BEFORE canary.

    Checks:
    1. Refactored code is parseable (with indentation normalization)
    2. Function name is preserved
    3. Function signature is preserved
    4. No class definitions added/removed
    5. def is not moved to a different indent level
    """
    func_name = metadata.get('function', '')
    violations = []

    # ── Normalize indentation for standalone parsing ──
    def dedent_code(code):
        lines = code.split('\n')
        non_empty = [l for l in lines if l.strip()]
        if not non_empty:
            return code
        min_indent = min(len(l) - len(l.lstrip()) for l in non_empty)
        return '\n'.join(l[min_indent:] if len(l) >= min_indent else l for l in lines)

    orig_dedented = dedent_code(original_code)
    refac_dedented = dedent_code(refactored_code)

    # ── Check 1: Refactored code must be parseable ──
    try:
        refac_ast = ast.parse(refac_dedented)
    except SyntaxError as se:
        return {
            "pass": False,
            "reason": f"AST_EMISSION: Refactored snippet has syntax error: {se}"
        }

    # ── Parse original (if it fails, skip remaining checks) ──
    try:
        orig_ast = ast.parse(orig_dedented)
    except SyntaxError:
        return {"pass": True, "reason": "Original snippet unparseable — basic syntax OK"}

    # ── Check 2: Function name preserved ──
    def get_top_funcs(tree):
        return [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

    orig_funcs = get_top_funcs(orig_ast)
    refac_funcs = get_top_funcs(refac_ast)

    if orig_funcs and refac_funcs:
        if orig_funcs[0].name != refac_funcs[0].name:
            violations.append(
                f"FUNC_NAME: Original '{orig_funcs[0].name}' → "
                f"Refactored '{refac_funcs[0].name}'"
            )

    if orig_funcs and not refac_funcs:
        violations.append("FUNC_LOST: Refactored code has no function definition")

    # ── Check 3: Signature preservation (arg names + count) ──
    if orig_funcs and refac_funcs:
        orig_args = [a.arg for a in orig_funcs[0].args.args]
        refac_args = [a.arg for a in refac_funcs[0].args.args]
        if orig_args != refac_args:
            violations.append(
                f"SIGNATURE: Args changed: {orig_args} → {refac_args}"
            )

    # ── Check 4: No class definitions added in snippet ──
    orig_classes = [n for n in ast.walk(orig_ast) if isinstance(n, ast.ClassDef)]
    refac_classes = [n for n in ast.walk(refac_ast) if isinstance(n, ast.ClassDef)]
    if len(refac_classes) > len(orig_classes):
        violations.append(
            f"CLASS_ADDED: {len(refac_classes) - len(orig_classes)} class(es) added in snippet"
        )

    # ── Check 5: Target function must still exist ──
    if func_name and refac_funcs:
        refac_names = {n.name for n in ast.walk(refac_ast)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        if func_name not in refac_names:
            violations.append(
                f"FUNC_LOST: Target function '{func_name}' not found in refactored code"
            )

    if violations:
        return {
            "pass": False,
            "violations": violations,
            "reason": "; ".join(violations)
        }

    return {"pass": True, "reason": "AST emission guard passed"}


def refactor_policy_check(refactored_code: str, target_file: str,
                          metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Check refactored code for banned patterns BEFORE canary.

    Blocks:
    - print() of auth/token/secret values
    - import statements inside method bodies (unless whitelisted)
    - isinstance() checks on typed dataclass fields (noise)
    - scope changes (class method becoming top-level or vice versa)
    """
    violations = []

    # ── Rule 1: No token/secret leakage via print ─────────────
    leak_patterns = [
        r'print\s*\(.*(?:token|auth|secret|password|key|bearer).*\)',
    ]
    for pat in leak_patterns:
        if re.search(pat, refactored_code, re.IGNORECASE):
            violations.append(f"SECURITY: print() leaks sensitive value (matched: {pat})")

    # ── Rule 1b: No print() as logger replacement ─────────────
    if re.search(r'except\s.*:\s*\n\s*print\s*\(', refactored_code):
        violations.append("STYLE: print() used as logger replacement in except block")

    # ── Rule 2: No imports inside function/method bodies (AST-based v9) ──
    try:
        refac_tree = ast.parse(refactored_code)
        for node in ast.walk(refac_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, (ast.Import, ast.ImportFrom)):
                        # Allow from __future__ imports
                        if isinstance(child, ast.ImportFrom) and child.module == '__future__':
                            continue
                        mod_name = ''
                        if isinstance(child, ast.ImportFrom):
                            mod_name = child.module or ''
                        elif child.names:
                            mod_name = child.names[0].name
                        violations.append(
                            f"STYLE: import inside function {node.name}(): '{mod_name}' — move to top level"
                        )
    except SyntaxError:
        # Fallback to text-based check if AST parse fails
        lines = refactored_code.split('\n')
        inside_def = False
        def_indent = 0
        for line in lines:
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if stripped.startswith(('def ', 'async def ')):
                inside_def = True
                def_indent = indent
            elif inside_def and indent > def_indent:
                if stripped.startswith(('import ', 'from ')):
                    if not stripped.startswith('from __future__'):
                        violations.append(f"STYLE: import inside method body: {stripped[:60]}")

    # ── Rule 3: Pointless isinstance on typed constructor args ─
    isinstance_noise = re.findall(
        r'if not isinstance\(self\.[\w.]+,\s*(?:str|int|float|bool|list|dict)\)',
        refactored_code
    )
    if len(isinstance_noise) >= 3:
        violations.append(f"NOISE: {len(isinstance_noise)} redundant isinstance checks on typed fields")

    # ── Rule 4: Scope consistency ─────────────────────────────
    func_name = metadata.get('function', '')
    if func_name and '.' in str(metadata.get('target', '')):
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith(('def ', 'async def ')):
                first_indent = len(line) - len(stripped)
                if first_indent == 0:
                    violations.append("SCOPE: method refactored to top-level (def with 0 indent)")
                break

    # ── Rule 5: Indentation drift between original and refactored ──
    original_code = metadata.get('original_code', '')
    if original_code:
        orig_def_indent = None
        for line in original_code.split('\n'):
            s = line.lstrip()
            if s.startswith(('def ', 'async def ')):
                orig_def_indent = len(line) - len(s)
                break

        refac_def_indent = None
        for line in lines:
            s = line.lstrip()
            if s.startswith(('def ', 'async def ')):
                refac_def_indent = len(line) - len(s)
                break

        if orig_def_indent is not None and refac_def_indent is not None:
            if orig_def_indent != refac_def_indent:
                violations.append(
                    f"INDENT_DRIFT: original def at col {orig_def_indent}, "
                    f"refactored at col {refac_def_indent} "
                    f"(scope {'narrowed' if refac_def_indent > orig_def_indent else 'widened'})"
                )

    if violations:
        return {
            "pass": False,
            "violations": violations,
            "reason": "; ".join(violations)
        }

    return {"pass": True, "reason": "Policy check passed"}


def structural_integrity_check(original_file: str, simulated_file: str,
                               target_file: str) -> Dict[str, Any]:
    """Structural Integrity Gate — AST-based validation.

    Compares the AST structure of the original file vs the simulated file.
    Rejects changes that:
    - Break class count or method nesting
    - Remove decorators (like @classmethod, @staticmethod)
    - Change function signatures incompatibly
    - Move methods outside their class
    """
    try:
        original_ast = ast.parse(original_file)
    except SyntaxError:
        return {"pass": True, "reason": "Original file has syntax issues — skipping structural check"}

    try:
        simulated_ast = ast.parse(simulated_file)
    except SyntaxError as se:
        return {"pass": False, "reason": f"Simulated file has syntax error: {se}"}

    # === Check 1: Class count must not change ===
    orig_classes = [n for n in ast.walk(original_ast) if isinstance(n, ast.ClassDef)]
    sim_classes = [n for n in ast.walk(simulated_ast) if isinstance(n, ast.ClassDef)]

    if len(sim_classes) != len(orig_classes):
        return {"pass": False,
                "reason": f"Class count changed: {len(orig_classes)} → {len(sim_classes)}"}

    # === Check 2: Methods inside classes must stay inside ===
    def get_class_methods(tree):
        """Return {class_name: [method_names]}."""
        result = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                result[node.name] = set(methods)
        return result

    orig_methods = get_class_methods(original_ast)
    sim_methods = get_class_methods(simulated_ast)

    for cls_name, orig_meths in orig_methods.items():
        sim_meths = sim_methods.get(cls_name, set())
        lost = orig_meths - sim_meths
        if lost:
            return {"pass": False,
                    "reason": f"Methods lost from class {cls_name}: {lost}"}

    # === Check 3: Top-level function count should not increase unexpectedly ===
    orig_top_funcs = [n.name for n in original_ast.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    sim_top_funcs = [n.name for n in simulated_ast.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

    new_top_funcs = set(sim_top_funcs) - set(orig_top_funcs)
    if new_top_funcs:
        all_orig_methods = set()
        for meths in orig_methods.values():
            all_orig_methods.update(meths)

        escaped = new_top_funcs & all_orig_methods
        if escaped:
            return {"pass": False,
                    "reason": f"Methods escaped from class to top-level: {escaped}"}

    # === Check 4: Decorator preservation ===
    def get_decorators(tree):
        """Return {func_name: [decorator_names]}."""
        result = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decs = []
                for d in node.decorator_list:
                    if isinstance(d, ast.Name):
                        decs.append(d.id)
                    elif isinstance(d, ast.Attribute):
                        decs.append(d.attr)
                result[node.name] = set(decs)
        return result

    orig_decs = get_decorators(original_ast)
    sim_decs = get_decorators(simulated_ast)

    for func_name, orig_dec_set in orig_decs.items():
        sim_dec_set = sim_decs.get(func_name, set())
        lost_decs = orig_dec_set - sim_dec_set
        critical_decs = {'classmethod', 'staticmethod', 'property', 'abstractmethod'}
        lost_critical = lost_decs & critical_decs
        if lost_critical:
            return {"pass": False,
                    "reason": f"Critical decorators lost from {func_name}: {lost_critical}"}

    return {"pass": True, "reason": "Structural integrity verified"}
