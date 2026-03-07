import pytest

from unified_core.intelligence.constraints import _violates, Proposal

@pytest.fixture
def proposal():
    return Proposal()

class Test_violates:
    def test_happy_path_max_constraint(self, proposal):
        proposal.set_value('max_amount', 100)
        assert _violates(proposal, 'max_amount', 50) is False
        assert _violates(proposal, 'max_amount', 150) is True

    def test_happy_path_min_constraint(self, proposal):
        proposal.set_value('min_age', 21)
        assert _violates(proposal, 'min_age', 30) is False
        assert _violates(proposal, 'min_age', 20) is True

    def test_edge_case_missing_constraint(self, proposal):
        assert _violates(proposal, 'max_amount', 50) is False
        assert _violates(proposal, 'min_age', 30) is False

    def test_edge_case_none_value(self, proposal):
        proposal.set_value('max_amount', None)
        assert _violates(proposal, 'max_amount', 50) is False

    def test_edge_case_empty_limit(self, proposal):
        proposal.set_value('max_amount', 100)
        assert _violates(proposal, 'max_amount', None) is False
        assert _violates(proposal, 'max_amount', '') is False

    def test_edge_case_boundary_max_constraint(self, proposal):
        proposal.set_value('max_amount', 100)
        assert _violates(proposal, 'max_amount', 100) is True

    def test_edge_case_boundary_min_constraint(self, proposal):
        proposal.set_value('min_age', 21)
        assert _violates(proposal, 'min_age', 21) is False

    # Error cases are not applicable as the function does not explicitly raise exceptions