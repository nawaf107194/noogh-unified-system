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

# Test cases
class TestMirrorShield:

    def test_happy_path(self):
        mirror_shield = MirrorShield()
        assert mirror_shield.primary_db == "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
        assert mirror_shield.evolution_ledger == "/home/noogh/.noogh/evolution/evolution_ledger.jsonl"
        assert mirror_shield.amla_logs == "/home/noogh/projects/noogh_unified_system/src/data/amla_audit.jsonl"
        assert mirror_shield.project_root == "/home/noogh/projects/noogh_unified_system"
        assert mirror_shield.targets["L2_HOT_MIRROR"] == "/media/noogh/New Volume/noogh_hot_backup"
        assert mirror_shield.targets["L3_VAULT"] == "/media/noogh/NOOGH_BACKUP/archives"
        assert mirror_shield.targets["L4_DEEP_SLEEP"] == "/media/noogh/TOSHIBA EXT/noogh_deep_storage"

    def test_empty_targets(self):
        original_targets = MirrorShield().targets
        try:
            delattr(MirrorShield, 'targets')
            mirror_shield = MirrorShield()
            assert mirror_shield.targets == {}
        finally:
            setattr(MirrorShield, 'targets', original_targets)

    def test_none_targets(self):
        original_targets = MirrorShield().targets
        try:
            setattr(MirrorShield, 'targets', None)
            mirror_shield = MirrorShield()
            assert mirror_shield.targets is None
        finally:
            setattr(MirrorShield, 'targets', original_targets)

    def test_invalid_target_key(self):
        original_targets = MirrorShield().targets
        try:
            del mirror_shield.targets["L2_HOT_MIRROR"]
            mirror_shield = MirrorShield()
            assert "L2_HOT_MIRROR" not in mirror_shield.targets
        finally:
            setattr(MirrorShield, 'targets', original_targets)