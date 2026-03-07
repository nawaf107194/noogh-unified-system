# unified_core/db/snapshot_db.py

import os
import shutil
from datetime import datetime

class SnapshotDB:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def save_snapshot(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        snapshot_path = os.path.join(self.base_dir, f"snapshot_{timestamp}.zip")
        
        # Implement logic to create a compressed backup of the entire system state
        # For simplicity, let's assume we are copying all relevant files and directories
        shutil.make_archive(snapshot_path[:-4], 'zip', root_dir='unified_core/db')
        
        return snapshot_path

    def restore_latest_snapshot(self):
        snapshots = sorted([f for f in os.listdir(self.base_dir) if f.startswith("snapshot_")])
        if not snapshots:
            raise ValueError("No snapshots found")
        
        latest_snapshot = snapshots[-1]
        snapshot_path = os.path.join(self.base_dir, latest_snapshot)
        
        # Implement logic to restore the system state from the latest snapshot
        # For simplicity, let's assume we are copying all relevant files and directories back
        shutil.unpack_archive(snapshot_path, root_dir='unified_core/db')
        
    def list_snapshots(self):
        return [f for f in os.listdir(self.base_dir) if f.startswith("snapshot_")]

if __name__ == '__main__':
    snapshot_db = SnapshotDB('snapshots')
    
    # Save a snapshot
    snapshot_path = snapshot_db.save_snapshot()
    print(f"Snapshot saved at: {snapshot_path}")
    
    # List snapshots
    snapshots = snapshot_db.list_snapshots()
    print("Snapshots:", snapshots)
    
    # Restore the latest snapshot
    snapshot_db.restore_latest_snapshot()
    print("Latest snapshot restored")