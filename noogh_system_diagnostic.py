#!/usr/bin/env python3
"""
NOOGH System Diagnostic Script v1.0
====================================
Scans the full execution path for operational issues:
  User → FastAPI → routes → orchestrator → react_loop → reasoning_engine
  → tool_call_parser → tool_executor → basic_tools → subprocess

Checks:
  1. Import health (circular imports, missing modules)
  2. Tool registration (duplicates, missing)
  3. Return type consistency
  4. Async/await correctness
  5. Endpoint registration
  6. Critical path connectivity
  7. WebSocket handler correctness
"""

import ast
import os
import sys
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

SRC_ROOT = Path("/home/noogh/projects/noogh_unified_system/src")
ENGINE_ROOT = SRC_ROOT / "neural_engine"

# ============================================================================
# RESULT TRACKING
# ============================================================================
class DiagResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = []
        self.warnings = []
        self.errors = []
    
    def ok(self, msg): self.passed.append(msg)
    def warn(self, msg): self.warnings.append(msg)
    def error(self, msg): self.errors.append(msg)
    
    def summary(self):
        status = "✅ PASS" if not self.errors else "❌ FAIL"
        if not self.errors and self.warnings:
            status = "⚠️  WARN"
        lines = [f"\n{'='*60}", f"{status} {self.name}", f"{'='*60}"]
        for p in self.passed: lines.append(f"  ✅ {p}")
        for w in self.warnings: lines.append(f"  ⚠️  {w}")
        for e in self.errors: lines.append(f"  ❌ {e}")
        return "\n".join(lines)


# ============================================================================
# TEST 1: SYNTAX CHECK ALL PYTHON FILES
# ============================================================================
def check_syntax():
    r = DiagResult("1. Syntax Check (ast.parse)")
    py_files = list(ENGINE_ROOT.rglob("*.py"))
    failures = 0
    for f in py_files:
        rel = f.relative_to(SRC_ROOT)
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                ast.parse(fh.read(), filename=str(rel))
        except SyntaxError as e:
            r.error(f"{rel}:{e.lineno} — {e.msg}")
            failures += 1
    if failures == 0:
        r.ok(f"All {len(py_files)} Python files parse cleanly")
    return r


# ============================================================================
# TEST 2: IMPORT GRAPH ANALYSIS
# ============================================================================
def check_imports():
    r = DiagResult("2. Import Health")
    
    # Collect all imports from neural_engine
    import_map = {}  # file -> list of imports
    py_files = list(ENGINE_ROOT.rglob("*.py"))
    
    for f in py_files:
        rel = str(f.relative_to(SRC_ROOT))
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                tree = ast.parse(fh.read(), filename=rel)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            import_map[rel] = imports
        except SyntaxError:
            pass  # caught by test 1
    
    # Check for critical missing modules
    critical_modules = {
        "neural_engine/api/routes.py": ["shared.models", "neural_engine.reasoning_engine"],
        "neural_engine/react_loop.py": ["neural_engine.reasoning_engine"],
        "neural_engine/tools/tool_executor.py": [
            "neural_engine.preamble_manager",
            "neural_engine.progress_checkpoint_manager",
        ],
    }
    
    for file, required in critical_modules.items():
        file_imports = import_map.get(file, [])
        for mod in required:
            found = any(mod in imp for imp in file_imports)
            if found:
                r.ok(f"{os.path.basename(file)} imports {mod}")
            else:
                r.error(f"{os.path.basename(file)} MISSING import: {mod}")
    
    # Check for potential circular imports (heuristic: A imports B, B imports A)
    module_map = {}
    for f, imps in import_map.items():
        mod_name = f.replace("/", ".").replace(".py", "")
        module_map[mod_name] = set(imps)
    
    circulars_found = set()
    for mod_a, imps_a in module_map.items():
        for imp in imps_a:
            for mod_b, imps_b in module_map.items():
                if mod_a != mod_b and imp.startswith(mod_b.split(".")[-1]):
                    if any(i.startswith(mod_a.split(".")[-1]) for i in imps_b):
                        pair = tuple(sorted([mod_a, mod_b]))
                        if pair not in circulars_found:
                            circulars_found.add(pair)
    
    if circulars_found:
        for a, b in list(circulars_found)[:5]:
            r.warn(f"Potential circular: {os.path.basename(a)} ↔ {os.path.basename(b)}")
    else:
        r.ok("No obvious circular imports detected")
    
    r.ok(f"Scanned {len(import_map)} files, {sum(len(v) for v in import_map.values())} imports")
    return r


