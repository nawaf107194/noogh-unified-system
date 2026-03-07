"""
Configuration Integrity Verification and Initialization

SECURITY: This module provides:
1. Integrity verification for immutable allowlists
2. Explicit directory initialization (no import-time side effects)
"""
import hashlib
from pathlib import Path
from . import settings


# Compute integrity hashes at module load
_ALLOWLIST_INTEGRITY = {
    "filesystem": hashlib.sha256(str(settings.FILESYSTEM_ALLOWLIST).encode()).hexdigest(),
    "network": hashlib.sha256(str(settings.NETWORK_ALLOWLIST).encode()).hexdigest(),
    "process": hashlib.sha256(str(settings.PROCESS_ALLOWLIST).encode()).hexdigest(),
}


class ConfigurationTamperError(Exception):
    """Raised when configuration integrity check fails."""
    pass


def verify_integrity():
    """
    Verify that allowlists have not been tampered with at runtime.
    MUST be called before EVERY actuator operation.
    
    Raises:
        ConfigurationTamperError: If any allowlist hash mismatch detected
    """
    current_fs = hashlib.sha256(str(settings.FILESYSTEM_ALLOWLIST).encode()).hexdigest()
    current_net = hashlib.sha256(str(settings.NETWORK_ALLOWLIST).encode()).hexdigest()
    current_proc = hashlib.sha256(str(settings.PROCESS_ALLOWLIST).encode()).hexdigest()
    
    if current_fs != _ALLOWLIST_INTEGRITY["filesystem"]:
        raise ConfigurationTamperError(
            "SECURITY VIOLATION: FILESYSTEM_ALLOWLIST has been modified at runtime"
        )
    if current_net != _ALLOWLIST_INTEGRITY["network"]:
        raise ConfigurationTamperError(
            "SECURITY VIOLATION: NETWORK_ALLOWLIST has been modified at runtime"
        )
    if current_proc != _ALLOWLIST_INTEGRITY["process"]:
        raise ConfigurationTamperError(
            "SECURITY VIOLATION: PROCESS_ALLOWLIST has been modified at runtime"
        )


def initialize_directories():
    """
    Create all required directories.
    MUST be called explicitly during application startup.
    MUST NOT be called at import time.
    """
    directories = [
        settings.DATA_DIR,
        settings.LOG_DIR,
        settings.ARTIFACTS_DIR,
        settings.WORLD_STATE_DIR,
        settings.BACKUP_DIR,
        settings.SCARS_DIR,
        settings.PROTECTED_DIR,
        settings.CONSEQUENCE_DIR,
        settings.COERCIVE_DIR,
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create directory {directory}: {e}")
