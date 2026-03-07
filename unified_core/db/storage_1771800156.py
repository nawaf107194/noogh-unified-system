import os
import shutil
from datetime import datetime

class SnapshotDB:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)

    def save_snapshot(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        snapshot_path = os.path.join(self.root_dir, f"snapshot_{timestamp}")
        shutil.copytree(".", snapshot_path)
        print(f"Snapshot saved to {snapshot_path}")

if __name__ == '__main__':
    snapshot_db = SnapshotDB("snapshots")
    snapshot_db.save_snapshot()