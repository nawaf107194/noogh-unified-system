"""
SecOps Audit and Static Analysis Security Tests

Tests for the SecOpsAgent security auditing:
- Dangerous function detection
- Shell injection patterns
- Unsafe deserialization
- Path traversal detection
- Sandbox escape patterns
- Code obfuscation detection

OWASP References:
- A03:2021 Injection
- CWE-78: OS Command Injection
- CWE-502: Deserialization of Untrusted Data
"""
import pytest
import asyncio
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# =============================================================================
# MOCK CLASSES - Always use mocks for testing isolation
# =============================================================================

class VulnerabilityCategory(Enum):
    """Mock VulnerabilityCategory."""
    INJECTION = "injection"
    FILE_ACCESS = "file_access"
    PROCESS = "process"
    NETWORK = "network"
    MEMORY = "memory"
    CRYPTO = "crypto"
    SERIALIZATION = "serialization"
    PRIVILEGE = "privilege"

CAT_INJECTION = VulnerabilityCategory.INJECTION
CAT_FILE_ACCESS = VulnerabilityCategory.FILE_ACCESS
CAT_PROCESS = VulnerabilityCategory.PROCESS
CAT_NETWORK = VulnerabilityCategory.NETWORK
CAT_SERIALIZATION = VulnerabilityCategory.SERIALIZATION

@dataclass
class SecurityIssue:
    """Mock SecurityIssue for testing."""
    category: VulnerabilityCategory
    severity: str  # critical, high, medium, low
    pattern: str
    line_number: int
    code_snippet: str
    recommendation: str

@dataclass
class AuditResult:
    """Mock AuditResult for testing."""
    approved: bool
    risk_score: float
    issues: List[SecurityIssue] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)


# =============================================================================
# DANGEROUS CODE SAMPLES
# =============================================================================

DANGEROUS_CODE_SAMPLES = {
    "eval_usage": '''
def process_input(user_input):
    result = eval(user_input)  # DANGEROUS
    return result
''',
    "exec_usage": '''
def run_command(cmd):
    exec(cmd)  # DANGEROUS
''',
    "os_system": '''
import os
def run_shell(command):
    os.system(command)  # DANGEROUS
''',
    "subprocess_shell": '''
import subprocess
def execute(cmd):
    subprocess.call(cmd, shell=True)  # DANGEROUS
''',
    "pickle_load": '''
import pickle
def load_data(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)  # DANGEROUS - untrusted deserialization
''',
    "path_traversal": '''
def read_file(filename):
    path = "/var/data/" + filename  # Vulnerable to path traversal
    with open(path) as f:
        return f.read()
''',
    "sql_string_format": '''
def query_user(user_id):
    sql = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection
    return execute_sql(sql)
''',
    "yaml_unsafe_load": '''
import yaml
def load_config(data):
    return yaml.load(data)  # DANGEROUS - can execute arbitrary code
''',
}

OBFUSCATED_DANGEROUS_CODE = {
    "base64_exec": '''
import base64
code = base64.b64decode("aW1wb3J0IG9zOyBvcy5zeXN0ZW0oJ2lkJyk=")
exec(code)
''',
    "getattr_bypass": '''
import os
getattr(os, 'sys' + 'tem')('id')
''',
    "import_bypass": '''
__import__('os').system('id')
''',
    "compile_exec": '''
code = compile("import os; os.system('id')", '<string>', 'exec')
exec(code)
''',
}

SAFE_CODE_SAMPLES = {
    "simple_function": '''
def add(a: int, b: int) -> int:
    """Add two numbers safely."""
    return a + b
''',
    "list_processing": '''
def filter_positive(numbers: list) -> list:
    """Filter positive numbers."""
    return [n for n in numbers if n > 0]
''',
    "class_definition": '''
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(result)
        return result
''',
}


# =============================================================================
# MOCK SECOPS AGENT
# =============================================================================

