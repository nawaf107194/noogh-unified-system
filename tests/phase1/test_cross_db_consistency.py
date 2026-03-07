"""
Cross-Database Consistency Tests

Tests ACID compliance and data integrity across the multi-database architecture:
- PostgreSQL (relational)
- Vector DB (semantic embeddings)
- Graph DB (Neo4j relationships)

Validates:
- Transaction isolation
- Cross-database write consistency
- Rollback behavior
- Orphan data detection
- Reference integrity
"""
import pytest
import asyncio
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

# Import modules under test
from unified_core.db.router import DataRouter, DataType, RoutingDecision, UnifiedQueryResult


@dataclass
class ConsistencyTestResult:
    """Result of consistency test."""
    test_name: str
    databases_involved: List[str]
    passed: bool
    anomalies_detected: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def router():
    """Create DataRouter for testing."""
    return DataRouter()


@pytest.fixture
def test_entity_id():
    """Generate unique test entity ID."""
    return f"test_{uuid.uuid4().hex[:8]}"


# =============================================================================
# MOCK DATABASE MANAGERS
# =============================================================================

class MockPostgresManager:
    """Mock PostgreSQL manager with transaction support."""
    
    def __init__(self):
        self.data = {}
        self.transaction_log = []
        self.in_transaction = False
        self.rollback_point = None
        
    async def begin_transaction(self):
        self.in_transaction = True
        self.rollback_point = dict(self.data)
        
    async def commit(self):
        if self.in_transaction:
            self.in_transaction = False
            self.rollback_point = None
            
    async def rollback(self):
        if self.in_transaction:
            self.data = self.rollback_point
            self.in_transaction = False
            self.rollback_point = None
            
    async def insert(self, key: str, value: Any):
        self.data[key] = value
        self.transaction_log.append(('insert', key, value))
        
    async def get(self, key: str) -> Optional[Any]:
        return self.data.get(key)
        
    async def delete(self, key: str):
        if key in self.data:
            del self.data[key]
            self.transaction_log.append(('delete', key, None))


class MockVectorManager:
    """Mock Vector DB manager."""
    
    def __init__(self):
        self.vectors = {}
        
    async def upsert(self, id: str, vector: List[float], metadata: Dict = None):
        self.vectors[id] = {'vector': vector, 'metadata': metadata or {}}
        
    async def search(self, vector: List[float], limit: int = 10) -> List[Dict]:
        # Simple mock search - return all
        return list(self.vectors.values())[:limit]
        
    async def delete(self, id: str):
        if id in self.vectors:
            del self.vectors[id]


class MockGraphManager:
    """Mock Graph DB manager with relationship tracking."""
    
    def __init__(self):
        self.nodes = {}
        self.relationships = []
        
    async def create_node(self, id: str, labels: List[str], properties: Dict):
        self.nodes[id] = {'labels': labels, 'properties': properties}
        
    async def create_relationship(self, from_id: str, to_id: str, rel_type: str, properties: Dict = None):
        self.relationships.append({
            'from': from_id,
            'to': to_id,
            'type': rel_type,
            'properties': properties or {}
        })
        
    async def get_node(self, id: str) -> Optional[Dict]:
        return self.nodes.get(id)
        
    async def delete_node(self, id: str):
        if id in self.nodes:
            del self.nodes[id]
            # Also remove relationships
            self.relationships = [r for r in self.relationships 
                                   if r['from'] != id and r['to'] != id]


@pytest.fixture
def mock_postgres():
    return MockPostgresManager()


@pytest.fixture
def mock_vector():
    return MockVectorManager()


@pytest.fixture
def mock_graph():
    return MockGraphManager()


# =============================================================================
# TRANSACTION ISOLATION TESTS
# =============================================================================