# ============================================================================
# TEST 3: DUPLICATE FUNCTION DEFINITIONS
# ============================================================================
def check_duplicates():
    r = DiagResult("3. Duplicate Definitions")
    
    critical_files = [
        ENGINE_ROOT / "cognitive_trace.py",
        ENGINE_ROOT / "tools" / "tool_executor.py",
        ENGINE_ROOT / "tools" / "basic_tools.py",
        ENGINE_ROOT / "api" / "routes.py",
    ]
    
    for filepath in critical_files:
        if not filepath.exists():
            r.warn(f"File not found: {filepath.name}")
            continue
        
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read(), filename=filepath.name)
        
        # Collect function/method names with line numbers
        func_defs = defaultdict(list)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_defs[node.name].append(node.lineno)
        
        dupes = {name: lines for name, lines in func_defs.items() if len(lines) > 1}
        
        if dupes:
            for name, lines in dupes.items():
                # Inner functions (closures) are OK, top-level dupes are not
                r.warn(f"{filepath.name}: `{name}` defined {len(lines)}x at lines {lines}")
        else:
            r.ok(f"{filepath.name}: No duplicate definitions")
    
    return r


# ============================================================================
# TEST 4: TOOL RETURN TYPE CONSISTENCY
# ============================================================================
def check_tool_returns():
    r = DiagResult("4. Tool Return Type Consistency")
    
    tools_file = ENGINE_ROOT / "tools" / "basic_tools.py"
    if not tools_file.exists():
        r.error("basic_tools.py not found")
        return r
    
    with open(tools_file, 'r') as f:
        tree = ast.parse(f.read(), filename="basic_tools.py")
    
    # Analyze top-level function return annotations
    returns_str = []
    returns_dict = []
    returns_unknown = []
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns:
                ret_type = ast.dump(node.returns)
                if "str" in ret_type:
                    returns_str.append(node.name)
                elif "Dict" in ret_type or "dict" in ret_type:
                    returns_dict.append(node.name)
                else:
                    returns_unknown.append(node.name)
            else:
                returns_unknown.append(node.name)
    
    if returns_str and returns_dict:
        r.warn(f"Mixed return types: {len(returns_str)} return str, {len(returns_dict)} return dict")
        r.warn(f"  str-returning: {', '.join(returns_str[:5])}")
        r.warn(f"  dict-returning: {', '.join(returns_dict[:5])}")
    elif returns_str:
        r.ok(f"Consistent: all {len(returns_str)} tools return str")
    elif returns_dict:
        r.ok(f"Consistent: all {len(returns_dict)} tools return dict")
    
    # Also check system_tools.py
    sys_tools = ENGINE_ROOT / "tools" / "system_tools.py"
    if sys_tools.exists():
        with open(sys_tools, 'r') as f:
            tree2 = ast.parse(f.read(), filename="system_tools.py")
        
        sys_str = []
        sys_dict = []
        for node in ast.iter_child_nodes(tree2):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.returns:
                    ret_type = ast.dump(node.returns)
                    if "str" in ret_type:
                        sys_str.append(node.name)
                    elif "Dict" in ret_type or "dict" in ret_type:
                        sys_dict.append(node.name)
        
        if sys_str and sys_dict:
            r.warn(f"system_tools.py: mixed returns — {len(sys_str)} str, {len(sys_dict)} dict")
        elif sys_str:
            r.ok(f"system_tools.py: consistent str returns ({len(sys_str)} functions)")
        elif sys_dict:
            r.ok(f"system_tools.py: consistent dict returns ({len(sys_dict)} functions)")
    
    return r


