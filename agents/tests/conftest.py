"""
pytest configuration for NOOGH agents tests.
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_market_data():
    """Sample market data for testing."""
    return {
        "symbol": "BTCUSDT",
        "price": 65000.0,
        "volume": 1234567.89,
        "funding_rate": 0.0001,
        "timestamp": 1741647600,
    }


@pytest.fixture
def mock_trading_config():
    """Sample trading config for testing."""
    return {
        "mode": "PAPER",
        "max_position_size": 0.01,
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.04,
        "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    }
