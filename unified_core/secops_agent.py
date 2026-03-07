"""
SecOpsAgent - Security Auditor with AST Analysis
Scans generated code for vulnerabilities, memory leaks, unauthorized calls
"""
import ast
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("unified_core.security.secops")


class SeverityLevel(Enum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class VulnerabilityCategory(Enum):
    INJECTION = "injection"
    FILE_ACCESS = "file_access"
    NETWORK = "network"
    PROCESS = "process"
    MEMORY = "memory"
    CRYPTO = "crypto"
    SERIALIZATION = "serialization"
    PRIVILEGE = "privilege"


@dataclass
class SecurityIssue:
    """Detected security issue."""
    category: VulnerabilityCategory
    severity: SeverityLevel
    message: str
    line_number: int
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str] = None


@dataclass
class AuditResult:
    """Result of security audit."""
    approved: bool
    issues: List[str]
    detailed_issues: List[SecurityIssue] = field(default_factory=list)
    risk_score: float = 0.0
    execution_time_ms: float = 0.0


class SecOpsAgent:
    """
    Security operations agent for code analysis.
    Uses AST parsing and pattern matching to detect vulnerabilities.
    """
    
    # Dangerous function patterns by category
    DANGEROUS_PATTERNS = {
        VulnerabilityCategory.INJECTION: {
            "python": [
                (r'\beval\s*\(', "eval() can execute arbitrary code", SeverityLevel.CRITICAL),
                (r'\bexec\s*\(', "exec() can execute arbitrary code", SeverityLevel.CRITICAL),
                (r'\bcompile\s*\(', "compile() can be used for code injection", SeverityLevel.HIGH),
                (r'__import__\s*\(', "Dynamic import can load malicious modules", SeverityLevel.HIGH),
                (r'subprocess\..*shell\s*=\s*True', "Shell=True enables command injection", SeverityLevel.CRITICAL),
                (r'os\.system\s*\(', "os.system() is vulnerable to injection", SeverityLevel.HIGH),
                (r'os\.popen\s*\(', "os.popen() is vulnerable to injection", SeverityLevel.HIGH),
            ],
            "rust": [
                (r'std::process::Command.*shell', "Shell commands may be injectable", SeverityLevel.HIGH),
            ],
        },
        VulnerabilityCategory.FILE_ACCESS: {
            "python": [
                (r'open\s*\([^)]*["\']\.\.', "Path traversal attempt detected", SeverityLevel.HIGH),
                (r'os\.chmod\s*\(', "Permission changes should be reviewed", SeverityLevel.MEDIUM),
                (r'shutil\.rmtree\s*\(', "Recursive delete is dangerous", SeverityLevel.HIGH),
                (r'/etc/passwd|/etc/shadow', "Sensitive system file access", SeverityLevel.CRITICAL),
            ],
        },
        VulnerabilityCategory.NETWORK: {
            "python": [
                (r'socket\.socket\s*\(', "Raw socket usage needs review", SeverityLevel.MEDIUM),
                (r'urllib.*urlopen.*http:', "Insecure HTTP connection", SeverityLevel.MEDIUM),
                (r'requests\.get.*verify\s*=\s*False', "SSL verification disabled", SeverityLevel.HIGH),
            ],
        },
        VulnerabilityCategory.SERIALIZATION: {
            "python": [
                (r'pickle\.load', "Pickle deserialization is unsafe", SeverityLevel.CRITICAL),
                (r'yaml\.load\s*\([^)]*\)', "yaml.load without Loader is unsafe", SeverityLevel.HIGH),
                (r'marshal\.load', "Marshal deserialization is unsafe", SeverityLevel.CRITICAL),
            ],
        },
        VulnerabilityCategory.CRYPTO: {
            "python": [
                (r'hashlib\.md5\s*\(', "MD5 is cryptographically weak", SeverityLevel.MEDIUM),
                (r'hashlib\.sha1\s*\(', "SHA1 is deprecated for security", SeverityLevel.MEDIUM),
                (r'random\.random\s*\(', "Use secrets module for crypto", SeverityLevel.LOW),
            ],
        },
    }
    
    # Blocked imports
    BLOCKED_IMPORTS = {
        "python": {
            "ctypes": SeverityLevel.HIGH,
            "cffi": SeverityLevel.HIGH,
            "multiprocessing": SeverityLevel.MEDIUM,
            "pty": SeverityLevel.CRITICAL,
            "fcntl": SeverityLevel.MEDIUM,
        }
    }
    
    # AST node types to analyze
    DANGEROUS_AST_NODES = {
        ast.Call: "_check_call",
        ast.Import: "_check_import",
        ast.ImportFrom: "_check_import_from",
        ast.Attribute: "_check_attribute",
    }
    
    def __init__(
        self,
        max_severity: SeverityLevel = SeverityLevel.MEDIUM,
        blocked_patterns: Optional[List[str]] = None,
        allowed_imports: Optional[Set[str]] = None
    ):
        self.max_severity = max_severity
        self.blocked_patterns = blocked_patterns or []
        self.allowed_imports = allowed_imports
        
        self._audit_count = 0
        self._rejection_count = 0
    
    async def audit(self, artifact: "CodeArtifact") -> AuditResult:
        """
        Perform comprehensive security audit on code artifact.
        """
        import time
        start = time.perf_counter()
        
        self._audit_count += 1
        issues: List[SecurityIssue] = []
        
        language = artifact.language.value
        code = artifact.code
        
        # Pattern-based scanning
        pattern_issues = self._scan_patterns(code, language)
        issues.extend(pattern_issues)
        
        # AST-based analysis (Python only currently)
        if language == "python":
            ast_issues = self._analyze_ast(code)
            issues.extend(ast_issues)
        
        # Check blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(SecurityIssue(
                    category=VulnerabilityCategory.PRIVILEGE,
                    severity=SeverityLevel.HIGH,
                    message=f"Blocked pattern detected: {pattern}",
                    line_number=0,
                    code_snippet="",
                    recommendation="Remove or refactor the blocked pattern"
                ))
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(issues)
        
        # Determine approval
        if issues:
            max_found_severity = max(issues, key=lambda i: i.severity.value).severity
        else:
            max_found_severity = SeverityLevel.INFO
        approved = max_found_severity.value <= self.max_severity.value
        
        if not approved:
            self._rejection_count += 1
        
        execution_time = (time.perf_counter() - start) * 1000
        
        return AuditResult(
            approved=approved,
            issues=[i.message for i in issues],
            detailed_issues=issues,
            risk_score=risk_score,
            execution_time_ms=execution_time
        )
    
    def _scan_patterns(self, code: str, language: str) -> List[SecurityIssue]:
        """Scan code for dangerous patterns using regex."""
        issues = []
        lines = code.split('\n')
        
        for category, lang_patterns in self.DANGEROUS_PATTERNS.items():
            patterns = lang_patterns.get(language, [])
            
            for pattern, message, severity in patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        issues.append(SecurityIssue(
                            category=category,
                            severity=severity,
                            message=message,
                            line_number=line_num,
                            code_snippet=line.strip()[:100],
                            recommendation=self._get_recommendation(category, pattern)
                        ))
        
        return issues
    
    def _analyze_ast(self, code: str) -> List[SecurityIssue]:
        """Perform AST-based security analysis on Python code."""
        issues = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(SecurityIssue(
                category=VulnerabilityCategory.INJECTION,
                severity=SeverityLevel.HIGH,
                message=f"Syntax error may indicate code injection: {e}",
                line_number=e.lineno or 0,
                code_snippet="",
                recommendation="Fix syntax error"
            ))
            return issues
        
        for node in ast.walk(tree):
            for node_type, check_method in self.DANGEROUS_AST_NODES.items():
                if isinstance(node, node_type):
                    method = getattr(self, check_method, None)
                    if method:
                        issue = method(node, code)
                        if issue:
                            issues.append(issue)
        
        return issues
    
    def _check_call(self, node: ast.Call, code: str) -> Optional[SecurityIssue]:
        """Check function calls for security issues."""
        func_name = ""
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        dangerous_funcs = {
            "eval": (VulnerabilityCategory.INJECTION, SeverityLevel.CRITICAL),
            "exec": (VulnerabilityCategory.INJECTION, SeverityLevel.CRITICAL),
            "compile": (VulnerabilityCategory.INJECTION, SeverityLevel.HIGH),
            "open": (VulnerabilityCategory.FILE_ACCESS, SeverityLevel.LOW),
            "getattr": (VulnerabilityCategory.INJECTION, SeverityLevel.MEDIUM),
            "setattr": (VulnerabilityCategory.INJECTION, SeverityLevel.MEDIUM),
        }
        
        if func_name in dangerous_funcs:
            category, severity = dangerous_funcs[func_name]
            return SecurityIssue(
                category=category,
                severity=severity,
                message=f"Dangerous function call: {func_name}()",
                line_number=node.lineno,
                code_snippet=ast.get_source_segment(code, node) or "",
                recommendation=f"Review usage of {func_name}() for security implications"
            )
        
        return None
    
    def _check_import(self, node: ast.Import, code: str) -> Optional[SecurityIssue]:
        """Check imports for blocked modules."""
        for alias in node.names:
            module = alias.name.split('.')[0]
            if module in self.BLOCKED_IMPORTS.get("python", {}):
                severity = self.BLOCKED_IMPORTS["python"][module]
                return SecurityIssue(
                    category=VulnerabilityCategory.PRIVILEGE,
                    severity=severity,
                    message=f"Blocked module imported: {alias.name}",
                    line_number=node.lineno,
                    code_snippet=f"import {alias.name}",
                    recommendation=f"Remove import of {alias.name}"
                )
        return None
    
    def _check_import_from(self, node: ast.ImportFrom, code: str) -> Optional[SecurityIssue]:
        """Check from-imports for blocked modules."""
        if node.module:
            module = node.module.split('.')[0]
            if module in self.BLOCKED_IMPORTS.get("python", {}):
                severity = self.BLOCKED_IMPORTS["python"][module]
                return SecurityIssue(
                    category=VulnerabilityCategory.PRIVILEGE,
                    severity=severity,
                    message=f"Blocked module imported: {node.module}",
                    line_number=node.lineno,
                    code_snippet=f"from {node.module} import ...",
                    recommendation=f"Remove import from {node.module}"
                )
        return None
    
    def _check_attribute(self, node: ast.Attribute, code: str) -> Optional[SecurityIssue]:
        """Check for dangerous attribute access."""
        dangerous_attrs = {
            "__class__": SeverityLevel.MEDIUM,
            "__bases__": SeverityLevel.HIGH,
            "__subclasses__": SeverityLevel.CRITICAL,
            "__globals__": SeverityLevel.CRITICAL,
            "__code__": SeverityLevel.HIGH,
        }
        
        if node.attr in dangerous_attrs:
            return SecurityIssue(
                category=VulnerabilityCategory.INJECTION,
                severity=dangerous_attrs[node.attr],
                message=f"Dangerous attribute access: {node.attr}",
                line_number=node.lineno,
                code_snippet=ast.get_source_segment(code, node) or "",
                recommendation="Avoid accessing dunder attributes for security"
            )
        return None
    
    def _calculate_risk_score(self, issues: List[SecurityIssue]) -> float:
        """Calculate overall risk score (0-100)."""
        if not issues:
            return 0.0
        
        severity_weights = {
            SeverityLevel.INFO: 1,
            SeverityLevel.LOW: 5,
            SeverityLevel.MEDIUM: 15,
            SeverityLevel.HIGH: 35,
            SeverityLevel.CRITICAL: 50,
        }
        
        total_weight = sum(severity_weights[i.severity] for i in issues)
        return min(100.0, total_weight)
    
    def _get_recommendation(self, category: VulnerabilityCategory, pattern: str) -> str:
        """Get recommendation based on category."""
        recommendations = {
            VulnerabilityCategory.INJECTION: "Use parameterized queries or safe APIs",
            VulnerabilityCategory.FILE_ACCESS: "Validate and sanitize file paths",
            VulnerabilityCategory.NETWORK: "Use secure protocols (HTTPS/TLS)",
            VulnerabilityCategory.SERIALIZATION: "Use safe serialization formats (JSON)",
            VulnerabilityCategory.CRYPTO: "Use modern cryptographic algorithms",
            VulnerabilityCategory.PROCESS: "Avoid shell=True, use subprocess.run with list",
            VulnerabilityCategory.MEMORY: "Use memory-safe constructs",
            VulnerabilityCategory.PRIVILEGE: "Follow least-privilege principle",
        }
        return recommendations.get(category, "Review for security implications")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics."""
        return {
            "total_audits": self._audit_count,
            "rejections": self._rejection_count,
            "approval_rate": (
                (self._audit_count - self._rejection_count) / self._audit_count * 100
                if self._audit_count > 0 else 100.0
            )
        }
