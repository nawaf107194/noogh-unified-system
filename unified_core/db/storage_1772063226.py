# unified_core/db/snapshot_db.py

import json
from datetime import datetime
from typing import List, Dict

class Snapshot:
    def __init__(self, timestamp: str, memory_state: List[Dict], innovation_state: List[Dict]):
        self.timestamp = timestamp
        self.memory_state = memory_state
        self.innovation_state = innovation_state

def save_snapshot(snapshot: Snapshot, filename: str = "snapshot.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": snapshot.timestamp,
            "memory_state": snapshot.memory_state,
            "innovation_state": snapshot.innovation_state
        }, f, ensure_ascii=False, indent=4)

def load_snapshot(filename: str = "snapshot.json") -> Snapshot:
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return Snapshot(
            timestamp=data["timestamp"],
            memory_state=data["memory_state"],
            innovation_state=data["innovation_state"]
        )

def get_latest_snapshot(directory: str) -> Snapshot:
    import os
    snapshot_files = [f for f in os.listdir(directory) if f.endswith('.json')]
    latest_file = max(snapshot_files, key=lambda x: int(x.split('.')[0]))
    return load_snapshot(os.path.join(directory, latest_file))

# Example usage
if __name__ == '__main__':
    # Simulate system state
    memory_state = [
        {"key": "belief1", "value": 0.9},
        {"key": "prediction1", "value": 1.2}
    ]
    innovation_state = [
        {"id": "innovation1", "status": "active"}
    ]

    # Create a snapshot and save it
    current_time = datetime.now().isoformat()
    snapshot = Snapshot(current_time, memory_state, innovation_state)
    save_snapshot(snapshot)

    # Load the latest snapshot
    latest_snapshot = get_latest_snapshot(".")
    print(latest_snapshot.__dict__)