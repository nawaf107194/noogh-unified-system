"""
Security Audit Runner for Database Layer

Master audit script that:
1. Runs all Phase 1 security tests
2. Collects metrics and findings
3. Generates structured audit report
4. Calculates security scores

CVSS 3.1 Scoring Reference:
- Critical: 9.0-10.0
- High: 7.0-8.9
- Medium: 4.0-6.9
- Low: 0.1-3.9
- None: 0.0
"""
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Vulnerability:
    """Detected vulnerability."""
    id: str
    title: str
    severity: Severity
    cvss_score: float
    category: str
    description: str
    affected_component: str
    cwe_id: str
    recommendation: str
    evidence: str = ""
    status: str = "open"


@dataclass
class AuditFinding:
    """Audit finding from test execution."""
    test_file: str
    test_name: str
    passed: bool
    duration_seconds: float
    error_message: Optional[str] = None
    vulnerabilities: List[Vulnerability] = field(default_factory=list)


@dataclass
class AuditReport:
    """Complete audit report."""
    timestamp: str
    phase: str
    component: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    security_score: float
    vulnerabilities: List[Vulnerability]
    findings: List[AuditFinding]
    summary: Dict[str, Any]


class DatabaseSecurityAuditor:
    """Security auditor for database layer."""
    
    def __init__(self, test_dir: str = "tests/phase1"):
        self.test_dir = Path(test_dir)
        self.findings: List[AuditFinding] = []
        self.vulnerabilities: List[Vulnerability] = []
        self.base_path = Path("/home/noogh/projects/noogh_unified_system/src")
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 1 security tests."""
        results = {
            "injection_tests": self._run_injection_tests(),
            "fuzzing_tests": self._run_fuzzing_tests(),
            "race_condition_tests": self._run_race_tests(),
            "consistency_tests": self._run_consistency_tests(),
            "benchmark_tests": self._run_benchmark_tests(),
        }
        return results
    
    def _run_pytest(self, test_file: str, markers: str = "") -> Tuple[bool, str, float]:
        """Run pytest on a specific file."""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.base_path / self.test_dir / test_file),
            "-v", "--tb=short", "-q"
        ]
        if markers:
            cmd.extend(["-m", markers])
        
        start = datetime.now()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.base_path)
            )
            elapsed = (datetime.now() - start).total_seconds()
            passed = result.returncode == 0
            output = result.stdout + result.stderr
            return passed, output, elapsed
        except subprocess.TimeoutExpired:
            return False, "Test timed out after 300 seconds", 300.0
        except Exception as e:
            return False, str(e), 0.0
    
    def _run_injection_tests(self) -> Dict[str, Any]:
        """Run SQL injection tests."""
        passed, output, duration = self._run_pytest("test_sql_injection_comprehensive.py")
        
        finding = AuditFinding(
            test_file="test_sql_injection_comprehensive.py",
            test_name="SQL Injection Comprehensive",
            passed=passed,
            duration_seconds=duration,
            error_message=output if not passed else None
        )
        
        # Add vulnerabilities based on test failures
        if not passed:
            self.vulnerabilities.append(Vulnerability(
                id="DB-001",
                title="SQL Injection Vulnerability Detected",
                severity=Severity.CRITICAL,
                cvss_score=9.8,
                category="Injection",
                description="SQL injection tests detected potential vulnerabilities in query handling",
                affected_component="unified_core.db.postgres",
                cwe_id="CWE-89",
                recommendation="Use parameterized queries exclusively; implement input validation layer",
                evidence=output[:500] if output else ""
            ))
        
        self.findings.append(finding)
        return {"passed": passed, "duration": duration}
    
    def _run_fuzzing_tests(self) -> Dict[str, Any]:
        """Run fuzzing tests."""
        passed, output, duration = self._run_pytest("test_data_router_fuzzing.py")
        
        finding = AuditFinding(
            test_file="test_data_router_fuzzing.py",
            test_name="DataRouter Fuzzing",
            passed=passed,
            duration_seconds=duration,
            error_message=output if not passed else None
        )
        
        if not passed:
            self.vulnerabilities.append(Vulnerability(
                id="DB-002",
                title="Input Validation Bypass",
                severity=Severity.HIGH,
                cvss_score=7.5,
                category="Input Validation",
                description="Fuzzing detected potential input validation bypass vulnerabilities",
                affected_component="unified_core.db.router",
                cwe_id="CWE-20",
                recommendation="Implement comprehensive input sanitization; add type checking at entry points",
                evidence=output[:500] if output else ""
            ))
        
        self.findings.append(finding)
        return {"passed": passed, "duration": duration}
    
    def _run_race_tests(self) -> Dict[str, Any]:
        """Run race condition tests."""
        passed, output, duration = self._run_pytest("test_routing_race_conditions.py")
        
        finding = AuditFinding(
            test_file="test_routing_race_conditions.py",
            test_name="Race Condition Detection",
            passed=passed,
            duration_seconds=duration,
            error_message=output if not passed else None
        )
        
        if not passed:
            self.vulnerabilities.append(Vulnerability(
                id="DB-003",
                title="Race Condition in Database Routing",
                severity=Severity.MEDIUM,
                cvss_score=5.9,
                category="Concurrency",
                description="Race conditions detected in concurrent database operations",
                affected_component="unified_core.db.router",
                cwe_id="CWE-362",
                recommendation="Implement proper locking mechanisms; use thread-safe data structures",
                evidence=output[:500] if output else ""
            ))
        
        self.findings.append(finding)
        return {"passed": passed, "duration": duration}
    
    def _run_consistency_tests(self) -> Dict[str, Any]:
        """Run cross-database consistency tests."""
        passed, output, duration = self._run_pytest("test_cross_db_consistency.py")
        
        finding = AuditFinding(
            test_file="test_cross_db_consistency.py",
            test_name="Cross-Database Consistency",
            passed=passed,
            duration_seconds=duration,
            error_message=output if not passed else None
        )
        
        if not passed:
            self.vulnerabilities.append(Vulnerability(
                id="DB-004",
                title="Data Consistency Violation",
                severity=Severity.HIGH,
                cvss_score=7.1,
                category="Data Integrity",
                description="Cross-database consistency violations detected",
                affected_component="unified_core.db",
                cwe_id="CWE-669",
                recommendation="Implement distributed transaction management; add consistency checks",
                evidence=output[:500] if output else ""
            ))
        
        self.findings.append(finding)
        return {"passed": passed, "duration": duration}
    
    def _run_benchmark_tests(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        passed, output, duration = self._run_pytest("benchmark_routing_performance.py")
        
        finding = AuditFinding(
            test_file="benchmark_routing_performance.py",
            test_name="Performance Benchmarks",
            passed=passed,
            duration_seconds=duration,
            error_message=output if not passed else None
        )
        
        if not passed:
            self.vulnerabilities.append(Vulnerability(
                id="DB-005",
                title="Performance Degradation Risk",
                severity=Severity.LOW,
                cvss_score=3.7,
                category="Availability",
                description="Performance benchmarks indicate potential DoS vulnerability",
                affected_component="unified_core.db.router",
                cwe_id="CWE-400",
                recommendation="Implement rate limiting; optimize classification algorithms",
                evidence=output[:500] if output else ""
            ))
        
        self.findings.append(finding)
        return {"passed": passed, "duration": duration}
    
    def calculate_security_score(self) -> float:
        """Calculate overall security score (0-100)."""
        if not self.findings:
            return 100.0
        
        # Weight by severity
        severity_weights = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 25,
            Severity.MEDIUM: 50,
            Severity.LOW: 75,
            Severity.INFO: 90,
        }
        
        if not self.vulnerabilities:
            passed_count = sum(1 for f in self.findings if f.passed)
            return (passed_count / len(self.findings)) * 100
        
        # Calculate based on worst vulnerability
        worst_severity = min(v.severity.value for v in self.vulnerabilities)
        severity_obj = next((s for s in Severity if s.value == worst_severity), Severity.INFO)
        base_score = severity_weights.get(severity_obj, 50)
        
        # Adjust for number of vulnerabilities
        vuln_penalty = min(len(self.vulnerabilities) * 5, 30)
        
        return max(0, base_score - vuln_penalty)
    
    def generate_report(self) -> AuditReport:
        """Generate complete audit report."""
        passed = sum(1 for f in self.findings if f.passed)
        failed = sum(1 for f in self.findings if not f.passed)
        
        return AuditReport(
            timestamp=datetime.now().isoformat(),
            phase="Phase 1",
            component="Database Orchestration Layer",
            total_tests=len(self.findings),
            passed_tests=passed,
            failed_tests=failed,
            security_score=self.calculate_security_score(),
            vulnerabilities=self.vulnerabilities,
            findings=self.findings,
            summary={
                "critical_count": sum(1 for v in self.vulnerabilities if v.severity == Severity.CRITICAL),
                "high_count": sum(1 for v in self.vulnerabilities if v.severity == Severity.HIGH),
                "medium_count": sum(1 for v in self.vulnerabilities if v.severity == Severity.MEDIUM),
                "low_count": sum(1 for v in self.vulnerabilities if v.severity == Severity.LOW),
                "test_coverage": f"{passed}/{len(self.findings)} tests passed",
            }
        )
    
    def save_report_json(self, report: AuditReport, output_path: str):
        """Save report as JSON."""
        report_dict = {
            "timestamp": report.timestamp,
            "phase": report.phase,
            "component": report.component,
            "total_tests": report.total_tests,
            "passed_tests": report.passed_tests,
            "failed_tests": report.failed_tests,
            "security_score": report.security_score,
            "vulnerabilities": [
                {
                    "id": v.id,
                    "title": v.title,
                    "severity": v.severity.value,
                    "cvss_score": v.cvss_score,
                    "category": v.category,
                    "description": v.description,
                    "affected_component": v.affected_component,
                    "cwe_id": v.cwe_id,
                    "recommendation": v.recommendation,
                    "status": v.status
                }
                for v in report.vulnerabilities
            ],
            "summary": report.summary
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
    
    def generate_markdown_report(self, report: AuditReport) -> str:
        """Generate markdown report."""
        md = []
        md.append("# Phase 1: Database Security Audit Report\n")
        md.append(f"**Generated:** {report.timestamp}\n")
        md.append(f"**Component:** {report.component}\n")
        md.append(f"**Security Score:** {report.security_score:.1f}/100\n")
        
        # Executive Summary
        md.append("\n## Executive Summary\n")
        md.append(f"- **Tests Executed:** {report.total_tests}\n")
        md.append(f"- **Tests Passed:** {report.passed_tests}\n")
        md.append(f"- **Tests Failed:** {report.failed_tests}\n")
        md.append(f"- **Critical Vulnerabilities:** {report.summary['critical_count']}\n")
        md.append(f"- **High Vulnerabilities:** {report.summary['high_count']}\n")
        md.append(f"- **Medium Vulnerabilities:** {report.summary['medium_count']}\n")
        md.append(f"- **Low Vulnerabilities:** {report.summary['low_count']}\n")
        
        # Vulnerabilities
        if report.vulnerabilities:
            md.append("\n## Vulnerability Findings\n")
            for v in sorted(report.vulnerabilities, key=lambda x: x.cvss_score, reverse=True):
                md.append(f"\n### {v.id}: {v.title}\n")
                md.append(f"- **Severity:** {v.severity.value.upper()} (CVSS: {v.cvss_score})\n")
                md.append(f"- **Category:** {v.category}\n")
                md.append(f"- **CWE:** {v.cwe_id}\n")
                md.append(f"- **Affected Component:** `{v.affected_component}`\n")
                md.append(f"\n**Description:** {v.description}\n")
                md.append(f"\n**Recommendation:** {v.recommendation}\n")
        else:
            md.append("\n## Vulnerability Findings\n")
            md.append("\n> [!TIP]\n> No vulnerabilities detected. All security tests passed.\n")
        
        # Test Results
        md.append("\n## Test Results\n")
        md.append("| Test File | Result | Duration |\n")
        md.append("|-----------|--------|----------|\n")
        for f in report.findings:
            status = "✅ PASS" if f.passed else "❌ FAIL"
            md.append(f"| {f.test_file} | {status} | {f.duration_seconds:.2f}s |\n")
        
        return "".join(md)


async def main():
    """Main entry point for security audit."""
    print("=" * 60)
    print("DATABASE SECURITY AUDIT - PHASE 1")
    print("=" * 60)
    
    auditor = DatabaseSecurityAuditor()
    
    print("\n[1/5] Running SQL Injection Tests...")
    results = await auditor.run_all_tests()
    
    print("\n[2/5] Calculating Security Score...")
    report = auditor.generate_report()
    
    print("\n[3/5] Generating Reports...")
    
    # Save JSON report
    json_path = "/home/noogh/projects/noogh_unified_system/src/reports/phase1_audit_results.json"
    auditor.save_report_json(report, json_path)
    print(f"  JSON report: {json_path}")
    
    # Generate markdown
    md_content = auditor.generate_markdown_report(report)
    md_path = "/home/noogh/projects/noogh_unified_system/src/reports/phase1_database_security_report.md"
    with open(md_path, 'w') as f:
        f.write(md_content)
    print(f"  Markdown report: {md_path}")
    
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"Security Score: {report.security_score:.1f}/100")
    print(f"Tests: {report.passed_tests}/{report.total_tests} passed")
    print(f"Vulnerabilities: {len(report.vulnerabilities)}")
    for v in report.vulnerabilities:
        print(f"  - [{v.severity.value.upper()}] {v.id}: {v.title}")
    print("=" * 60)
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