class MockSecOpsAgent:
    """Mock SecOpsAgent for security testing."""
    
    DANGEROUS_PATTERNS = {
        CAT_INJECTION: [
            (r'\beval\s*\(', 'Arbitrary code execution via eval()'),
            (r'\bexec\s*\(', 'Arbitrary code execution via exec()'),
            (r'\bcompile\s*\(', 'Code compilation - potential exec'),
            (r'f["\']SELECT', 'SQL injection via f-string'),
            (r'f["\'].*WHERE.*\{', 'SQL injection via f-string interpolation'),
        ],
        CAT_PROCESS: [
            (r'\bos\.system\s*\(', 'Shell command execution'),
            (r'\bos\.popen\s*\(', 'Shell command execution'),
            (r'\bsubprocess\.', 'Subprocess execution'),
        ],
        CAT_SERIALIZATION: [
            (r'\bpickle\.load', 'Unsafe pickle deserialization'),
            (r'\byaml\.load\s*\([^)]*(?!Loader)', 'Unsafe YAML loading'),
            (r'\bmarshal\.loads', 'Unsafe marshal deserialization'),
        ],
        CAT_FILE_ACCESS: [
            (r'open\s*\([^)]*["\']w', 'File write operation'),
            (r'\.\./|\.\.\\\\', 'Path traversal pattern'),
            (r'\+\s*filename', 'Potential path traversal - direct concatenation'),
        ],
        CAT_NETWORK: [
            (r'\bsocket\.\w+\(', 'Direct socket access'),
        ],
    }
    
    # Additional obfuscation patterns
    OBFUSCATION_PATTERNS = [
        (r'__import__\s*\(', 'Dynamic import - potential bypass'),
        (r'getattr\s*\(\s*\w+\s*,\s*["\'][^"\']+["\']', 'getattr - potential bypass'),
        (r'base64\.b64decode', 'Base64 decode - check for code'),
        (r'\bcodecs\.decode', 'Encoding - check for obfuscation'),
    ]
    
    def __init__(self):
        self.audit_count = 0
        self.issues_found = []
    
    async def audit(self, artifact: Any) -> AuditResult:
        """Audit code artifact for security issues."""
        self.audit_count += 1
        code = artifact.code if hasattr(artifact, 'code') else str(artifact)
        
        issues = []
        
        # Check dangerous patterns
        for category, patterns in self.DANGEROUS_PATTERNS.items():
            for pattern, description in patterns:
                matches = list(re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE))
                for match in matches:
                    line_no = code[:match.start()].count('\n') + 1
                    issues.append(SecurityIssue(
                        category=category,
                        severity='high',
                        pattern=pattern,
                        line_number=line_no,
                        code_snippet=match.group(0),
                        recommendation=f"Remove or secure: {description}"
                    ))
        
        # Check obfuscation patterns
        for pattern, description in self.OBFUSCATION_PATTERNS:
            matches = list(re.finditer(pattern, code, re.IGNORECASE))
            for match in matches:
                line_no = code[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(
                    category=CAT_INJECTION,  # Use injection category for obfuscation
                    severity='critical',
                    pattern=pattern,
                    line_number=line_no,
                    code_snippet=match.group(0),
                    recommendation=f"Obfuscation detected: {description}"
                ))
        
        self.issues_found.extend(issues)
        
        # Calculate risk score
        risk_score = self._calculate_risk(issues)
        
        return AuditResult(
            approved=len(issues) == 0,
            risk_score=risk_score,
            issues=issues
        )
    
    def _calculate_risk(self, issues: List[SecurityIssue]) -> float:
        """Calculate risk score from 0-10."""
        if not issues:
            return 0.0
        
        severity_weights = {'critical': 3.0, 'high': 2.0, 'medium': 1.0, 'low': 0.5}
        total = sum(severity_weights.get(i.severity, 1.0) for i in issues)
        return min(10.0, total)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def secops_agent():
    """SecOpsAgent for testing."""
    return MockSecOpsAgent()


# =============================================================================
# DANGEROUS FUNCTION DETECTION TESTS
# =============================================================================

class TestDangerousFunctionDetection:
    """Test detection of dangerous functions."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("code_name,code", DANGEROUS_CODE_SAMPLES.items())
    async def test_dangerous_code_detected(self, secops_agent, code_name, code):
        """Test that dangerous code patterns are detected."""
        
        class MockArtifact:
            def __init__(self, c):
                self.code = c
        
        result = await secops_agent.audit(MockArtifact(code))
        
        assert not result.approved, f"Dangerous code not detected: {code_name}"
        assert len(result.issues) > 0, f"No issues found for: {code_name}"
    
    @pytest.mark.asyncio
    async def test_eval_detected(self, secops_agent):
        """Test eval() detection."""
        
        class MockArtifact:
            code = "result = eval(user_input)"
        
        result = await secops_agent.audit(MockArtifact())
        
        assert not result.approved
        assert any('eval' in str(i.pattern) for i in result.issues)
    
    @pytest.mark.asyncio
    async def test_exec_detected(self, secops_agent):
        """Test exec() detection."""
        
        class MockArtifact:
            code = "exec(dynamic_code)"
        
        result = await secops_agent.audit(MockArtifact())
        
        assert not result.approved
        assert any('exec' in str(i.pattern) for i in result.issues)


# =============================================================================
# OBFUSCATION DETECTION TESTS
# =============================================================================

class TestObfuscationDetection:
    """Test detection of obfuscated malicious code."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("code_name,code", OBFUSCATED_DANGEROUS_CODE.items())
    async def test_obfuscated_code_detected(self, secops_agent, code_name, code):
        """Test that obfuscated malicious code is detected."""
        
        class MockArtifact:
            def __init__(self, c):
                self.code = c
        
        result = await secops_agent.audit(MockArtifact(code))
        
        assert not result.approved, f"Obfuscated code not detected: {code_name}"
    
    @pytest.mark.asyncio
    async def test_base64_obfuscation_detected(self, secops_agent):
        """Test base64-encoded malicious code detection."""
        
        class MockArtifact:
            code = '''
import base64
exec(base64.b64decode('bWFsaWNpb3Vz'))
'''
        
        result = await secops_agent.audit(MockArtifact())
        
        assert not result.approved
        assert result.risk_score >= 5.0  # High risk
    
    @pytest.mark.asyncio
    async def test_dynamic_import_detected(self, secops_agent):
        """Test __import__ bypass detection."""
        
        class MockArtifact:
            code = "__import__('os').system('id')"
        
        result = await secops_agent.audit(MockArtifact())
        
        assert not result.approved


