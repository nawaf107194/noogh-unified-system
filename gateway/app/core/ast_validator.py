import ast
import logging

logger = logging.getLogger("validator.ast")

DANGEROUS_IMPORTS = {
    "os", "sys", "subprocess", "socket", "requests", "http", "urllib", "shutil", "pickle", "importlib"
}

DANGEROUS_CALLS = {
    "eval", "exec", "compile", "open", "system", "popen", "spawn", "fork", "remove", "unlink", "rmdir"
}

class CodeSecurityValidator(ast.NodeVisitor):
    def __init__(self):
        self.errors = []
        self.safe = True

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split('.')[0] in DANGEROUS_IMPORTS:
                self.errors.append(f"Forbidden import: {alias.name}")
                self.safe = False
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split('.')[0] in DANGEROUS_IMPORTS:
            self.errors.append(f"Forbidden import from: {node.module}")
            self.safe = False
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in DANGEROUS_CALLS:
                self.errors.append(f"Forbidden call: {node.func.id}()")
                self.safe = False
        elif isinstance(node.func, ast.Attribute):
            # Block subprocess.run, os.system etc if not already blocked by import
            if node.func.attr in DANGEROUS_CALLS:
                 self.errors.append(f"Forbidden attribute call: {node.func.attr}")
                 self.safe = False
        self.generic_visit(node)

def validate_code(code: str) -> tuple[bool, str]:
    """
    Statically analyze code for forbidden patterns using AST.
    Returns: (is_safe, error_message)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"

    validator = CodeSecurityValidator()
    validator.visit(tree)

    if not validator.safe:
        return False, f"Security Violation: {'; '.join(validator.errors)}"
    
    return True, "Safe"
