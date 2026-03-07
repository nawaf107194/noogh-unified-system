# unified_core/evolution/code_analyzer.py
import ast
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from pathlib import Path

logger = logging.getLogger("unified_core.evolution.analyzer")

@dataclass
class CodeIssue:
    """وصف لمشكلة برمجية مكتشفة"""
    file: str
    line: int
    issue_type: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    function: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FileFunction:
    name: str
    start_line: int
    end_line: int

class FileAnalysis:
    def __init__(self, file_path, lines=0, complexity=0, functions=None, vulnerabilities=None):
        self.file = file_path
        self.lines = lines
        self.complexity = complexity
        self.functions = functions or []
        self.vulnerabilities = vulnerabilities or []
        self.score = 100
        self._source = None  # v9: cached source for per-function analysis

class ArchitectureMap:
    """خريطة العلاقات الهيكلية في النظام"""
    def __init__(self):
        self.nodes = {}
        self.links = []
        self.layers = {
            "CORE": {"component": "Unified Core", "focus": "Reasoning & World Mode"},
            "EVOLUTION": {"component": "Self-Directed Layer", "focus": "Self-Improvement"},
            "WORLD": {"component": "Environment", "focus": "Data & State"},
            "ACTUATORS": {"component": "Executors", "focus": "Action execution"},
            "TOOLS": {"component": "Utilities", "focus": "Maintenance Scripts"}
        }
        
    def map_project(self):
        """Map project components."""
        src_path = Path(__file__).parent.parent  # unified_core/
        for p in src_path.rglob("*.py"):
            self.nodes[str(p)] = {"type": "component", "size": p.stat().st_size}
        return {"nodes": self.nodes, "links": self.links}

    def get_layer_for_path(self, path: str) -> str:
        """تحديد الطبقة المعمارية للمسار"""
        if "core" in path: return "CORE"
        if "evolution" in path: return "EVOLUTION"
        if "scripts" in path: return "TOOLS"
        return "GENERAL"

_arch_instance = None
def get_architecture_map() -> ArchitectureMap:
    global _arch_instance
    if _arch_instance is None:
        _arch_instance = ArchitectureMap()
    return _arch_instance

class ComplexityCalculator(ast.NodeVisitor):
    """حاسبة التعقيد الهيكلي"""
    def __init__(self):
        self.complexity = 0
        
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

class SecurityScanner:
    """فاحص الثغرات البرمجية"""
    def find_vulnerabilities(self, source: str) -> List[Dict]:
        vulnerabilities = []
        if "eval(" in source:
            vulnerabilities.append({"type": "INSECURE_EVAL", "severity": "CRITICAL"})
        if "os.system(" in source:
            vulnerabilities.append({"type": "SHELL_INJECTION", "severity": "HIGH"})
        return vulnerabilities