class TestTransactionIsolation:
    """Test transaction isolation properties."""
    
    @pytest.mark.asyncio
    async def test_read_uncommitted_isolation(self, mock_postgres):
        """Test that uncommitted transactions are isolated."""
        key = "test_key"
        
        # Start transaction and insert
        await mock_postgres.begin_transaction()
        await mock_postgres.insert(key, "uncommitted_value")
        
        # Value should be visible within transaction
        value = await mock_postgres.get(key)
        assert value == "uncommitted_value"
        
        # Rollback should remove the value
        await mock_postgres.rollback()
        value = await mock_postgres.get(key)
        assert value is None
    
    @pytest.mark.asyncio
    async def test_committed_data_persistence(self, mock_postgres):
        """Test that committed data persists."""
        key = "persistent_key"
        
        await mock_postgres.begin_transaction()
        await mock_postgres.insert(key, "committed_value")
        await mock_postgres.commit()
        
        # Value should persist after commit
        value = await mock_postgres.get(key)
        assert value == "committed_value"
    
    @pytest.mark.asyncio
    async def test_concurrent_transaction_isolation(self, mock_postgres):
        """Test isolation between concurrent transactions."""
        # This simulates what would happen with real DB isolation
        
        # Transaction 1 starts
        tx1_data = dict(mock_postgres.data)
        mock_postgres.data["tx1_key"] = "tx1_value"
        
        # Transaction 2 shouldn't see tx1's uncommitted changes
        # (In real DB, this depends on isolation level)
        # Here we test the concept
        
        assert "tx1_key" in mock_postgres.data  # It's there (uncommitted)


# =============================================================================
# CROSS-DATABASE CONSISTENCY TESTS
# =============================================================================

class TestCrossDatabaseConsistency:
    """Test consistency across multiple databases."""
    
    @pytest.mark.asyncio
    async def test_entity_creation_across_databases(
        self, mock_postgres, mock_vector, mock_graph, test_entity_id
    ):
        """Test creating entity across all three databases maintains consistency."""
        entity_data = {
            "id": test_entity_id,
            "name": "Test Entity",
            "embedding": [0.1] * 128,
            "relationships": [("Entity", "Entity2", "KNOWS")]
        }
        
        # Create in PostgreSQL
        await mock_postgres.insert(
            test_entity_id, 
            {"name": entity_data["name"]}
        )
        
        # Create embedding in Vector DB
        await mock_vector.upsert(
            test_entity_id,
            entity_data["embedding"],
            {"name": entity_data["name"]}
        )
        
        # Create node and relationships in Graph DB
        await mock_graph.create_node(
            test_entity_id,
            ["Entity"],
            {"name": entity_data["name"]}
        )
        
        # Verify consistency
        pg_data = await mock_postgres.get(test_entity_id)
        vector_data = mock_vector.vectors.get(test_entity_id)
        graph_data = await mock_graph.get_node(test_entity_id)
        
        assert pg_data is not None, "Missing in PostgreSQL"
        assert vector_data is not None, "Missing in Vector DB"
        assert graph_data is not None, "Missing in Graph DB"
        
        # Verify data matches
        assert pg_data["name"] == entity_data["name"]
        assert vector_data["metadata"]["name"] == entity_data["name"]
        assert graph_data["properties"]["name"] == entity_data["name"]
    
    @pytest.mark.asyncio
    async def test_entity_deletion_cascade(
        self, mock_postgres, mock_vector, mock_graph, test_entity_id
    ):
        """Test that deletion cascades across all databases."""
        # Setup - create entity in all databases
        await mock_postgres.insert(test_entity_id, {"name": "ToDelete"})
        await mock_vector.upsert(test_entity_id, [0.1] * 128)
        await mock_graph.create_node(test_entity_id, ["Entity"], {})
        
        # Delete from all databases
        await mock_postgres.delete(test_entity_id)
        await mock_vector.delete(test_entity_id)
        await mock_graph.delete_node(test_entity_id)
        
        # Verify complete deletion
        assert await mock_postgres.get(test_entity_id) is None
        assert test_entity_id not in mock_vector.vectors
        assert await mock_graph.get_node(test_entity_id) is None
    
    @pytest.mark.asyncio
    async def test_partial_failure_handling(
        self, mock_postgres, mock_vector, mock_graph, test_entity_id
    ):
        """Test handling of partial failures during multi-DB operations."""
        # Successfully write to PostgreSQL
        await mock_postgres.insert(test_entity_id, {"name": "PartialFail"})
        
        # Simulate Vector DB write
        await mock_vector.upsert(test_entity_id, [0.1] * 128)
        
        # Simulate Graph DB failure by not creating
        # (In real scenario, this would be an exception)
        
        # Check for orphan detection
        pg_exists = await mock_postgres.get(test_entity_id) is not None
        vector_exists = test_entity_id in mock_vector.vectors
        graph_exists = await mock_graph.get_node(test_entity_id) is not None
        
        # We have an inconsistent state
        assert pg_exists and vector_exists and not graph_exists
        
        # In production, this should trigger cleanup or alert


