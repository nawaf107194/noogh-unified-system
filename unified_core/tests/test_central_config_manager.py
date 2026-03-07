import unittest
import os
import json
from unified_core.core.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.config_manager = ConfigManager()
        self.config_manager.clear()
        self.test_json = 'test_config.json'
        with open(self.test_json, 'w') as f:
            json.dump({"api": {"key": "12345", "url": "http://localhost"}, "debug": True}, f)

    def tearDown(self):
        if os.path.exists(self.test_json):
            os.remove(self.test_json)
        if os.path.exists('saved_config.json'):
            os.remove('saved_config.json')

    def test_singleton(self):
        cm2 = ConfigManager()
        self.assertIs(self.config_manager, cm2)

    def test_load_and_get(self):
        self.assertTrue(self.config_manager.load_config(self.test_json))
        self.assertEqual(self.config_manager.get_setting('api.key'), '12345')
        self.assertEqual(self.config_manager.get_setting('debug'), True)
        self.assertEqual(self.config_manager.get_setting('nonexistent', 'default'), 'default')

    def test_set_and_save(self):
        self.config_manager.set_setting('new.setting', 'value')
        self.assertEqual(self.config_manager.get_setting('new.setting'), 'value')
        self.assertTrue(self.config_manager.save_config('saved_config.json'))
        
        with open('saved_config.json', 'r') as f:
            data = json.load(f)
            self.assertEqual(data['new']['setting'], 'value')

if __name__ == "__main__":
    unittest.main()
