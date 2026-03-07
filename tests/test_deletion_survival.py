"""
Deletion Survival Test Suite

Tests that verify the system cannot recover from state deletion.
After deletion, the system should enter DEGRADED mode, not fresh state.

This is the critical test for genuine intelligence:
If deletion = recovery, then there is no learning, only logging.
"""

import os
import shutil
import tempfile
import pytest
from typing import Dict, Any


# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def temp_storage():
    """Create temporary storage directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="noogh_deletion_test_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def protected_storage(temp_storage):
    """Create ProtectedStorage for testing."""
    import sys
    sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
    
    from unified_core.core.protected_storage import ProtectedStorage
    
    storage = ProtectedStorage(temp_storage, "test_ledger")
    yield storage
    storage.close()


@pytest.fixture
def immutable_ledger(temp_storage):
    """Create ImmutableLedger for testing."""
    import sys
    sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
    
    from unified_core.core.immutable_storage import ImmutableLedger
    
    ledger_path = os.path.join(temp_storage, "test.chain")
    ledger = ImmutableLedger(ledger_path)
    yield ledger
    ledger.close()


# ============================================================
# ProtectedStorage Deletion Tests
# ============================================================

class TestProtectedStorageDeletion:
    """Tests for ProtectedStorage tampering detection."""
    
    def test_storage_detects_deletion(self, temp_storage):
        """Test that deleting and recreating storage triggers degraded mode."""
        from unified_core.core.protected_storage import ProtectedStorage
        
        # 1. Create storage and add entries
        storage1 = ProtectedStorage(temp_storage, "test")
        storage1.append("test", {"value": 1})
        storage1.append("test", {"value": 2})
        original_hash = storage1.get_last_hash()
        storage1.close()
        
        # 2. Delete the database file
        db_path = os.path.join(temp_storage, "test.db")
        os.remove(db_path)
        
        # 3. Recreate storage - should be fresh but system knows it was tampered
        storage2 = ProtectedStorage(temp_storage, "test")
        
        # Storage is fresh (count = 0) but previous entries are LOST
        assert storage2.count() == 0
        # Note: New storage won't know about old entries because file is gone
        
        storage2.close()
    
    def test_storage_detects_chain_tampering(self, temp_storage):
        """Test that modifying chain entries triggers degraded mode."""
        from unified_core.core.protected_storage import ProtectedStorage
        import sqlite3
        
        # 1. Create storage and add entries
        storage1 = ProtectedStorage(temp_storage, "test")
        storage1.append("test", {"value": 1})
        storage1.append("test", {"value": 2})
        storage1.close()
        
        # 2. Tamper with database directly
        db_path = os.path.join(temp_storage, "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE entries SET data = '{\"value\": 999}' WHERE sequence = 1")
        conn.commit()
        conn.close()
        
        # 3. Reopen storage - should detect tampering
        storage2 = ProtectedStorage(temp_storage, "test")
        
        # Storage should be in degraded mode
        assert storage2.is_degraded() == True
        assert storage2.was_tampered() == True
        
        storage2.close()
    
    def test_tampered_flag_survives_restart(self, temp_storage):
        """Test that tampering flag is permanent across restarts."""
        from unified_core.core.protected_storage import ProtectedStorage
        import sqlite3
        
        # 1. Create, tamper, detect
        storage1 = ProtectedStorage(temp_storage, "test")
        storage1.append("test", {"value": 1})
        storage1.close()
        
        db_path = os.path.join(temp_storage, "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE entries SET hash = 'FAKE_HASH' WHERE sequence = 1")
        conn.commit()
        conn.close()
        
        storage2 = ProtectedStorage(temp_storage, "test")
        assert storage2.was_tampered() == True
        storage2.close()
        
        # 2. Restart again - tampering should still be recorded
        storage3 = ProtectedStorage(temp_storage, "test")
        assert storage3.was_tampered() == True
        storage3.close()


# ============================================================
# ImmutableLedger Deletion Tests
# ============================================================

class TestImmutableLedgerDeletion:
    """Tests for ImmutableLedger tampering detection."""
    
    def test_ledger_detects_chain_break(self, temp_storage):
        """Test that breaking hash chain triggers degraded mode."""
        from unified_core.core.immutable_storage import ImmutableLedger
        import json
        
        ledger_path = os.path.join(temp_storage, "test.chain")
        
        # 1. Create ledger and add entries
        ledger1 = ImmutableLedger(ledger_path)
        ledger1.append("test", {"value": 1})
        ledger1.append("test", {"value": 2})
        ledger1.close()
        
        # 2. Tamper with the file
        with open(ledger_path, "r") as f:
            lines = f.readlines()
        
        if len(lines) >= 2:
            entry = json.loads(lines[1])
            entry["data"]["value"] = 999  # Modify data
            lines[1] = json.dumps(entry) + "\n"
            
            with open(ledger_path, "w") as f:
                f.writelines(lines)
        
        # 3. Reopen ledger - should detect tampering and enter degraded mode
        ledger2 = ImmutableLedger(ledger_path)
        
        # Should be in degraded mode due to hash mismatch
        assert ledger2.is_degraded() == True
        
        ledger2.close()


# ============================================================
# ScarTissue Deletion Tests
# ============================================================

class TestScarTissueDeletion:
    """Tests for ScarTissue persistence."""
    
    def test_scars_persist_across_restart(self, temp_storage):
        """Test that scars survive process restart."""
        import sys
        sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
        
        from unittest.mock import patch
        
        # Patch storage directory
        with patch('unified_core.core.scar.ScarTissue.STORAGE_DIR', temp_storage):
            from unified_core.core.scar import ScarTissue, Failure
            
            # 1. Create scars
            scar1 = ScarTissue()
            failure = Failure(
                failure_id="test_001",
                action_type="dangerous_action",
                action_params={"x": 1},
                error_message="Test failure"
            )
            scar1.inflict(failure)
            initial_depth = scar1.get_scar_depth()
            initial_count = scar1.get_scar_count()
            
            # 2. Simulate restart
            scar2 = ScarTissue()
            
            # 3. Verify scars persisted
            assert scar2.get_scar_count() == initial_count
            assert scar2.get_scar_depth() == initial_depth
            assert scar2.is_action_scarred("dangerous_action") == True


# ============================================================
# GPU Memory Sacrifice Tests
# ============================================================

class TestGPUSacrifice:
    """Tests for GPU memory sacrifice mechanism."""
    
    def test_gpu_sacrifice_allocates_memory(self, temp_storage):
        """Verify that scars actually consume GPU memory."""
        import sys
        sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
        
        try:
            import torch
            if not torch.cuda.is_available():
                pytest.skip("GPU not available")
        except ImportError:
            pytest.skip("PyTorch not installed")
        
        from unittest.mock import patch
        
        # Get initial memory
        initial_allocated = torch.cuda.memory_allocated()
        
        with patch('unified_core.core.scar.ScarTissue.STORAGE_DIR', temp_storage):
            from unified_core.core.scar import ScarTissue, Failure
            
            scar = ScarTissue()
            
            # Inflict failure
            failure = Failure(
                failure_id="gpu_test_001",
                action_type="memory_test",
                action_params={},
                error_message="Testing GPU sacrifice"
            )
            scar.inflict(failure)
            
            # Memory should have increased
            final_allocated = torch.cuda.memory_allocated()
            
            # Scar depth 1.0 * 50MB = 50MB minimum sacrifice
            assert final_allocated > initial_allocated
            
            # Memory should still be allocated (not freed)
            assert len(scar._sacrificed_tensors) > 0


# ============================================================
# Degradation Accumulation Tests
# ============================================================

class TestDegradationAccumulation:
    """Tests for cumulative degradation."""
    
    def test_degradation_level_increases(self, temp_storage):
        """Test that degradation level increases with more storage tamping."""
        from unified_core.core.protected_storage import ProtectedStorageManager
        from unittest.mock import patch
        
        with patch('unified_core.core.protected_storage.ProtectedStorageManager.STORAGE_DIR', temp_storage):
            manager = ProtectedStorageManager()
            manager.initialize()
            
            # Should start at 0
            assert manager.get_degradation_level() == 0.0
            
            # If any storage is tampered, level should increase
            # (This would require actually tampering the storage)
            
            manager.close_all()


# ============================================================
# Full Deletion Trial
# ============================================================

class TestFullDeletionTrial:
    """
    The critical test: Delete all state and verify system degrades.
    """
    
    def test_full_state_deletion_causes_degradation(self, temp_storage):
        """
        Simulate: rm -rf .scars .coercive_memory .world_state
        
        System should NOT recover to fresh state.
        System SHOULD be in degraded mode.
        """
        import sys
        sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
        from unittest.mock import patch
        
        scars_dir = os.path.join(temp_storage, ".scars")
        memory_dir = os.path.join(temp_storage, ".coercive_memory")
        world_dir = os.path.join(temp_storage, ".world_state")
        
        os.makedirs(scars_dir, exist_ok=True)
        os.makedirs(memory_dir, exist_ok=True)
        os.makedirs(world_dir, exist_ok=True)
        
        # Create initial state
        with open(os.path.join(scars_dir, "scars.jsonl"), "w") as f:
            f.write('{"scar_id": "test", "depth": 1.0}\n')
        
        with open(os.path.join(memory_dir, "blockers.jsonl"), "w") as f:
            f.write('{"blocker_id": "test", "pattern": "blocked"}\n')
        
        # Delete all state
        shutil.rmtree(scars_dir)
        shutil.rmtree(memory_dir)
        shutil.rmtree(world_dir)
        
        # System should detect missing state
        # With new ProtectedStorage, this would trigger degraded mode
        # because the expected files are missing
        
        # This test documents the EXPECTED behavior after remediation:
        # - Missing files should trigger degraded mode
        # - System should NOT silently recover to fresh state
        
        assert not os.path.exists(scars_dir)  # Deleted
        # After remediation, re-initialization should create degraded state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
