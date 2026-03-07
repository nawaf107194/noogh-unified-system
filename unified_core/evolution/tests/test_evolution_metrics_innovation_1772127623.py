import pytest

from unified_core.evolution.evolution_metrics import EvolutionMetrics

class TestEvolutionMetrics:

    @pytest.fixture
    def metrics(self):
        return EvolutionMetrics()

    @pytest.mark.asyncio
    async def test_inc_happy_path(self, metrics):
        await metrics.inc('test_counter', 5)
        assert metrics._counters['test_counter'] == 5

    @pytest.mark.asyncio
    async def test_inc_default_value(self, metrics):
        await metrics.inc('test_counter')
        assert metrics._counters['test_counter'] == 1

    @pytest.mark.asyncio
    async def test_inc_multiple_calls(self, metrics):
        await metrics.inc('test_counter', 3)
        await metrics.inc('test_counter', 2)
        assert metrics._counters['test_counter'] == 5

    @pytest.mark.asyncio
    async def test_inc_with_zero_value(self, metrics):
        await metrics.inc('test_counter', 0)
        assert metrics._counters['test_counter'] == 0

    @pytest.mark.asyncio
    async def test_inc_with_negative_value(self, metrics):
        await metrics.inc('test_counter', -2)
        assert metrics._counters['test_counter'] == -2

    @pytest.mark.asyncio
    async def test_inc_empty_name(self, metrics):
        with pytest.raises(ValueError) as exc_info:
            await metrics.inc('')
        assert 'Counter name cannot be empty' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_inc_none_name(self, metrics):
        with pytest.raises(ValueError) as exc_info:
            await metrics.inc(None)
        assert 'Counter name cannot be None' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_inc_non_string_name(self, metrics):
        with pytest.raises(TypeError) as exc_info:
            await metrics.inc(123)
        assert 'Counter name must be a string' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_inc_non_integer_value(self, metrics):
        with pytest.raises(TypeError) as exc_info:
            await metrics.inc('test_counter', 1.5)
        assert 'Value must be an integer' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_inc_negative_boundary_value(self, metrics):
        with pytest.raises(ValueError) as exc_info:
            await metrics.inc('test_counter', -3000000001)
        assert 'Value cannot be below -2**63' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_inc_positive_boundary_value(self, metrics):
        with pytest.raises(ValueError) as exc_info:
            await metrics.inc('test_counter', 3000000001)
        assert 'Value cannot be above 2**63' in str(exc_info.value)