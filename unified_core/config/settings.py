
"""
Noogh Unified System - Central Configuration
Single Source of Truth (SSOT) for Paths, Secrets, and Toggles.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# ==============================
# 1. CORE PATHS (Dynamic & Portable)
# ==============================
# Resolve root relative to this file: src/config/settings.py -> parents[2] is project root
_THIS_FILE = Path(__file__).resolve()
SRC_DIR = _THIS_FILE.parents[1]   # /home/noogh/projects/noogh_unified_system/src

# Load .env from SRC_DIR if it exists
dotenv_path = SRC_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
elif os.path.exists(".env"):
    load_dotenv(".env")
ROOT_DIR = _THIS_FILE.parents[2]  # /home/noogh/projects/noogh_unified_system
SRC_DIR = _THIS_FILE.parents[1]   # /home/noogh/projects/noogh_unified_system/src

# Data Directory Resolution
# Priority: Env Var > Default relative to project
_ENV_DATA_DIR = os.environ.get("NOOGH_DATA_DIR")
if _ENV_DATA_DIR:
    DATA_DIR = Path(_ENV_DATA_DIR).resolve()
else:
    DATA_DIR = ROOT_DIR / "data"

# SECURITY FIX: Do NOT create directories at import time
# Directories will be created explicitly during startup via initialize_directories()

# Sub-directories
DB_PATH = DATA_DIR / "shared_memory.sqlite"
LOG_DIR = DATA_DIR / "logs"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
WORLD_STATE_DIR = DATA_DIR / "world_state"
BACKUP_DIR = DATA_DIR / "backups"
SCARS_DIR = DATA_DIR / "scars"
PROTECTED_DIR = DATA_DIR / "protected"
CONSEQUENCE_DIR = DATA_DIR / "consequences"
COERCIVE_DIR = DATA_DIR / "coercive"
AMLA_LOG_PATH = DATA_DIR / "amla_audit.jsonl"
ASAA_LOG_PATH = DATA_DIR / "asaa_audit.jsonl"

# ... (rest of ENV and Secrets) ...

# ==============================
# 3. POLICIES & ALLOWLISTS
# ==============================

# ...

# Storage Locations (Consolidated)
# These lists mimic the multi-tiered storage logic (User, Backup, Hidden/System)
# But we map them to portable locations inside DATA_DIR by default.

def _get_tiered_locations(primary_dir: Path, backup_dir: Path, legacy_user_path: str = None) -> List[str]:
    locs = [
        str(primary_dir),
        str(backup_dir),
        "/tmp/.noogh_emergency"
    ]
    # If strictly needed for data migration, we could add legacy paths here if they exist
    return locs

WORLD_STORAGE_LOCATIONS = _get_tiered_locations(WORLD_STATE_DIR, BACKUP_DIR / "world")
SCAR_STORAGE_LOCATIONS = _get_tiered_locations(SCARS_DIR, BACKUP_DIR / "scars")
PROTECTED_STORAGE_LOCATIONS = _get_tiered_locations(PROTECTED_DIR, BACKUP_DIR / "protected")
CONSEQUENCE_STORAGE_LOCATIONS = _get_tiered_locations(CONSEQUENCE_DIR, BACKUP_DIR / "consequences")
COERCIVE_STORAGE_LOCATIONS = _get_tiered_locations(COERCIVE_DIR, BACKUP_DIR / "coercive")
def get_env_or_fail(key: str, default: str = None, dev_mode: bool = False) -> str:
    """
    Retrieve env var. If missing and no default, EXIT process.
    If dev_mode is True, allow weaker defaults with warning.
    """
    val = os.environ.get(key)
    if val:
        return val
    
    if default is not None:
        # If in strict production (checked via another flag?), maybe warn?
        # For now, we trust the caller's distinct default.
        return default

    # Failure case
    print(f"🛑 FATAL: Missing required environment variable: {key}")
    sys.exit(1)

# Env Mode
ENV_MODE = os.environ.get("NOOGH_ENV", "development").lower()
IS_PROD = ENV_MODE == "production"

# Secrets
JOB_SIGNING_SECRET = get_env_or_fail("NOOGH_JOB_SIGNING_SECRET", "dev-secret-CHANGE-IF-PROD" if not IS_PROD else None)
ADMIN_TOKEN = get_env_or_fail("NOOGH_ADMIN_TOKEN", "admin" if not IS_PROD else None)
SERVICE_TOKEN = get_env_or_fail("NOOGH_SERVICE_TOKEN", "service" if not IS_PROD else None)
READONLY_TOKEN = get_env_or_fail("NOOGH_READONLY_TOKEN", "readonly" if not IS_PROD else None)
INTERNAL_TOKEN = get_env_or_fail("NOOGH_INTERNAL_TOKEN", "internal" if not IS_PROD else None)

# ==============================
# 3. POLICIES & ALLOWLISTS
# ==============================

# Actuator: Filesystem Safe Paths (IMMUTABLE)
# MUST be absolute paths. We derive them from DATA_DIR to ensure portability.
# SECURITY: tuple = immutable, prevents runtime tampering
FILESYSTEM_ALLOWLIST: tuple[str, ...] = tuple([
    str(DATA_DIR),
    str(SRC_DIR / "unified_core" / "core" / ".data"), # Legacy support if needed
    "/tmp/noogh_safe"
])

# ... mapped above ...

# Actuator: Network Allowlist (IMMUTABLE)
# SECURITY: tuple = immutable, prevents runtime tampering
NETWORK_ALLOWLIST: tuple[str, ...] = tuple([
    r"^https?://127\.0\.0\.1(:\d+)?/",
    r"^https?://localhost(:\d+)?/",
    r"^https?://api\.noogh\.local/",
    r"^https?://neural-engine(:\d+)?/",
])

# Actuator: Process Command Allowlist (IMMUTABLE)
# SECURITY: tuple = immutable, prevents runtime tampering
PROCESS_ALLOWLIST: tuple[str, ...] = tuple([
    "/usr/bin/echo",
    "/usr/bin/date",
    "/usr/bin/whoami",
    "/usr/bin/hostname",
    "/usr/bin/uname",
    "/usr/bin/uptime",
    "/usr/bin/ls",
    "/usr/bin/cat",
    "/usr/bin/head",
    "/usr/bin/tail",
    "/usr/bin/wc",
    "/usr/bin/file",
    "/usr/bin/stat",
    "/usr/bin/ps",
    "/usr/bin/top",
    "/usr/bin/free",
    "/usr/bin/df",
])

# ==============================
# 4. LOGGING
# ==============================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
