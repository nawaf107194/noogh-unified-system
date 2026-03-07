import pytest

from unified_core.evolution.innovation_engine import InnovationEngine, ProposalStatus

class MockProposal:
    def __init__(self, description: str, status: str):
        self.description = description
        self.status = status

class MockLedger:
    def __init__(self, proposals: dict):
        self.proposals = proposals

@pytest.fixture
def innovation_engine():
    return InnovationEngine(MockLedger({}))

def test_get_promoted_titles_happy_path(innovation_engine):
    mock_proposals = {
        '1': MockProposal('[INNOVATION] Title 1', ProposalStatus.PROMOTED),
        '2': MockProposal('Title 2', ProposalStatus.APPROVED),
        '3': MockProposal('[INNOVATION] Title 3', ProposalStatus.PROMOTED)
    }
    innovation_engine.ledger.proposals = mock_proposals
    assert innovation_engine._get_promoted_titles() == ['title 1', 'title 3']

def test_get_promoted_titles_empty_ledger(innovation_engine):
    innovation_engine.ledger.proposals = {}
    assert innovation_engine._get_promoted_titles() == []

def test_get_promoted_titles_no_promoted_proposals(innovation_engine):
    mock_proposals = {
        '1': MockProposal('Title 1', ProposalStatus.APPROVED),
        '2': MockProposal('Title 2', ProposalStatus.REJECTED)
    }
    innovation_engine.ledger.proposals = mock_proposals
    assert innovation_engine._get_promoted_titles() == []

def test_get_promoted_titles_none_status(innovation_engine):
    mock_proposals = {
        '1': MockProposal('[INNOVATION] Title 1', None),
        '2': MockProposal('Title 2', ProposalStatus.PROMOTED)
    }
    innovation_engine.ledger.proposals = mock_proposals
    assert innovation_engine._get_promoted_titles() == ['title 2']

def test_get_promoted_titles_invalid_status(innovation_engine):
    mock_proposals = {
        '1': MockProposal('[INNOVATION] Title 1', 'INVALID_STATUS'),
        '2': MockProposal('Title 2', ProposalStatus.PROMOTED)
    }
    innovation_engine.ledger.proposals = mock_proposals
    assert innovation_engine._get_promoted_titles() == ['title 2']