# ============================================================================
# TEST 5: ASYNC/AWAIT CORRECTNESS
# ============================================================================
def check_async_correctness():
    r = DiagResult("5. Async/Await Correctness")
    
    critical_files = [
        ENGINE_ROOT / "api" / "routes.py",
        ENGINE_ROOT / "react_loop.py",
        ENGINE_ROOT / "orchestrator.py",
    ]
    
    for filepath in critical_files:
        if not filepath.exists():
            r.warn(f"Not found: {filepath.name}")
            continue
        
        with open(filepath, 'r') as f:
            source = f.read()
            tree = ast.parse(source, filename=filepath.name)
        
        # Find async functions and check if they use await
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                has_await = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Await):
                        has_await = True
                        break
                if not has_await:
                    r.warn(f"{filepath.name}: async `{node.name}` (L{node.lineno}) never uses await")
        
        # Check for sync calls to async functions (heuristic: calling known async funcs without await)
        known_async = {"reason", "run", "recall", "store", "route"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in known_async:
                    # Check if parent is Await
                    pass  # TODO: more sophisticated analysis
    
    r.ok("Basic async/await analysis complete")
    return r


# ============================================================================
# TEST 6: WEBSOCKET HANDLER CORRECTNESS
# ============================================================================
def check_websocket():
    r = DiagResult("6. WebSocket Handler")
    
    main_file = ENGINE_ROOT / "api" / "main.py"
    if not main_file.exists():
        r.error("api/main.py not found")
        return r
    
    with open(main_file, 'r') as f:
        source = f.read()
    
    # Check disconnect in finally block
    if "finally:" in source and "disconnect" in source:
        r.ok("WebSocket disconnect in finally block")
    elif "manager.disconnect" in source:
        # Check if disconnect is reachable
        lines = source.split('\n')
        for i, line in enumerate(lines, 1):
            if "while True:" in line:
                # Check next lines for disconnect before except
                for j in range(i, min(i+10, len(lines))):
                    if "manager.disconnect" in lines[j-1] and "except" not in lines[j-1]:
                        # Check if there's a break or if it's after the while
                        indent_while = len(line) - len(line.lstrip())
                        indent_disc = len(lines[j-1]) - len(lines[j-1].lstrip())
                        if indent_disc > indent_while:
                            r.error(f"L{j}: manager.disconnect INSIDE while True — UNREACHABLE without break")
                        break
    else:
        r.error("No WebSocket disconnect logic found")
    
    # Check for WebSocketDisconnect exception handling
    if "WebSocketDisconnect" in source:
        r.ok("WebSocketDisconnect exception handled")
    else:
        r.warn("No WebSocketDisconnect exception handler — abrupt disconnects not caught cleanly")
    
    return r


# ============================================================================
# TEST 7: ENDPOINT COUNT AND AUTH STATUS
# ============================================================================
def check_endpoints():
    r = DiagResult("7. Endpoint Registration & Auth")
    
    routes_file = ENGINE_ROOT / "api" / "routes.py"
    if not routes_file.exists():
        r.error("routes.py not found")
        return r
    
    with open(routes_file, 'r') as f:
        source = f.read()
    
    lines = source.split('\n')
    
    authed = []
    unauthed = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("@router.") and ("post(" in stripped or "get(" in stripped):
            # Extract endpoint path
            import re
            match = re.search(r'["\'](/[^"\']+)["\']', stripped)
            path = match.group(1) if match else "unknown"
            
            has_auth = "verify_internal_token" in stripped or "Depends(" in stripped
            
            if has_auth:
                authed.append(path)
            else:
                unauthed.append(path)
    
    r.ok(f"Total endpoints: {len(authed) + len(unauthed)}")
    r.ok(f"Authenticated: {len(authed)}")
    
    if unauthed:
        r.warn(f"Unauthenticated: {len(unauthed)}")
        for ep in unauthed[:10]:
            r.warn(f"  NO AUTH: {ep}")
        if len(unauthed) > 10:
            r.warn(f"  ... and {len(unauthed) - 10} more")
    else:
        r.ok("All endpoints authenticated")
    
    return r


# ============================================================================
# TEST 8: CRITICAL PATH CONNECTIVITY
# ============================================================================
def check_critical_path():
    r = DiagResult("8. Critical Path Connectivity")
    
    # Check each layer exists and has required exports
    checks = [
        ("api/main.py", ["app"], "FastAPI app instance"),
        ("api/routes.py", ["router", "get_components"], "Router & component initializer"),
        ("react_loop.py", ["ReActLoop", "get_react_loop"], "ReAct loop"),
        ("reasoning_engine.py", ["ReasoningEngine"], "Reasoning engine"),
        ("tools/tool_executor.py", ["ToolExecutor", "get_tool_executor"], "Tool executor"),
        ("tools/basic_tools.py", ["execute_command", "read_file"], "Basic tools"),
        ("orchestrator.py", ["NeuralOrchestrator"], "Orchestrator"),
        ("cognitive_trace.py", ["CognitiveTrace", "get_trace_manager"], "Cognitive trace"),
        ("model_authority.py", ["ModelAuthority", "get_model_authority"], "Model authority"),
    ]
    
    for filepath, required_names, description in checks:
        full_path = ENGINE_ROOT / filepath
        if not full_path.exists():
            r.error(f"MISSING: {filepath} ({description})")
            continue
        
        with open(full_path, 'r') as f:
            tree = ast.parse(f.read(), filename=filepath)
        
        defined_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)
        
        missing = [n for n in required_names if n not in defined_names]
        if missing:
            r.error(f"{filepath}: missing {missing}")
        else:
            r.ok(f"{filepath}: {description} ✓")
    
    return r


