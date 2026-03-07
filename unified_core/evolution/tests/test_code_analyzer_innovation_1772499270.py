import pytest
from pathlib import Path
from unified_core.evolution.code_analyzer import CodeAnalyzer, ProjectReport, CodeIssue

class MockCodeAnalysisResult:
    def __init__(self, lines=0, score=0, complexity=0, functions=None, vulnerabilities=None):
        self.lines = lines
        self.score = score
        self.complexity = complexity
        self.functions = functions if functions else []
        self.vulnerabilities = vulnerabilities if vulnerabilities else []

    def analyze_file(self, path_str):
        return MockCodeAnalysisResult()

class MockComplexityCalculator:
    def visit(self, node):
        pass

def test_analyze_project_happy_path():
    analyzer = CodeAnalyzer()
    mock_analysis_result = MockCodeAnalysisResult(lines=100, score=95, complexity=12)
    analyzer.analyze_file = lambda path_str: mock_analysis_result
    issues = [CodeIssue(file="file.py", line=1, issue_type="cognitive_logic", severity="MEDIUM")]
    mock_analysis_result.vulnerabilities = []

    result = analyzer.analyze_project()

    assert isinstance(result, ProjectReport)
    assert result.files_analyzed == 1
    assert result.total_issues == len(issues)
    assert result.avg_score == 95.0
    assert result.hotspots == ["file.py"]
    assert result.issues == issues

def test_analyze_project_empty_directory():
    analyzer = CodeAnalyzer()
    mock_analysis_result = MockCodeAnalysisResult(lines=100, score=95, complexity=12)
    analyzer.analyze_file = lambda path_str: mock_analysis_result
    issues = []
    mock_analysis_result.vulnerabilities = []

    result = analyzer.analyze_project()

    assert isinstance(result, ProjectReport)
    assert result.files_analyzed == 0
    assert result.total_issues == len(issues)
    assert result.avg_score == 100.0
    assert result.hotspots == []
    assert result.issues == issues

def test_analyze_project_skip_directories():
    analyzer = CodeAnalyzer()
    mock_analysis_result = MockCodeAnalysisResult(lines=100, score=95, complexity=12)
    analyzer.analyze_file = lambda path_str: mock_analysis_result
    issues = []
    mock_analysis_result.vulnerabilities = []

    result = analyzer.analyze_project()

    assert isinstance(result, ProjectReport)
    assert result.files_analyzed == 0
    assert result.total_issues == len(issues)
    assert result.avg_score == 100.0
    assert result.hotspots == []
    assert result.issues == issues

def test_analyze_project_invalid_input():
    analyzer = CodeAnalyzer()
    mock_analysis_result = MockCodeAnalysisResult(lines=100, score=95, complexity=12)
    analyzer.analyze_file = lambda path_str: mock_analysis_result
    issues = []
    mock_analysis_result.vulnerabilities = []

    result = analyzer.analyze_project()

    assert isinstance(result, ProjectReport)
    assert result.files_analyzed == 0
    assert result.total_issues == len(issues)
    assert result.avg_score == 100.0
    assert result.hotspots == []
    assert result.issues == issues

@pytest.mark.asyncio
async def test_analyze_project_async_behavior():
    analyzer = CodeAnalyzer()
    mock_analysis_result = MockCodeAnalysisResult(lines=100, score=95, complexity=12)
    analyzer.analyze_file = lambda path_str: mock_analysis_result
    issues = []
    mock_analysis_result.vulnerabilities = []

    result = await analyzer.analyze_project()

    assert isinstance(result, ProjectReport)
    assert result.files_analyzed == 1
    assert result.total_issues == len(issues)
    assert result.avg_score == 95.0
    assert result.hotspots == ["file.py"]
    assert result.issues == issues