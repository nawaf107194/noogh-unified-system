"""
Tests for DataRouter classification and query routing
"""
import pytest
import asyncio
from unified_core.db.router import DataRouter, DataType, RoutingStrategy, RoutingDecision


class TestDataTypeClassification:
    """Test input classification logic."""
    
    @pytest.fixture
    def router(self):
        return DataRouter()
    
    def test_classify_equation_pure_math(self, router):
        """Pure mathematical expressions → EQUATION."""
        result = router.classify("2 + 3 * 4")
        assert result.data_type == DataType.EQUATION
        assert result.primary_target == "postgres"
    
    def test_classify_equation_with_assignment(self, router):
        """Variable assignment → EQUATION."""
        result = router.classify("x = 5 + 3")
        assert result.data_type == DataType.EQUATION
        assert result.primary_target == "postgres"
    
    def test_classify_equation_functions(self, router):
        """Math functions → EQUATION."""
        for expr in ["sin(x)", "cos(45)", "log(100)", "sqrt(16)"]:
            result = router.classify(expr)
            assert result.data_type == DataType.EQUATION
    
    def test_classify_logical_patterns(self, router):
        """Logical expressions → LOGICAL."""
        cases = [
            "if x then y",
            "A and B or C",
            "not true implies false",
            "forall x exists y",
        ]
        for expr in cases:
            result = router.classify(expr)
            assert result.data_type == DataType.LOGICAL
            assert result.primary_target == "postgres"
    
    def test_classify_relational_patterns(self, router):
        """Relationship expressions → RELATIONAL."""
        cases = [
            "A is a B",
            "X causes Y",
            "Node connects to Node2",
            "Parent has a child",
        ]
        for expr in cases:
            result = router.classify(expr)
            assert result.data_type == DataType.RELATIONAL
            assert result.primary_target == "graph"
    
    def test_classify_semantic_natural_language(self, router):
        """Natural language → SEMANTIC."""
        text = "What is the meaning of life? This is a philosophical question that many have pondered."
        result = router.classify(text)
        assert result.data_type == DataType.SEMANTIC
        assert result.primary_target == "vector"
    
    def test_classify_vector_list(self, router):
        """Numeric list → SEMANTIC (embedding)."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = router.classify(embedding)
        assert result.data_type == DataType.SEMANTIC
        assert result.primary_target == "vector"
        assert result.confidence >= 0.9
    
    def test_classify_dict_with_embedding(self, router):
        """Dict with embedding key → SEMANTIC."""
        data = {"embedding": [0.1, 0.2], "text": "hello"}
        result = router.classify(data)
        assert result.data_type == DataType.SEMANTIC
        assert result.primary_target == "vector"
    
    def test_classify_dict_relationship(self, router):
        """Dict with from/to → RELATIONAL."""
        data = {"from": "A", "to": "B", "relationship": "KNOWS"}
        result = router.classify(data)
        assert result.data_type == DataType.RELATIONAL
        assert result.primary_target == "graph"
    
    def test_classify_dict_expression(self, router):
        """Dict with expression → EQUATION."""
        data = {"expression": "2 + 2", "result": 4}
        result = router.classify(data)
        assert result.data_type == DataType.EQUATION
        assert result.primary_target == "postgres"


class TestCustomRules:
    """Test custom routing rules."""
    
    def test_custom_rule_override(self):
        """Custom rule overrides default classification."""
        router = DataRouter()
        
        # Add custom rule
        def force_graph(text: str):
            if "FORCE_GRAPH" in text:
                return RoutingDecision(
                    data_type=DataType.RELATIONAL,
                    primary_target="graph",
                    confidence=1.0,
                    reasoning="Custom rule"
                )
            return None
        
        router.add_custom_rule(force_graph)
        
        # Test custom rule triggers
        result = router.classify("FORCE_GRAPH: 2 + 2")
        assert result.primary_target == "graph"
        
        # Test fallback to default
        result = router.classify("2 + 2")
        assert result.primary_target == "postgres"


class TestCaching:
    """Test classification caching."""
    
    def test_cache_hit(self):
        """Same input returns cached result."""
        router = DataRouter()
        
        # First call
        result1 = router.classify("test input")
        
        # Second call - should hit cache
        result2 = router.classify("test input")
        
        assert result1.data_type == result2.data_type
        assert result1.primary_target == result2.primary_target


class TestRouterInitialization:
    """Test router with database managers."""
    
    @pytest.mark.asyncio
    async def test_initialize_empty(self):
        """Router works without databases (memory fallback)."""
        router = DataRouter()
        results = await router.initialize_all()
        assert results == {}
    
    @pytest.mark.asyncio
    async def test_query_without_dbs(self):
        """Query fails gracefully without databases."""
        router = DataRouter()
        result = await router.query("test")
        assert not result.success or len(result.sources) == 0
