import pytest

from unified_core.db.graph_db import GraphDB, Node, Relationship

@pytest.fixture
def default_graphdb():
    return GraphDB()

@pytest.fixture
def custom_graphdb():
    return GraphDB(
        uri="bolt://custom:7687",
        user="custom_user",
        password="custom_password",
        database="custom_db",
        max_connection_pool_size=10,
        use_memory_fallback=False
    )

def test_default_init(default_graphdb):
    assert default_graphdb.uri == "bolt://localhost:7687"
    assert default_graphdb.user == "neo4j"
    assert default_graphdb.password == ""
    assert default_graphdb.database == "neo4j"
    assert default_graphdb.max_pool_size == 50
    assert default_graphdb.use_memory_fallback is True
    assert default_graphdb._driver is None
    assert default_graphdb._initialized is False
    assert default_graphdb._using_memory is False
    assert default_graphdb._memory_nodes == {}
    assert default_graphdb._memory_relationships == {}
    assert default_graphdb._memory_adjacency == {}

def test_custom_init(custom_graphdb):
    assert custom_graphdb.uri == "bolt://custom:7687"
    assert custom_graphdb.user == "custom_user"
    assert custom_graphdb.password == "custom_password"
    assert custom_graphdb.database == "custom_db"
    assert custom_graphdb.max_pool_size == 10
    assert custom_graphdb.use_memory_fallback is False
    assert custom_graphdb._driver is None
    assert custom_graphdb._initialized is False
    assert custom_graphdb._using_memory is False
    assert custom_graphdb._memory_nodes == {}
    assert custom_graphdb._memory_relationships == {}
    assert custom_graphdb._memory_adjacency == {}

def test_empty_uri(custom_graphdb):
    with pytest.raises(ValueError) as exc_info:
        GraphDB(uri="")
    assert "URI cannot be empty" in str(exc_info.value)

def test_none_uri(default_graphdb):
    with pytest.raises(ValueError) as exc_info:
        GraphDB(uri=None)
    assert "URI cannot be None" in str(exc_info.value)

def test_empty_database(custom_graphdb):
    with pytest.raises(ValueError) as exc_info:
        GraphDB(database="")
    assert "Database name cannot be empty" in str(exc_info.value)

def test_none_database(default_graphdb):
    with pytest.raises(ValueError) as exc_info:
        GraphDB(database=None)
    assert "Database name cannot be None" in str(exc_info.value)

def test_max_pool_size_out_of_bounds(custom_graphdb):
    with pytest.raises(ValueError) as exc_info:
        GraphDB(max_connection_pool_size=0)
    assert "Max connection pool size must be greater than 0" in str(exc_info.value)