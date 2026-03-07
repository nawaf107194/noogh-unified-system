import pytest

class MirrorShield:
    def __init__(self):
        self.primary_db = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
        self.evolution_ledger = "/home/noogh/.noogh/evolution/evolution_ledger.jsonl"
        self.amla_logs = "/home/noogh/projects/noogh_unified_system/src/data/amla_audit.jsonl"
        self.project_root = "/home/noogh/projects/noogh_unified_system"
        
        # Defined Hierarchy
        self.targets = {
            "L2_HOT_MIRROR": "/media/noogh/New Volume/noogh_hot_backup",
            "L3_VAULT": "/media/noogh/NOOGH_BACKUP/archives",
            "L4_DEEP_SLEEP": "/media/noogh/TOSHIBA EXT/noogh_deep_storage"
        }

def test_mirror_shield_happy_path():
    mirror_shield = MirrorShield()
    assert mirror_shield.primary_db == "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
    assert mirror_shield.evolution_ledger == "/home/noogh/.noogh/evolution/evolution_ledger.jsonl"
    assert mirror_shield.amla_logs == "/home/noogh/projects/noogh_unified_system/src/data/amla_audit.jsonl"
    assert mirror_shield.project_root == "/home/noogh/projects/noogh_unified_system"
    assert mirror_shield.targets == {
        "L2_HOT_MIRROR": "/media/noogh/New Volume/noogh_hot_backup",
        "L3_VAULT": "/media/noogh/NOOGH_BACKUP/archives",
        "L4_DEEP_SLEEP": "/media/noogh/TOSHIBA EXT/noogh_deep_storage"
    }

def test_mirror_shield_empty_values():
    mirror_shield = MirrorShield()
    assert mirror_shield.primary_db != ""
    assert mirror_shield.evolution_ledger != ""
    assert mirror_shield.amla_logs != ""
    assert mirror_shield.project_root != ""

def test_mirror_shield_none_values():
    mirror_shield = MirrorShield()
    assert mirror_shield.primary_db is not None
    assert mirror_shield.evolution_ledger is not None
    assert mirror_shield.amla_logs is not None
    assert mirror_shield.project_root is not None

def test_mirror_shield_boundary_values():
    mirror_shield = MirrorShield()
    # Assuming these are paths, boundary cases might be specific to the filesystem.
    pass  # Add assertions based on actual path constraints if known.

def test_mirror_shield_invalid_inputs():
    with pytest.raises(TypeError):
        mirror_shield = MirrorShield(primary_db=123)
    
    with pytest.raises(TypeError):
        mirror_shield = MirrorShield(evolution_ledger=123)
    
    with pytest.raises(TypeError):
        mirror_shield = MirrorShield(amla_logs=123)
    
    with pytest.raises(TypeError):
        mirror_shield = MirrorShield(project_root=123)

    # Assuming targets values are not validated in the constructor