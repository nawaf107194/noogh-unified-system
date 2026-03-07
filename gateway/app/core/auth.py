"""
Gateway Auth Module - Re-exports from unified_core

LAYER 3 RE-EXPORT ONLY
This module does NOT implement authentication primitives.
All auth logic lives in unified_core/auth.py (Layer 1 SSOT).

This ensures:
- No circular dependencies (Layer 1 -> Layer 3 eliminated)
- Single source of truth for AuthContext and require_bearer
- Gateway can still import auth from its own namespace
"""

# Re-export from Layer 1 SSOT
from unified_core.auth import (
    AuthContext,
    require_bearer,
    require_scoped_token,
    require_admin,
    # صلاحيات كاملة
    ALL_SCOPES,
    FULL_ADMIN_AUTH,
    DASHBOARD_AUTH,
    get_full_admin_auth,
    get_dashboard_auth,
)

__all__ = [
    "AuthContext",
    "require_bearer",
    "require_scoped_token",
    "require_admin",
    "ALL_SCOPES",
    "FULL_ADMIN_AUTH",
    "DASHBOARD_AUTH",
    "get_full_admin_auth",
    "get_dashboard_auth",
]

