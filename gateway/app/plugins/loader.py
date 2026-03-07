import importlib.util
import json
import logging
import os
from typing import Dict, List

from gateway.app.core.capabilities import PLUGIN_SAFE_CAPABILITIES, Capability
from gateway.app.plugins.manifest import PluginManifest
from gateway.app.plugins.registry import PluginRegistry
from gateway.app.plugins.signing import verify_signature

logger = logging.getLogger(__name__)

PLUGIN_DIR = ".noogh_memory/plugins"


class PluginLoader:
    def __init__(self, key: str):
        self.signing_key = key
        self.registry = PluginRegistry.get_instance()

    def load_all(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Refresh plugins. Returns { 'loaded': [...], 'rejected': [...] }
        """
        self.registry.clear()
        results = {"loaded": [], "rejected": []}

        if not os.path.exists(PLUGIN_DIR):
            return results

        for plugin_name in os.listdir(PLUGIN_DIR):
            plugin_path = os.path.join(PLUGIN_DIR, plugin_name)
            if not os.path.isdir(plugin_path):
                continue

            try:
                self._load_plugin(plugin_path, plugin_name)
                results["loaded"].append({"name": plugin_name})
            except Exception as e:
                logger.warning(f"Failed to load plugin {plugin_name}: {e}")
                results["rejected"].append({"name": plugin_name, "reason": str(e)})

        return results

    def _load_plugin(self, path: str, name: str):
        manifest_path = os.path.join(path, "plugin.json")
        sig_path = os.path.join(path, "plugin.sig")

        # 1. Check files existence
        if not os.path.exists(manifest_path) or not os.path.exists(sig_path):
            raise ValueError("Missing plugin.json or plugin.sig")

        # 2. Verify Signature (Fail-Closed)
        with open(manifest_path, "rb") as f:
            manifest_bytes = f.read()

        with open(sig_path, "r") as f:
            signature = f.read().strip()

        if not verify_signature(manifest_bytes, signature, self.signing_key):
            raise ValueError("Invalid Signature")

        # 3. Parse and Validate Manifest
        try:
            manifest_data = json.loads(manifest_bytes)
            manifest = PluginManifest(**manifest_data)
        except Exception as e:
            raise ValueError(f"Invalid Manifest JSON: {e}")

        # 4. Check Capabilities (Allowlist)
        for cap in manifest.capabilities:
            try:
                # Map string to Enum if possible, or check string directly against Enum values
                # Capability is Enum.
                # cap is string like "FS_READ"
                if cap not in Capability.__members__:
                    raise ValueError(f"Unknown capability: {cap}")

                c_enum = Capability[cap]
                if c_enum not in PLUGIN_SAFE_CAPABILITIES:
                    raise ValueError(f"Forbidden Capability: {cap}")
            except KeyError:
                raise ValueError(f"Invalid capability format: {cap}")

        # 5. Load Code
        entrypoint_file, entrypoint_func = manifest.entrypoint.split(":")
        code_path = os.path.join(path, entrypoint_file)

        if not os.path.exists(code_path):
            raise ValueError(f"Entrypoint file missing: {entrypoint_file}")

        spec = importlib.util.spec_from_file_location(f"plugins.{name}", code_path)
        if not spec or not spec.loader:
            raise ValueError("Failed to create module spec")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 6. Register
        if not hasattr(module, entrypoint_func):
            raise ValueError(f"Entrypoint function {entrypoint_func} not found")

        register_func = getattr(module, entrypoint_func)
        # register_func should take the registry as argument
        register_func(self.registry)

        # Track loaded
        self.registry.register_plugin(manifest.name, manifest.dict())
        logger.info(f"Loaded plugin: {manifest.name}")
