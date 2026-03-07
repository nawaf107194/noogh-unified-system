# unified_core/db/snapshot_db.py

import os
import time
from shutil import copyfile
from unified_core.db.data_router import DataRouter

class SnapshotDB:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

    def save_snapshot(self):
        current_time = int(time.time())
        snapshot_path = os.path.join(self.base_dir, f"snapshot_{current_time}.db")
        DataRouter.save_state(snapshot_path)
        self.prune_old_snapshots()

    def prune_old_snapshots(self, retention_days=7):
        current_time = time.time()
        cutoff_time = current_time - (retention_days * 24 * 60 * 60)

        for filename in os.listdir(self.base_dir):
            if filename.startswith("snapshot_"):
                snapshot_path = os.path.join(self.base_dir, filename)
                if os.path.getmtime(snapshot_path) < cutoff_time:
                    os.remove(snapshot_path)

if __name__ == '__main__':
    import threading
    snapshot_db = SnapshotDB('snapshots')
    
    # Save daily snapshots
    def save_daily_snapshots():
        while True:
            snapshot_db.save_snapshot()
            time.sleep(86400)  # Sleep for 24 hours

    thread = threading.Thread(target=save_daily_snapshots)
    thread.start()