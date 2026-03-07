"""
Unified Core Authentication - Central auth module.

This module provides authentication utilities that can be used by
both gateway and neural_engine without circular dependencies.
"""

from dataclasses import dataclass
from typing import Dict, Set, Optional

from fastapi import Depends, Header, HTTPException, Request


@dataclass
class AuthContext:
    """Authentication context with token and scopes."""
    token: str
    scopes: Set[str]
    user_id: str = "anonymous"

    def require_scope(self, scope: str):
        """Raise SecurityError if specified scope is missing."""
        if "*" in self.scopes or "admin:all" in self.scopes:
            return
        if scope not in self.scopes:
            from unified_core.core.actuators import SecurityError
            raise SecurityError(f"Insufficient permissions: requires '{scope}' scope.")


def _build_token_scope_map(secrets: Dict[str, str]) -> Dict[str, Set[str]]:
    """Build token to scopes mapping from secrets."""
    admin = secrets.get("NOOGH_ADMIN_TOKEN", "").strip()
    service = secrets.get("NOOGH_SERVICE_TOKEN", "").strip()
    readonly = secrets.get("NOOGH_READONLY_TOKEN", "").strip()
    internal = secrets.get("NOOGH_INTERNAL_TOKEN", "").strip()

    mapping = {}
    if admin:
        mapping[admin] = {"*"}
    if internal:
        mapping[internal] = {"*"}
    if service:
        mapping[service] = {"tools:use", "http:request", "fs:read", "fs:write", "memory:rw", "exec"}
    if readonly:
        mapping[readonly] = {"read:status", "read:metrics"}
    return mapping


def require_bearer(request: Request, authorization: str | None = Header(default=None)) -> AuthContext:
    """Validate bearer token and return AuthContext with explicit scopes.
    Unknown token -> 401. Missing header -> 401.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    secrets = getattr(request.app.state, "secrets", {})
    token_map = _build_token_scope_map(secrets)

    scopes = token_map.get(token)
    if scopes is None:
        # Unknown token
        raise HTTPException(status_code=401, detail="Invalid token")

    return AuthContext(token=token, scopes=scopes)


def require_scoped_token(required_scopes: Set[str]):
    """Dependency factory ensuring AuthContext contains required scopes."""

    def dependency(auth: AuthContext = Depends(require_bearer)) -> None:
        # wildcard admin
        if "*" in auth.scopes:
            return
        if not required_scopes.issubset(auth.scopes):
            raise HTTPException(status_code=403, detail="Insufficient token scopes")

    return dependency


def require_admin(auth: AuthContext = Depends(require_bearer)) -> AuthContext:
    """Require admin token (wildcard scope)."""
    if "*" not in auth.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth


# =============================================================================
# Full Admin Permissions - صلاحيات المدير الكاملة
# =============================================================================

# جميع الصلاحيات المتاحة في النظام
ALL_SCOPES = {
    "*",                  # Wildcard admin
    "tools:use",          # استخدام الأدوات
    "http:request",       # طلبات HTTP خارجية
    "fs:read",            # قراءة الملفات
    "fs:write",           # كتابة الملفات
    "fs:delete",          # حذف الملفات
    "fs:system",          # ملفات النظام (خارج sandbox)
    "memory:rw",          # قراءة/كتابة الذاكرة
    "exec",               # تنفيذ أوامر
    "exec:system",        # أوامر النظام (sudo)
    "process:spawn",      # إنشاء عمليات
    "process:kill",       # إنهاء عمليات
    "network:full",       # وصول شبكي كامل
    "admin:all",          # صلاحيات المدير
    "read:status",        # قراءة الحالة
    "read:metrics",       # قراءة المقاييس
}

# سياق المصادقة للمدير الكامل
FULL_ADMIN_AUTH = AuthContext(
    token="NOOGH_INTERNAL_ADMIN",
    scopes=ALL_SCOPES
)

# سياق المصادقة للوحة التحكم
DASHBOARD_AUTH = AuthContext(
    token="NOOGH_DASHBOARD",
    scopes={"*", "tools:use", "fs:read", "fs:write", "memory:rw", "exec", "admin:all"}
)


def get_full_admin_auth() -> AuthContext:
    """الحصول على سياق المصادقة بصلاحيات كاملة"""
    return FULL_ADMIN_AUTH


def get_dashboard_auth() -> AuthContext:
    """الحصول على سياق المصادقة للوحة التحكم"""
    return DASHBOARD_AUTH


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
