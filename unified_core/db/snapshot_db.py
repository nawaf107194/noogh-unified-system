# unified_core/db/snapshot_db.py
import json
from datetime import datetime

class SnapshotDB:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.snapshot_path = "unified_core/db/snaps/"

    def save_snapshot(self, system_state=None):
        if not system_state:
            system_state = self.db_manager.get_system_state()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        snapshot_file = f"{self.snapshot_path}snapshot_{timestamp}.json"
        
        with open(snapshot_file, 'w') as file:
            json.dump(system_state, file)
        
        print(f"Snapshot saved to {snapshot_file}")

    def load_latest_snapshot(self):
        import os
        snapshots = [f for f in os.listdir(self.snapshot_path) if f.startswith("snapshot_") and f.endswith(".json")]
        if not snapshots:
            return None
        
        latest_snapshot = max(snapshots, key=lambda x: datetime.strptime(x.split("_")[1], "%Y%m%d%H%M%S"))
        snapshot_file = os.path.join(self.snapshot_path, latest_snapshot)
        
        with open(snapshot_file, 'r') as file:
            system_state = json.load(file)
        
        return system_state

# Example usage
if __name__ == '__main__':
    from unified_core.db.postgres import PostgresManager
    db_manager = PostgresManager()
    snapshot_db = SnapshotDB(db_manager)
    
    # Save a snapshot of the current system state
    snapshot_db.save_snapshot()
    
    # Load the latest snapshot and print it
    latest_state = snapshot_db.load_latest_snapshot()
    print(latest_state)