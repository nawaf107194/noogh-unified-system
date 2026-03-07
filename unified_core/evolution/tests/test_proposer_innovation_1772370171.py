import pytest

from unified_core.evolution.proposer import get_patch_proposer, PatchProposer

_proposer_instance = None  # Reset global variable for testing

def teardown_module():
    """Reset global variable after tests."""
    global _proposer_instance
    _proposer_instance = None

@pytest.fixture(scope="module")
def patch_proposer_instance():
    return PatchProposer()

class TestGetPatchProposer:

    def test_happy_path(self, patch_proposer_instance):
        """Test the happy path with normal inputs."""
        global _proposer_instance
        _proposer_instance = patch_proposer_instance
        
        result = get_patch_proposer()
        
        assert result is not None
        assert isinstance(result, PatchProposer)
    
    def test_no_existing_instance(self, patch_proposer_instance):
        """Test when no existing instance exists."""
        global _proposer_instance
        _proposer_instance = None
        
        result = get_patch_proposer()
        
        assert result is not None
        assert isinstance(result, PatchProposer)
    
    def test_existing_instance(self, patch_proposer_instance):
        """Test when an existing instance already exists."""
        global _proposer_instance
        _proposer_instance = patch_proposer_instance
        
        first_call_result = get_patch_proposer()
        second_call_result = get_patch_proposer()
        
        assert first_call_result is not None
        assert isinstance(first_call_result, PatchProposer)
        assert first_call_result == second_call_result