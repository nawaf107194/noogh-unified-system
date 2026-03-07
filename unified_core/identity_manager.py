import uuid
import json
import os
from typing import Dict, Optional
from unified_core.config.settings import DATA_DIR

class IdentityManager:
    """
    Manages unique identities for agents, components, and the system itself.
    Ensures that IDs are persistent across restarts.
    """
    _instance: Optional['IdentityManager'] = None
    _identities: Dict[str, str] = {}
    _storage_path: str = str(DATA_DIR / "identities.json")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IdentityManager, cls).__new__(cls)
            cls._instance._load_identities()
        return cls._instance

    def _load_identities(self):
        """Load persistent identities from storage."""
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path, 'r') as f:
                    self._identities = json.load(f)
            except Exception as e:
                print(f"Error loading identities: {e}")
                self._identities = {}

    def _save_identities(self):
        """Save identities to persistent storage."""
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            with open(self._storage_path, 'w') as f:
                json.dump(self._identities, f, indent=4)
        except Exception as e:
            print(f"Error saving identities: {e}")

    def get_id(self, name: str, category: str = "agent") -> str:
        """
        Get or create a unique ID for a given name and category.
        """
        key = f"{category}:{name}"
        if key not in self._identities:
            self._identities[key] = str(uuid.uuid4())
            self._save_identities()
        return self._identities[key]

    def get_system_id(self) -> str:
        """Return the unique ID for this system instance."""
        return self.get_id("system_root", category="system")

    def resolve_name(self, identity_id: str) -> Optional[str]:
        """Find the name associated with a given ID."""
        for key, val in self._identities.items():
            if val == identity_id:
                return key.split(":", 1)[1]
        return None

    def clear_identities(self):
        """Reset all identities (caution: destructive)."""
        self._identities = {}
        if os.path.exists(self._storage_path):
            os.remove(self._storage_path)