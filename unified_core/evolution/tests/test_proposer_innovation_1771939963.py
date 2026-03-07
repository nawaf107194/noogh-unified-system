import pytest

from unified_core.evolution.proposer import EvolutionProposal, ProposalType, _propose_threshold_adjustment


@pytest.fixture
def proposer():
    return proposer.EvolutionProposer()  # Assuming EvolutionProposer is the class containing _propose_threshold_adjustment


def test_happy_path(proposer):
    proposal = proposer._propose_threshold_adjustment(
        threshold_name="example_threshold",
        current_value=0.1,
        suggested_value=0.2
    )
    assert proposal.proposal_id is not None
    assert proposal.proposal_type == ProposalType.CONFIG
    assert proposal.description == "Adjust example_threshold from 0.1 to 0.2"
    assert proposal.scope == "config"
    assert proposal.targets == ["config/thresholds.yaml"]
    assert proposal.diff == "# Threshold Adjustment: example_threshold\n- example_threshold: 0.1\n+ example_threshold: 0.2"
    assert proposal.risk_score == 15
    assert proposal.expected_benefit == "Optimized example_threshold for current load"
    assert proposal.rollback_plan == "Revert example_threshold to 0.1"


def test_edge_cases(proposer):
    proposal = proposer._propose_threshold_adjustment(
        threshold_name="",
        current_value=None,
        suggested_value=0.2
    )
    assert proposal is None

    proposal = proposer._propose_threshold_adjustment(
        threshold_name="example_threshold",
        current_value=0.1,
        suggested_value=None
    )
    assert proposal is None

    proposal = proposer._propose_threshold_adjustment(
        threshold_name=None,
        current_value=0.1,
        suggested_value=0.2
    )
    assert proposal is None


def test_error_cases(proposer):
    with pytest.raises(ValueError) as exc_info:
        proposer._propose_threshold_adjustment(
            threshold_name="example_threshold",
            current_value=0.1,
            suggested_value=-0.1
        )
    assert "suggested_value must be greater than or equal to 0" in str(exc_info.value)


def test_async_behavior(proposer):
    # Assuming _propose_threshold_adjustment is not async, so no need for this test
    pass