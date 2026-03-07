import pytest
from unittest.mock import patch, MagicMock
from noogh_unified_system.src.unified_core.evolution.ledger import Ledger, ProposalStatus

@pytest.fixture
def ledger():
    return Ledger()

def test_record_canary_result_happy_path(ledger):
    proposal_id = "test_proposal"
    result = "Test Result"
    
    with patch.object(ledger, "_write_entry") as mock_write_entry:
        ledger.record_canary_result(proposal_id, True, result)
        
        assert ledger.proposals[proposal_id].canary_result == result
        assert ledger.proposals[proposal_id].status == ProposalStatus.CANARY
        assert mock_write_entry.call_args_list == [
            call("canary_success", {"proposal_id": proposal_id, "result": result}),
            call("log_info", f"🐤 CANARY SUCCESS: {proposal_id}")
        ]

def test_record_canary_result_failure(ledger):
    proposal_id = "test_proposal"
    result = "Test Result"
    
    with patch.object(ledger, "_write_entry") as mock_write_entry:
        ledger.record_canary_result(proposal_id, False, result)
        
        assert ledger.proposals[proposal_id].canary_result == result
        assert ledger.proposals[proposal_id].status == ProposalStatus.FAILED
        assert len(ledger.failures_24h) == 1
        assert mock_write_entry.call_args_list == [
            call("canary_failed", {"proposal_id": proposal_id, "result": result}),
            call("log_warning", f"🐤 CANARY FAILED: {proposal_id}")
        ]

def test_record_canary_result_missing_proposal(ledger):
    proposal_id = "nonexistent_proposal"
    
    with patch.object(ledger, "_write_entry") as mock_write_entry:
        ledger.record_canary_result(proposal_id, True)
        
        assert mock_write_entry.call_args_list == []

def test_record_canary_result_empty_string(ledger):
    proposal_id = "test_proposal"
    result = ""
    
    with patch.object(ledger, "_write_entry") as mock_write_entry:
        ledger.record_canary_result(proposal_id, True, result)
        
        assert ledger.proposals[proposal_id].canary_result == result
        assert ledger.proposals[proposal_id].status == ProposalStatus.CANARY
        assert mock_write_entry.call_args_list == [
            call("canary_success", {"proposal_id": proposal_id, "result": result}),
            call("log_info", f"🐤 CANARY SUCCESS: {proposal_id}")
        ]

def test_record_canary_result_none_status(ledger):
    proposal_id = "test_proposal"
    
    with patch.object(ledger, "_write_entry") as mock_write_entry:
        ledger.record_canary_result(proposal_id, True)
        
        assert ledger.proposals[proposal_id].canary_result == ""
        assert ledger.proposals[proposal_id].status == ProposalStatus.CANARY
        assert mock_write_entry.call_args_list == [
            call("canary_success", {"proposal_id": proposal_id, "result": ""}),
            call("log_info", f"🐤 CANARY SUCCESS: {proposal_id}")
        ]

def test_record_canary_result_check_kill_switch(ledger):
    proposal_id = "test_proposal"
    
    with patch.object(ledger, "_write_entry") as mock_write_entry:
        with patch.object(ledger, "_check_kill_switch") as mock_check_kill_switch:
            ledger.record_canary_result(proposal_id, False)
            
            assert len(ledger.failures_24h) == 1
            assert mock_check_kill_switch.call_count == 1
            assert mock_write_entry.call_args_list == [
                call("canary_failed", {"proposal_id": proposal_id, "result": ""}),
                call("log_warning", f"🐤 CANARY FAILED: {proposal_id}")
            ]