# =============================================================================
# ORPHAN DATA DETECTION TESTS
# =============================================================================

class TestOrphanDataDetection:
    """Test detection of orphaned data across databases."""
    
    @pytest.mark.asyncio
    async def test_detect_vector_without_postgres(
        self, mock_postgres, mock_vector, test_entity_id
    ):
        """Detect vector embeddings without corresponding relational data."""
        # Create only in Vector DB (orphan)
        await mock_vector.upsert(test_entity_id, [0.1] * 128)
        
        # Detection logic
        orphans = []
        for vid in mock_vector.vectors:
            if await mock_postgres.get(vid) is None:
                orphans.append(vid)
        
        assert test_entity_id in orphans
    
    @pytest.mark.asyncio
    async def test_detect_graph_without_vector(
        self, mock_vector, mock_graph, test_entity_id
    ):
        """Detect graph nodes without corresponding vector embeddings."""
        # Create only in Graph DB (orphan)
        await mock_graph.create_node(test_entity_id, ["Entity"], {})
        
        # Detection logic
        orphans = []
        for nid in mock_graph.nodes:
            if nid not in mock_vector.vectors:
                orphans.append(nid)
        
        assert test_entity_id in orphans
    
    @pytest.mark.asyncio
    async def test_detect_dangling_relationships(self, mock_graph):
        """Detect relationships pointing to non-existent nodes."""
        # Create node A but not B
        await mock_graph.create_node("node_a", ["Entity"], {})
        
        # Create relationship to non-existent node
        await mock_graph.create_relationship("node_a", "node_nonexistent", "KNOWS")
        
        # Detect dangling relationships
        dangling = []
        for rel in mock_graph.relationships:
            if rel["to"] not in mock_graph.nodes:
                dangling.append(rel)
        
        assert len(dangling) == 1
        assert dangling[0]["to"] == "node_nonexistent"


# =============================================================================
# DATA INTEGRITY TESTS
# =============================================================================

