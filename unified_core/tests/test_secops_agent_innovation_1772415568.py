import pytest
import re

from unified_core.secops_agent import SecOpsAgent, SecurityIssue

class MockSecOpsAgent:
    DANGEROUS_PATTERNS = {
        'SQL_INJECTION': {
            'Python': [
                (r'(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)', 'SQL Injection risk', 1),
                (r'(\bexec\s+sp_executesql\s+)\b', 'SQL Injection via stored procedures', 2)
            ]
        },
        'XSS': {
            'JavaScript': [
                (r'<script>', 'Cross-Site Scripting risk', 3),
                (r'document\.cookie', 'Cookie theft risk', 4)
            ]
        }
    }

def test_scan_patterns_happy_path():
    agent = MockSecOpsAgent()
    code = "import sqlite3; conn = sqlite3.connect('example.db')"
    language = 'Python'
    expected_issues = [
        SecurityIssue(
            category='SQL_INJECTION',
            severity=1,
            message='SQL Injection risk',
            line_number=1,
            code_snippet="import sqlite3;",
            recommendation=SecOpsAgent._get_recommendation(agent, 'SQL_INJECTION', r'(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)')
        )
    ]
    assert agent._scan_patterns(code, language) == expected_issues

def test_scan_patterns_empty_code():
    agent = MockSecOpsAgent()
    code = ""
    language = 'Python'
    assert not agent._scan_patterns(code, language)

def test_scan_patterns_none_code():
    agent = MockSecOpsAgent()
    code = None
    language = 'Python'
    assert not agent._scan_patterns(code, language)

def test_scan_patterns_empty_language():
    agent = MockSecOpsAgent()
    code = "import sqlite3; conn = sqlite3.connect('example.db')"
    language = ''
    assert not agent._scan_patterns(code, language)

def test_scan_patterns_invalid_language():
    agent = MockSecOpsAgent()
    code = "import sqlite3; conn = sqlite3.connect('example.db')"
    language = 'Java'
    assert not agent._scan_patterns(code, language)

def test_scan_patterns_async_behavior():
    # Since _scan_patterns is synchronous, we don't need to test async behavior
    pass

# Run tests
if __name__ == "__main__":
    pytest.main()