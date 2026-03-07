import os
import json
from datetime import datetime
from typing import Dict, Any

class ModelVersioning:
    def __init__(self, base_path: str = './model_versions'):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def save_model(self, model_name: str, version: int, model_data: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        """Save a model with its version and metadata."""
        timestamp = datetime.now().isoformat()
        version_path = os.path.join(self.base_path, f"{model_name}_v{version}")
        os.makedirs(version_path, exist_ok=True)
        
        with open(os.path.join(version_path, 'model.json'), 'w') as model_file:
            json.dump(model_data, model_file)
        
        with open(os.path.join(version_path, 'metadata.json'), 'w') as meta_file:
            json.dump({**metadata, 'timestamp': timestamp}, meta_file)

    def load_model(self, model_name: str, version: int) -> Dict[str, Any]:
        """Load a model by its name and version."""
        version_path = os.path.join(self.base_path, f"{model_name}_v{version}")
        if not os.path.exists(version_path):
            raise FileNotFoundError(f"Model {model_name} version {version} not found.")
        
        with open(os.path.join(version_path, 'model.json'), 'r') as model_file:
            model_data = json.load(model_file)
        
        with open(os.path.join(version_path, 'metadata.json'), 'r') as meta_file:
            metadata = json.load(meta_file)
        
        return {'model': model_data, 'metadata': metadata}

    def list_versions(self, model_name: str) -> List[int]:
        """List all available versions for a given model."""
        versions = []
        for item in os.listdir(self.base_path):
            if item.startswith(f"{model_name}_v"):
                try:
                    version = int(item.split('_v')[1])
                    versions.append(version)
                except ValueError:
                    continue
        return sorted(versions)

# Example usage
if __name__ == "__main__":
    versioning = ModelVersioning()
    model_data = {"weights": [0.1, 0.2, 0.3], "bias": 0.5}
    metadata = {"author": "AI Team", "description": "Initial model version"}
    
    versioning.save_model('example_model', 1, model_data, metadata)
    print(versioning.load_model('example_model', 1))
    print(versioning.list_versions('example_model'))