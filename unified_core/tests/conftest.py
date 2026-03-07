"""
pytest configuration for Unified Core tests
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Add unified_core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_embedding():
    """Sample 1536-dim embedding vector."""
    import random
    return [random.random() for _ in range(1536)]


@pytest.fixture
def sample_code():
    """Sample Python code for testing."""
    return '''
def calculate_factorial(n: int) -> int:
    """Calculate factorial of n recursively."""
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)


def test_factorial():
    assert calculate_factorial(5) == 120
    assert calculate_factorial(0) == 1
'''


@pytest.fixture
def dangerous_code():
    """Dangerous Python code for security testing."""
    return '''
import pickle
import subprocess

data = pickle.load(open("data.pkl", "rb"))
subprocess.run(user_input, shell=True)
result = eval(request.get("expression"))
'''
