import pytest

from unified_core.evolution.ledger import Ledger

class TestLedgerIsSafeMode:

    @pytest.fixture
    def ledger(self):
        return Ledger()

    @pytest.mark.asyncio
    async def test_happy_path(self, ledger):
        ledger.safe_mode = False
        assert not await ledger.is_safe_mode()
        
        ledger.safe_mode = True
        assert await ledger.is_safe_mode()

    @pytest.mark.asyncio
    async def test_edge_case_none_safe_mode(self, ledger):
        ledger.safe_mode = None
        assert not await ledger.is_safe_mode()

    @pytest.mark.asyncio
    async def test_edge_case_empty_safe_mode(self, ledger):
        ledger.safe_mode = ""
        assert not await ledger.is_safe_mode()

    @pytest.mark.asyncio
    async def test_edge_case_boundary_true(self, ledger):
        ledger.safe_mode = True
        assert await ledger.is_safe_mode()

    @pytest.mark.asyncio
    async def test_error_case_invalid_input(self, ledger):
        with pytest.raises(TypeError):
            # Create a Ledger instance with an invalid input to trigger the error
            ledger_with_invalid_input = Ledger(safe_mode="not a boolean")