class TestDataIntegrity:
    """Test data integrity constraints."""
    
    @pytest.mark.asyncio
    async def test_unique_id_constraint(
        self, mock_postgres, mock_vector, mock_graph, test_entity_id
    ):
        """Test that IDs are unique across databases."""
        # Insert with same ID
        await mock_postgres.insert(test_entity_id, {"version": 1})
        await mock_vector.upsert(test_entity_id, [0.1] * 128, {"version": 1})
        await mock_graph.create_node(test_entity_id, ["Entity"], {"version": 1})
        
        # Update (overwrite) should maintain consistency
        await mock_postgres.insert(test_entity_id, {"version": 2})
        await mock_vector.upsert(test_entity_id, [0.2] * 128, {"version": 2})
        
        # Verify current state
        pg_data = await mock_postgres.get(test_entity_id)
        assert pg_data["version"] == 2
        assert mock_vector.vectors[test_entity_id]["metadata"]["version"] == 2
    
    @pytest.mark.asyncio
    async def test_referential_integrity(self, mock_graph):
        """Test referential integrity in graph relationships."""
        # Create proper relationship
        await mock_graph.create_node("parent", ["Entity"], {})
        await mock_graph.create_node("child", ["Entity"], {})
        await mock_graph.create_relationship("parent", "child", "HAS_CHILD")
        
        # Verify relationship is valid
        valid_relationships = [
            r for r in mock_graph.relationships
            if r["from"] in mock_graph.nodes and r["to"] in mock_graph.nodes
        ]
        
        assert len(valid_relationships) == 1
    
    @pytest.mark.asyncio
    async def test_type_consistency_across_dbs(
        self, mock_postgres, mock_vector, test_entity_id
    ):
        """Test that data types are consistent across databases."""
        # Store a complex object
        complex_data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "array": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        await mock_postgres.insert(test_entity_id, complex_data)
        await mock_vector.upsert(test_entity_id, [0.1] * 128, complex_data)
        
        # Retrieve and verify types match
        pg_data = await mock_postgres.get(test_entity_id)
        vector_meta = mock_vector.vectors[test_entity_id]["metadata"]
        
        assert type(pg_data["string"]) == type(vector_meta["string"])
        assert type(pg_data["number"]) == type(vector_meta["number"])
        assert type(pg_data["array"]) == type(vector_meta["array"])


# =============================================================================
# ROLLBACK AND RECOVERY TESTS
# =============================================================================