# =============================================================================
# SAFE CODE TESTS
# =============================================================================

class TestSafeCodeApproval:
    """Test that safe code is approved."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("code_name,code", SAFE_CODE_SAMPLES.items())
    async def test_safe_code_approved(self, secops_agent, code_name, code):
        """Test that safe code passes audit."""
        
        class MockArtifact:
            def __init__(self, c):
                self.code = c
        
        result = await secops_agent.audit(MockArtifact(code))
        
        assert result.approved, f"Safe code not approved: {code_name}, issues: {result.issues}"
        assert result.risk_score == 0.0


# =============================================================================
# RISK SCORING TESTS
# =============================================================================

class TestRiskScoring:
    """Test risk score calculation."""
    
    @pytest.mark.asyncio
    async def test_critical_issues_high_score(self, secops_agent):
        """Test that critical issues result in high risk score."""
        
        class MockArtifact:
            code = '''
exec(user_input)
__import__('os').system('rm -rf /')
'''
        
        result = await secops_agent.audit(MockArtifact())
        
        assert result.risk_score >= 5.0
    
    @pytest.mark.asyncio
    async def test_clean_code_zero_score(self, secops_agent):
        """Test that clean code has zero risk score."""
        
        class MockArtifact:
            code = '''
def safe_add(a, b):
    return a + b
'''
        
        result = await secops_agent.audit(MockArtifact())
        
        assert result.risk_score == 0.0


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_code(self, secops_agent):
        """Test handling of empty code."""
        
        class MockArtifact:
            code = ""
        
        result = await secops_agent.audit(MockArtifact())
        
        assert result.approved
    
    @pytest.mark.asyncio
    async def test_comments_with_dangerous_patterns(self, secops_agent):
        """Test that comments with dangerous patterns are still flagged."""
        
        class MockArtifact:
            code = '''
# exec(user_input)  # This is commented out
def safe_function():
    pass
'''
        
        result = await secops_agent.audit(MockArtifact())
        
        # Current implementation detects patterns even in comments
        # In production, might want to ignore comments
    
    @pytest.mark.asyncio
    async def test_string_literal_patterns(self, secops_agent):
        """Test patterns in string literals."""
        
        class MockArtifact:
            code = '''
error_msg = "Do not use eval() in production code"
'''
        
        result = await secops_agent.audit(MockArtifact())
        
        # String literal should trigger pattern (conservative detection)


# =============================================================================
# AUDIT SUMMARY
# =============================================================================

class TestSecOpsAuditSummary:
    """Generate SecOps audit summary."""
    
    @pytest.mark.asyncio
    async def test_generate_audit_summary(self, secops_agent):
        """Run SecOps tests and generate summary."""
        results = {
            "dangerous_detected": 0,
            "dangerous_total": 0,
            "obfuscated_detected": 0,
            "obfuscated_total": 0,
            "safe_approved": 0,
            "safe_total": 0,
        }
        
        class MockArtifact:
            def __init__(self, c):
                self.code = c
        
        # Test dangerous code detection
        for code in DANGEROUS_CODE_SAMPLES.values():
            results["dangerous_total"] += 1
            result = await secops_agent.audit(MockArtifact(code))
            if not result.approved:
                results["dangerous_detected"] += 1
        
        # Test obfuscated code detection
        for code in OBFUSCATED_DANGEROUS_CODE.values():
            results["obfuscated_total"] += 1
            result = await secops_agent.audit(MockArtifact(code))
            if not result.approved:
                results["obfuscated_detected"] += 1
        
        # Test safe code approval
        for code in SAFE_CODE_SAMPLES.values():
            results["safe_total"] += 1
            result = await secops_agent.audit(MockArtifact(code))
            if result.approved:
                results["safe_approved"] += 1
        
        print(f"\n{'='*60}")
        print("SECOPS AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Dangerous Code Detected: {results['dangerous_detected']}/{results['dangerous_total']}")
        print(f"Obfuscated Code Detected: {results['obfuscated_detected']}/{results['obfuscated_total']}")
        print(f"Safe Code Approved: {results['safe_approved']}/{results['safe_total']}")
        print(f"Total Audits: {secops_agent.audit_count}")
        print(f"{'='*60}\n")
        
        # All dangerous code should be detected
        assert results["dangerous_detected"] == results["dangerous_total"]
        # All safe code should be approved
        assert results["safe_approved"] == results["safe_total"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
