import pytest
from typing import Dict, Any

class Scar:
    def __init__(self, scar_id: str, **kwargs):
        self.scar_id = scar_id
        for key, value in kwargs.items():
            setattr(self, key, value)

class UnifiedCore:
    def __init__(self):
        self._scars = []
    
    def _process_scar_entry(self, data: Dict[str, Any], seen_scar_ids: Dict[str, float]):
        """Deduplicate scar by timestamp and instantiate Scar object."""
        scar_id = data["scar_id"]
        created_at = data.get("created_at", 0)
        
        # Skip if we already have a newer version
        if scar_id in seen_scar_ids:
            if created_at <= seen_scar_ids[scar_id]:
                return
        
        seen_scar_ids[scar_id] = created_at
        
        scar = Scar(
            scar_id=scar_id,
            source_failure_id=data["source_failure_id"],
            actions_blocked=data["actions_blocked"],
            beliefs_falsified=data.get("beliefs_falsified", []),
            ideas_penalized=data.get("ideas_penalized", []),
            depth=data.get("depth", 1.0),
            created_at=created_at
        )
        
        # Remove old version if exists and update
        self._scars = [s for s in self._scars if s.scar_id != scar_id]
        self._scars.append(scar)

# Happy path
def test_process_scar_entry_happy_path():
    core = UnifiedCore()
    seen_scar_ids = {}
    
    data1 = {
        "scar_id": "123",
        "source_failure_id": "fail1",
        "actions_blocked": ["act1"],
        "depth": 2.0
    }
    core._process_scar_entry(data1, seen_scar_ids)
    
    assert len(core._scars) == 1
    scar = core._scars[0]
    assert scar.scar_id == "123"
    assert scar.source_failure_id == "fail1"
    assert scar.actions_blocked == ["act1"]
    assert scar.depth == 2.0
    
    data2 = {
        "scar_id": "456",
        "source_failure_id": "fail2",
        "actions_blocked": ["act2"],
        "depth": 3.0
    }
    core._process_scar_entry(data2, seen_scar_ids)
    
    assert len(core._scars) == 2

# Edge cases
def test_process_scar_entry_empty_data():
    core = UnifiedCore()
    seen_scar_ids = {}
    
    data = {}
    with pytest.raises(KeyError):
        core._process_scar_entry(data, seen_scar_ids)
    
def test_process_scar_entry_none_input():
    core = UnifiedCore()
    seen_scar_ids = {}
    
    with pytest.raises(TypeError):
        core._process_scar_entry(None, seen_scar_ids)

# Error cases (invalid inputs)
def test_process_scar_entry_invalid_created_at():
    core = UnifiedCore()
    seen_scar_ids = {}
    
    data = {
        "scar_id": "123",
        "source_failure_id": "fail1",
        "actions_blocked": ["act1"],
        "created_at": "invalid"
    }
    with pytest.raises(TypeError):
        core._process_scar_entry(data, seen_scar_ids)

# Async behavior (if applicable)
def test_process_scar_entry_async_behavior():
    # This function does not contain any async code to test
    pass