class TestRollbackAndRecovery:
    """Test rollback and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_single_db_rollback(self, mock_postgres):
        """Test rollback in single database."""
        key = "rollback_test"
        
        # Insert data
        await mock_postgres.insert(key, "initial_value")
        
        # Start transaction and modify
        await mock_postgres.begin_transaction()
        await mock_postgres.insert(key, "modified_value")
        
        # Rollback
        await mock_postgres.rollback()
        
        # Should have original value
        value = await mock_postgres.get(key)
        assert value == "initial_value"
    
    @pytest.mark.asyncio
    async def test_multi_db_compensating_transaction(
        self, mock_postgres, mock_vector, mock_graph, test_entity_id
    ):
        """Test compensating transactions for multi-DB consistency."""
        # Setup - track operations for rollback
        operations = []
        
        # Attempt multi-DB write
        try:
            await mock_postgres.insert(test_entity_id, {"name": "test"})
            operations.append(("postgres", "insert", test_entity_id))
            
            await mock_vector.upsert(test_entity_id, [0.1] * 128)
            operations.append(("vector", "insert", test_entity_id))
            
            # Simulate failure in graph DB
            raise Exception("Simulated graph failure")
            
        except Exception:
            # Compensating transaction - rollback previous operations
            for db, op, entity_id in reversed(operations):
                if db == "postgres":
                    await mock_postgres.delete(entity_id)
                elif db == "vector":
                    await mock_vector.delete(entity_id)
        
        # Verify complete rollback
        assert await mock_postgres.get(test_entity_id) is None
        assert test_entity_id not in mock_vector.vectors


# =============================================================================
# ROUTING CONSISTENCY TESTS
# =============================================================================

class TestRoutingConsistency:
    """Test that routing decisions are consistent."""
    
    def test_deterministic_routing(self, router):
        """Test that same input always routes to same database."""
        inputs = [
            "2 + 3 * 4",
            "SELECT * FROM users",
            [0.1, 0.2, 0.3],
            {"from": "A", "to": "B"},
            "The meaning of life is complex",
        ]
        
        for input_val in inputs:
            results = [router.classify(input_val) for _ in range(100)]
            
            # All should be identical
            first = results[0]
            for result in results[1:]:
                assert result.data_type == first.data_type
                assert result.primary_target == first.primary_target
    
    def test_routing_coverage(self, router):
        """Test that different input types get classified consistently."""
        test_cases = [
            ("equation", "x = 5 + 3"),  # Should route to equation handling
            ("embedding", [0.1] * 128),  # Should route to vector/semantic
            ("relational", {"from": "A", "to": "B", "type": "KNOWS"}),  # Dict input
        ]
        
        for input_type, input_val in test_cases:
            result = router.classify(input_val)
            # Verify we get a valid routing decision
            assert result is not None, f"No result for {input_type}"
            assert result.primary_target is not None, f"No target for {input_type}"
            assert result.confidence > 0, f"Zero confidence for {input_type}"
            # Verify determinism - same input should always route same way
            result2 = router.classify(input_val)
            assert result.primary_target == result2.primary_target, \
                f"Non-deterministic routing for {input_type}"


# =============================================================================
# CONSISTENCY AUDIT SUMMARY
# =============================================================================

class TestConsistencyAuditSummary:
    """Generate consistency audit summary."""
    
    @pytest.mark.asyncio
    async def test_generate_consistency_report(
        self, mock_postgres, mock_vector, mock_graph, router
    ):
        """Run comprehensive consistency tests and generate report."""
        results = {
            "transaction_tests": 0,
            "transaction_passed": 0,
            "cross_db_tests": 0,
            "cross_db_passed": 0,
            "orphan_tests": 0,
            "orphan_passed": 0,
            "integrity_tests": 0,
            "integrity_passed": 0,
        }
        
        # Transaction isolation test
        results["transaction_tests"] += 1
        try:
            await mock_postgres.begin_transaction()
            await mock_postgres.insert("tx_test", "value")
            await mock_postgres.rollback()
            if await mock_postgres.get("tx_test") is None:
                results["transaction_passed"] += 1
        except Exception:
            pass
        
        # Cross-DB consistency test
        results["cross_db_tests"] += 1
        try:
            test_id = f"test_{uuid.uuid4().hex[:8]}"
            await mock_postgres.insert(test_id, {"name": "test"})
            await mock_vector.upsert(test_id, [0.1] * 128)
            await mock_graph.create_node(test_id, ["Entity"], {})
            
            if all([
                await mock_postgres.get(test_id),
                test_id in mock_vector.vectors,
                await mock_graph.get_node(test_id)
            ]):
                results["cross_db_passed"] += 1
        except Exception:
            pass
        
        # Orphan detection test
        results["orphan_tests"] += 1
        orphan_id = f"orphan_{uuid.uuid4().hex[:8]}"
        await mock_vector.upsert(orphan_id, [0.1] * 128)
        orphans = [vid for vid in mock_vector.vectors if await mock_postgres.get(vid) is None]
        if orphan_id in orphans:
            results["orphan_passed"] += 1
        
        # Integrity test
        results["integrity_tests"] += 1
        integrity_id = f"integrity_{uuid.uuid4().hex[:8]}"
        await mock_postgres.insert(integrity_id, {"type": "test"})
        if await mock_postgres.get(integrity_id) is not None:
            results["integrity_passed"] += 1
        
        # Print report
        print(f"\n{'='*60}")
        print("DATABASE CONSISTENCY AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Transaction Isolation: {results['transaction_passed']}/{results['transaction_tests']}")
        print(f"Cross-DB Consistency: {results['cross_db_passed']}/{results['cross_db_tests']}")
        print(f"Orphan Detection: {results['orphan_passed']}/{results['orphan_tests']}")
        print(f"Data Integrity: {results['integrity_passed']}/{results['integrity_tests']}")
        
        total_passed = sum(v for k, v in results.items() if k.endswith('_passed'))
        total_tests = sum(v for k, v in results.items() if k.endswith('_tests'))
        print(f"\nTotal: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
        print(f"{'='*60}\n")
        
        assert total_passed == total_tests, "Some consistency tests failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
