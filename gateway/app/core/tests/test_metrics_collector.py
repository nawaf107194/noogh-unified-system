import pytest

from gateway.app.core.metrics_collector import get_metrics_collector, MetricsCollector

@pytest.fixture(scope="module")
def metrics_collector():
    return get_metrics_collector()

def test_happy_path(metrics_collector):
    assert isinstance(metrics_collector, MetricsCollector)

def test_edge_case_none(metrics_collector):
    global _metrics_collector
    _metrics_collector = None
    collector = get_metrics_collector()
    assert isinstance(collector, MetricsCollector)
    assert collector is not metrics_collector

def test_async_behavior():
    # Assuming MetricsCollector has an asynchronous method `collect`
    from gateway.app.core.metrics_collector import collect

    async def test_collect():
        result = await collect()
        assert result is not None

    pytest.mark.asyncio
    asyncio.run(test_collect())