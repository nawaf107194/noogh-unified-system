import json
from typing import Dict, List

class FeatureFlagManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.flags = self.load_flags()

    def load_flags(self) -> Dict[str, bool]:
        try:
            with open(self.config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_flags(self):
        with open(self.config_path, 'w') as file:
            json.dump(self.flags, file, indent=4)

    def enable_feature(self, feature_name: str):
        if feature_name in self.flags:
            self.flags[feature_name] = True
            self.save_flags()
        else:
            raise KeyError(f"Feature '{feature_name}' not found in configuration.")

    def disable_feature(self, feature_name: str):
        if feature_name in self.flags:
            self.flags[feature_name] = False
            self.save_flags()
        else:
            raise KeyError(f"Feature '{feature_name}' not found in configuration.")

    def is_feature_enabled(self, feature_name: str) -> bool:
        return self.flags.get(feature_name, False)

    def list_features(self) -> List[str]:
        return list(self.flags.keys())

# Example usage
if __name__ == "__main__":
    manager = FeatureFlagManager('config/feature_flags.json')
    print(manager.list_features())
    manager.enable_feature('new_feature')
    print(manager.is_feature_enabled('new_feature'))