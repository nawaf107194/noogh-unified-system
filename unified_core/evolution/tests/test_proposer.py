import pytest
from unified_core.evolution.proposer import Proposer
import time
import uuid

class TestProposer:
    def setup_method(self):
        self.proposer = Proposer()

    @pytest.mark.asyncio
    async def test_happy_path(self):
        """Test normal inputs."""
        proposal_id = await self.proposer._generate_proposal_id()
        assert isinstance(proposal_id, str)
        assert len(proposal_id) == 24
        assert proposal_id.startswith('prop_')
        assert proposal_id[5:].isdigit()
        assert len(proposal_id[13:]) == 8
        assert all(x in '0123456789abcdef' for x in proposal_id[-8:])

    @pytest.mark.asyncio
    async def test_edge_case_empty_input(self):
        """Test edge case with empty input."""
        with pytest.raises(ValueError) as exc_info:
            await self.proposer._generate_proposal_id(None)
        assert "Empty input not allowed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_edge_case_none_input(self):
        """Test edge case with None input."""
        with pytest.raises(ValueError) as exc_info:
            await self.proposer._generate_proposal_id(None)
        assert "None input not allowed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_case_invalid_input(self):
        """Test error case with invalid input type."""
        with pytest.raises(TypeError) as exc_info:
            await self.proposer._generate_proposal_id([1, 2, 3])
        assert "Invalid input type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_behavior(self):
        """Test async behavior."""
        proposal_ids = set()
        for _ in range(10):
            proposal_ids.add(await self.proposer._generate_proposal_id())
        assert len(proposal_ids) == 10  # Ensure all IDs are unique

    @pytest.mark.asyncio
    async def test_timestamp_boundary(self):
        """Test boundary condition for timestamp."""
        current_time = int(time.time())
        await self.proposer._generate_proposal_id()
        next_time = int(time.time())
        assert next_time > current_time  # Ensure timestamp increments correctly