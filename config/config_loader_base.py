from config.config_loader_base import ConfigLoaderBase
import yaml

class YamlConfigLoader(ConfigLoaderBase):
    def load(self) -> Dict[str, Any]:
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        self._validate_config(config)
        return self._post_process_config(config)