class CodeAnalyzer:
    """محلل الكود المعياري - v3.0"""
    
    def __init__(self):
        self.scanner = SecurityScanner()
        self._cache = {}  # Required by BrainAssistedRefactoring
        
    def analyze_file(self, file_path: str) -> FileAnalysis:
        """تحليل ملف برمجيا"""
        try:
            with open(file_path, "r") as f:
                source = f.read()
                
            tree = ast.parse(source)
            
            # حساب التعقيد
            calc = ComplexityCalculator()
            calc.visit(tree)
            
            # استخراج الدوال
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(FileFunction(
                        name=node.name,
                        start_line=node.lineno,
                        end_line=node.end_lineno if hasattr(node, "end_lineno") else node.lineno + 20
                    ))
            
            # فحص أمني
            vulns = self.scanner.find_vulnerabilities(source)
            
            analysis = FileAnalysis(
                file_path=file_path,
                lines=len(source.splitlines()),
                complexity=calc.complexity,
                functions=functions,
                vulnerabilities=vulns
            )
            analysis.score = max(0, 100 - (calc.complexity * 2) - (len(vulns) * 20))
            
            # تحديث الكاش
            self._cache[file_path] = analysis
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed for {file_path}: {e}")
            return FileAnalysis(file_path)

    def analyze_project(self) -> Any:
        """تحليل المشروع بالكامل — يشمل كل المجلدات"""
        from dataclasses import dataclass
        @dataclass
        class ProjectReport:
            files_analyzed: int
            total_issues: int
            avg_score: float
            hotspots: List[str]
            issues: List[CodeIssue]

        issues = []
        files = 0
        total_score = 0
        
        # Scan entire src/ directory (not just unified_core/)
        src_path = Path(__file__).parent.parent.parent  # src/
        
        # Skip directories that don't contain meaningful code
        skip_dirs = {'__pycache__', '.git', 'node_modules', 'venv', '.venv', 
                     'dist', 'build', 'egg-info', 'migrations'}
        
        for p in src_path.rglob("*.py"):
            # Skip unwanted directories
            if any(skip in str(p) for skip in skip_dirs):
                continue
            # Skip test/verify/backup files
            path_str = str(p)
            if any(skip in path_str.lower() for skip in ['test', 'verify', 'audit', '_backup', '.orig', '.rej']):
                continue
            
            # v9: mtime-based cache — skip files that haven't changed
            try:
                file_mtime = p.stat().st_mtime
            except OSError:
                continue
            
            if path_str in self._cache:
                cached = self._cache[path_str]
                if getattr(cached, '_mtime', None) == file_mtime:
                    res = cached  # Use cached result
                else:
                    res = self.analyze_file(path_str)
                    res._mtime = file_mtime
            else:
                res = self.analyze_file(path_str)
                res._mtime = file_mtime
            
            if res.lines > 0:
                files += 1
                total_score += res.score
                
                # High complexity functions
                if res.complexity >= 15:
                    issues.append(CodeIssue(
                        file=path_str, line=1, issue_type="high_complexity",
                        description=f"High cyclomatic complexity ({res.complexity})",
                        severity="HIGH", metrics={"complexity": res.complexity},
                        function=res.functions[0].name if res.functions else "module"
                    ))
                elif res.complexity >= 10:
                    issues.append(CodeIssue(
                        file=path_str, line=1, issue_type="high_complexity",
                        description=f"Moderate complexity ({res.complexity})",
                        severity="MEDIUM", metrics={"complexity": res.complexity},
                        function=res.functions[0].name if res.functions else "module"
                    ))
                
                # Security vulnerabilities
                for v in res.vulnerabilities:
                    issues.append(CodeIssue(
                        file=path_str, line=1, issue_type=v["type"],
                        description=f"Security issue: {v['type']}",
                        severity=v["severity"]
                    ))
                
                # v9: Smart cognitive_logic — only flag functions with real complexity
                # Read source once for per-function analysis
                try:
                    if res._source is None:
                        with open(path_str, 'r') as f:
                            res._source = f.read()
                    source_lines = res._source.splitlines()
                except Exception:
                    source_lines = None
                
                for func in res.functions:
                    func_lines = func.end_line - func.start_line
                    # v9: Skip small functions (< 30 lines instead of 5)
                    if func_lines < 30:
                        # Still allow if function has high per-function complexity
                        if source_lines and func.start_line <= len(source_lines):
                            try:
                                func_source = '\n'.join(source_lines[func.start_line-1:func.end_line])
                                func_tree = ast.parse(func_source)
                                calc = ComplexityCalculator()
                                calc.visit(func_tree)
                                if calc.complexity < 5:
                                    continue  # Skip: short AND simple
                            except Exception:
                                continue  # Can't parse → skip
                        else:
                            continue
                    
                    if func.name.startswith('__') and func.name.endswith('__') and func.name != '__init__':
                        continue
                    
                    issues.append(CodeIssue(
                        file=path_str, 
                        line=func.start_line, 
                        issue_type="cognitive_logic",
                        description=f"Function '{func.name}' ({func_lines} lines) — review for robustness",
                        severity="MEDIUM",
                        function=func.name,
                        metrics={"lines": func_lines, "complexity": res.complexity}
                    ))
        
        return ProjectReport(
            files_analyzed=files, total_issues=len(issues),
            avg_score=total_score/files if files > 0 else 100,
            hotspots=[i.file for i in issues[:3]],
            issues=issues
        )

    def get_critical_issues(self, report: Any) -> List[CodeIssue]:
        """تصفية المشاكل — تشمل MEDIUM لتغطية كل الملفات"""
        return [i for i in report.issues if i.severity in ["MEDIUM", "HIGH", "CRITICAL"]]

# Singleton
_analyzer_instance = None

def get_code_analyzer() -> CodeAnalyzer:
    """الحصول على نسخة محلل الكود الوحيدة"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = CodeAnalyzer()
    return _analyzer_instance

if __name__ == "__main__":
    analyzer = get_code_analyzer()
    report = analyzer.analyze_file("unified_core/agent_daemon.py")
    print(report)
