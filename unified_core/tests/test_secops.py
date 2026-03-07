"""
Tests for SecOpsAgent security analysis
"""
import pytest
from unified_core.secops_agent import (
    SecOpsAgent, SeverityLevel, VulnerabilityCategory, SecurityIssue
)
from unified_core.dev_agent import CodeArtifact, CodeLanguage


class TestPatternDetection:
    """Test vulnerability pattern detection."""
    
    @pytest.fixture
    def agent(self):
        return SecOpsAgent()
    
    @pytest.mark.asyncio
    async def test_detect_eval(self, agent):
        """Detect eval() as critical injection."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='result = eval(user_input)',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        assert not result.approved
        assert any("eval" in i.lower() for i in result.issues)
        assert result.risk_score >= 50
    
    @pytest.mark.asyncio
    async def test_detect_exec(self, agent):
        """Detect exec() as critical injection."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='exec(code_string)',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        assert not result.approved
        assert any("exec" in i.lower() for i in result.issues)
    
    @pytest.mark.asyncio
    async def test_detect_shell_injection(self, agent):
        """Detect shell=True subprocess."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='subprocess.run(cmd, shell=True)',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        assert not result.approved
        assert any("shell" in i.lower() for i in result.issues)
    
    @pytest.mark.asyncio
    async def test_detect_pickle(self, agent):
        """Detect pickle.load as unsafe deserialization."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='data = pickle.load(file)',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        assert not result.approved
        assert any("pickle" in i.lower() or "deserialization" in i.lower() for i in result.issues)
    
    @pytest.mark.asyncio
    async def test_detect_path_traversal(self, agent):
        """Detect path traversal attempts."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='open("../../etc/passwd")',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        assert not result.approved
        # Either path traversal or sensitive file detected
        assert len(result.issues) > 0


class TestASTAnalysis:
    """Test AST-based security analysis."""
    
    @pytest.fixture
    def agent(self):
        return SecOpsAgent()
    
    @pytest.mark.asyncio
    async def test_dangerous_dunder_access(self, agent):
        """Detect dangerous __class__ access."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='obj.__class__.__bases__[0].__subclasses__()',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        assert not result.approved
        # Should detect multiple dangerous attributes
        assert len(result.detailed_issues) >= 1
    
    @pytest.mark.asyncio
    async def test_blocked_import(self, agent):
        """Detect blocked module imports."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='import ctypes\nctypes.windll',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        assert not result.approved
        assert any("ctypes" in i.lower() or "blocked" in i.lower() for i in result.issues)
    
    @pytest.mark.asyncio
    async def test_syntax_error_detection(self, agent):
        """Detect syntax errors (potential injection)."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='def foo( { broken',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        # Syntax error should be flagged
        assert not result.approved or any("syntax" in i.lower() for i in result.issues)


class TestApprovalThreshold:
    """Test severity threshold for approval."""
    
    @pytest.mark.asyncio
    async def test_low_severity_approved(self):
        """Low severity issues can be approved."""
        agent = SecOpsAgent(max_severity=SeverityLevel.MEDIUM)
        
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='import random\nvalue = random.random()',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        # random.random is LOW severity - should be approved
        assert result.approved or len([i for i in result.detailed_issues if i.severity.value > SeverityLevel.MEDIUM.value]) == 0
    
    @pytest.mark.asyncio
    async def test_safe_code_approved(self):
        """Clean code passes audit."""
        agent = SecOpsAgent()
        
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='''
def calculate_sum(a: int, b: int) -> int:
    """Add two numbers safely."""
    return a + b

def test_calculate_sum():
    assert calculate_sum(1, 2) == 3
''',
            filename="calculator.py",
            description="Simple calculator"
        )
        result = await agent.audit(code)
        
        assert result.approved
        assert result.risk_score < 20


class TestRiskScoring:
    """Test risk score calculation."""
    
    @pytest.fixture
    def agent(self):
        return SecOpsAgent()
    
    @pytest.mark.asyncio
    async def test_critical_high_score(self, agent):
        """Critical vulnerabilities have high risk score."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='eval(input()) and exec(code)',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        assert result.risk_score >= 50
    
    @pytest.mark.asyncio
    async def test_clean_zero_score(self, agent):
        """Clean code has zero risk score."""
        code = CodeArtifact(
            language=CodeLanguage.PYTHON,
            code='x = 1 + 1',
            filename="test.py",
            description="Test"
        )
        result = await agent.audit(code)
        
        assert result.risk_score == 0


class TestStats:
    """Test audit statistics."""
    
    @pytest.mark.asyncio
    async def test_audit_stats(self):
        """Stats are tracked correctly."""
        agent = SecOpsAgent()
        
        safe = CodeArtifact(CodeLanguage.PYTHON, "x = 1", "t.py", "")
        dangerous = CodeArtifact(CodeLanguage.PYTHON, "eval(x)", "t.py", "")
        
        await agent.audit(safe)
        await agent.audit(dangerous)
        
        stats = agent.get_stats()
        
        assert stats["total_audits"] == 2
        assert stats["rejections"] >= 1