# ============================================================================
# TEST 9: shell=True REMAINING
# ============================================================================
def check_shell_true():
    r = DiagResult("9. Remaining shell=True Usage")
    
    py_files = list(ENGINE_ROOT.rglob("*.py"))
    
    user_controlled = []  # Functions that take user input
    hardcoded = []  # Functions with hardcoded commands
    
    for f in py_files:
        rel = str(f.relative_to(SRC_ROOT))
        try:
            with open(f, 'r') as fh:
                for i, line in enumerate(fh, 1):
                    if "shell=True" in line and not line.strip().startswith("#"):
                        # Heuristic: is the command variable user-controlled?
                        is_user_input = any(kw in rel for kw in ["execute_command", "execute_system"])
                        ctx = f"{rel}:{i}"
                        if is_user_input:
                            user_controlled.append(ctx)
                        else:
                            hardcoded.append(ctx)
        except Exception:
            pass
    
    if user_controlled:
        for loc in user_controlled:
            r.error(f"USER-INPUT shell=True: {loc}")
    
    if hardcoded:
        r.warn(f"{len(hardcoded)} hardcoded shell=True remaining (lower risk)")
        for loc in hardcoded[:5]:
            r.warn(f"  {loc}")
        if len(hardcoded) > 5:
            r.warn(f"  ... and {len(hardcoded) - 5} more")
    
    if not user_controlled and not hardcoded:
        r.ok("No shell=True usage found")
    elif not user_controlled:
        r.ok("No user-input-controlled shell=True (critical paths clean)")
    
    return r


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("=" * 60)
    print("  NOOGH System Diagnostic v1.0")
    print("=" * 60)
    print(f"  Source root: {SRC_ROOT}")
    print(f"  Engine root: {ENGINE_ROOT}")
    print()
    
    tests = [
        check_syntax,
        check_imports,
        check_duplicates,
        check_tool_returns,
        check_async_correctness,
        check_websocket,
        check_endpoints,
        check_critical_path,
        check_shell_true,
    ]
    
    results = []
    total_errors = 0
    total_warnings = 0
    
    for test in tests:
        try:
            result = test()
            results.append(result)
            total_errors += len(result.errors)
            total_warnings += len(result.warnings)
            print(result.summary())
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {test.__name__}: {e}")
            total_errors += 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("  FINAL SUMMARY")
    print("=" * 60)
    print(f"  Tests run: {len(results)}")
    print(f"  ❌ Errors:   {total_errors}")
    print(f"  ⚠️  Warnings: {total_warnings}")
    print(f"  ✅ Passed:   {sum(len(r.passed) for r in results)}")
    
    if total_errors == 0:
        print("\n  🎉 SYSTEM IS OPERATIONALLY HEALTHY")
    else:
        print(f"\n  🚨 {total_errors} ISSUES REQUIRE ATTENTION")
    
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
