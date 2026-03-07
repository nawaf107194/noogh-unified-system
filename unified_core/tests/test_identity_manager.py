import unittest
import os
import json
from unified_core.identity_manager import IdentityManager
from unified_core.config.settings import DATA_DIR

class TestIdentityManager(unittest.TestCase):
    def setUp(self):
        self.im = IdentityManager()
        self.im.clear_identities()
        self.test_name = "test_agent_alpha"

    def test_singleton(self):
        im2 = IdentityManager()
        self.assertIs(self.im, im2)

    def test_get_id(self):
        id1 = self.im.get_id(self.test_name)
        id2 = self.im.get_id(self.test_name)
        self.assertEqual(id1, id2)
        self.assertTrue(len(id1) > 30) # UUID length

    def test_persistence(self):
        id1 = self.im.get_id("persistent_agent")
        # Simulate restart by creating a new instance (though it is a singleton, the storage is what matters)
        # We'll just check the file
        storage_path = str(DATA_DIR / "identities.json")
        self.assertTrue(os.path.exists(storage_path))
        with open(storage_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["agent:persistent_agent"], id1)

    def test_system_id(self):
        sid = self.im.get_system_id()
        self.assertIn("system:system_root", self.im._identities)

    def test_resolve_name(self):
        id1 = self.im.get_id("resolver_test")
        name = self.im.resolve_name(id1)
        self.assertEqual(name, "resolver_test")

if __name__ == "__main__":
    unittest.main()
