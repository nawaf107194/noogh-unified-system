# unified_core/db/snapshot_db.py

import os
import json
from datetime import datetime

class SnapshotDB:
    def __init__(self, snapshot_dir='snapshots'):
        self.snapshot_dir = snapshot_dir
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)

    def save_snapshot(self, data):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        snapshot_path = os.path.join(self.snapshot_dir, f'snapshot_{timestamp}.json')
        with open(snapshot_path, 'w') as f:
            json.dump(data, f)
        return snapshot_path

    def load_latest_snapshot(self):
        snapshots = [f for f in os.listdir(self.snapshot_dir) if f.startswith('snapshot_')]
        if not snapshots:
            raise FileNotFoundError("No snapshots found")
        latest_snapshot = sorted(snapshots)[-1]
        snapshot_path = os.path.join(self.snapshot_dir, latest_snapshot)
        with open(snapshot_path, 'r') as f:
            data = json.load(f)
        return data

if __name__ == '__main__':
    # Example usage
    db_manager = SnapshotDB()
    current_state = {
        "beliefs": [...],
        "predictions": [...],
        "observations": [...]
    }
    snapshot_path = db_manager.save_snapshot(current_state)
    print(f"Snapshot saved to {snapshot_path}")

    latest_state = db_manager.load_latest_snapshot()
    print("Latest Snapshot Data:", latest_state)