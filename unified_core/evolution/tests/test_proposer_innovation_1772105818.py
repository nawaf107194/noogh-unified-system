import pytest

from unified_core.evolution.proposer import EvolutionProposal, _propose_interval_adjustment

@pytest.mark.parametrize("current_value, suggested_value, expected_description", [
    (1.0, 2.0, "Adjust interval from 1.0 to 2.0"),
    (0.5, 0.75, "Adjust interval from 0.5 to 0.75"),
    (100, 50, "Adjust interval from 100 to 50")
])
def test_propose_interval_adjustment_happy_path(current_value, suggested_value, expected_description):
    proposal = _propose_interval_adjustment(current_value, suggested_value)
    assert isinstance(proposal, EvolutionProposal)
    assert proposal.proposal_type == ProposalType.CONFIG
    assert proposal.description == expected_description
    assert proposal.scope == "config"
    assert proposal.targets == ["config/intervals.yaml"]
    assert proposal.diff.startswith("# Interval Adjustment\n- current: ")
    assert proposal.diff.endswith("\n+ suggested: " + str(suggested_value))
    assert proposal.risk_score == 10
    assert proposal.expected_benefit == "Improved cycle timing"
    assert proposal.rollback_plan == f"Revert to {current_value}"
    assert proposal.rationale == "Optimizing based on observed performance"

def test_propose_interval_adjustment_edge_cases():
    # Empty inputs
    proposal = _propose_interval_adjustment("", "")
    assert proposal is None

    # None inputs
    proposal = _propose_interval_adjustment(None, None)
    assert proposal is None

    # Boundary values
    proposal = _propose_interval_adjustment(0.0, 1.0e-9)
    assert proposal is not None

@pytest.mark.parametrize("current_value, suggested_value", [
    ("invalid", "value"),
    (None, 2.0),
    (1.0, "suggested")
])
def test_propose_interval_adjustment_error_cases(current_value, suggested_value):
    proposal = _propose_interval_adjustment(current_value, suggested_value)
    assert proposal is None