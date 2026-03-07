import pytest

from unified_core.config.ports import Ports

@pytest.fixture
def ports():
    return Ports(
        NEURAL_ENGINE=8081,
        GATEWAY=8082,
        REDIS=6379,
        POSTGRES=5432,
        NEO4J=7687,
        MILVUS=19530,
        PROMETHEUS=9090,
        GRAFANA=3000,
    )

def test_to_dict_happy_path(ports):
    result = ports.to_dict()
    assert isinstance(result, dict)
    assert result == {
        "neural_engine": 8081,
        "gateway": 8082,
        "redis": 6379,
        "postgres": 5432,
        "neo4j": 7687,
        "milvus": 19530,
        "prometheus": 9090,
        "grafana": 3000,
    }

def test_to_dict_empty():
    empty_ports = Ports()
    result = empty_ports.to_dict()
    assert isinstance(result, dict)
    assert result == {}

def test_to_dict_none_values():
    none_ports = Ports(
        NEURAL_ENGINE=None,
        GATEWAY=None,
        REDIS=None,
        POSTGRES=None,
        NEO4J=None,
        MILVUS=None,
        PROMETHEUS=None,
        GRAFANA=None,
    )
    result = none_ports.to_dict()
    assert isinstance(result, dict)
    assert result == {
        "neural_engine": None,
        "gateway": None,
        "redis": None,
        "postgres": None,
        "neo4j": None,
        "milvus": None,
        "prometheus": None,
        "grafana": None,
    }

def test_to_dict_boundary_values():
    boundary_ports = Ports(
        NEURAL_ENGINE=1023,  # Lowest possible non-reserved port
        GATEWAY=65535,       # Highest possible non-reserved port
        REDIS=1024,          # Non-standard Redis port
        POSTGRES=5432,         # Standard PostgreSQL port
        NEO4J=7474,          # Non-standard Neo4j port
        MILVUS=19530,        # Default Milvus port
        PROMETHEUS=9000,     # Non-standard Prometheus port
        GRAFANA=3001,         # Non-standard Grafana port
    )
    result = boundary_ports.to_dict()
    assert isinstance(result, dict)
    assert result == {
        "neural_engine": 1023,
        "gateway": 65535,
        "redis": 1024,
        "postgres": 5432,
        "neo4j": 7474,
        "milvus": 19530,
        "prometheus": 9000,
        "grafana": 3001,
    }

# Since the function does not handle async behavior, no need for additional tests in this case.