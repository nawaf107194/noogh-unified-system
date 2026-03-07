"""
Innovation Storage - Backward-compatible wrapper for ProtobufInnovationStorage
Uses the high-performance protobuf storage system while maintaining the existing API.
"""

import os
import time
from pathlib import Path
from typing import List, Optional

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from proto_generated.evolution import learning_pb2
from unified_core.storage.protobuf_storage import ProtobufInnovationStorage


class InnovationStorage:
    """
    Manages storage of innovations using Protocol Buffers.

    This is a compatibility wrapper around ProtobufInnovationStorage,
    providing the same API that existing code expects while using
    the advanced storage implementation underneath.
    """

    def __init__(self, pb_file: str = "/home/noogh/.noogh/innovations.pb"):
        self.pb_file = pb_file
        # Use the advanced protobuf storage implementation
        self._storage = ProtobufInnovationStorage(storage_path=pb_file)

    def get_all(self) -> List[learning_pb2.Innovation]:
        """Load all innovations from storage."""
        return self._storage.load_all_innovations()

    def save_all(self, innovations: List[learning_pb2.Innovation]):
        """
        Overwrite the entire storage with the given list of innovations.

        This is implemented by deleting the old file and writing all innovations fresh.
        """
        # Delete old file if exists
        if os.path.exists(self.pb_file):
            os.remove(self.pb_file)

        # Write all innovations
        for inno in innovations:
            self._storage.save_innovation(inno)

    def append(self, innovation: learning_pb2.Innovation):
        """Append a single innovation to storage."""
        self._storage.save_innovation(innovation)

    def update_status(self, innovation_id: str, new_status: 'learning_pb2.InnovationStatus') -> bool:
        """
        Update the status of a specific innovation.

        Returns True if innovation was found and updated, False otherwise.
        """
        all_innovations = self.get_all()
        updated = False

        for inno in all_innovations:
            if inno.id == innovation_id:
                inno.status = new_status
                inno.applied_at.seconds = int(time.time())
                updated = True
                break

        if updated:
            self.save_all(all_innovations)

        return updated

    def get_stats(self):
        """Get storage statistics (delegates to advanced storage)."""
        return self._storage.get_stats()


# Re-export for convenience
def get_innovation_storage() -> InnovationStorage:
    """Get or create a global InnovationStorage instance."""
    global _global_storage
    if '_global_storage' not in globals():
        _global_storage = InnovationStorage()
    return _global_storage
