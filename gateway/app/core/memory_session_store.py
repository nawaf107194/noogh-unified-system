"""
Memory session management for UC3 with isolation.
Different from task-based SessionStore - this handles memory access sessions.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MemorySessionStore:
    """
    Manages memory access sessions for isolation.
    Each session is tied to an authenticated token and has a TTL.
    """

    def __init__(self):
        self.sessions: Dict[str, Dict] = {}  # session_id -> session_data

    def create_session(self, token: str, user_scope: str = "default", ttl_hours: int = 24) -> str:
        """
        Create a new memory session for the given token.

        Args:
            token: The authenticated bearer token
            user_scope: Scope derived from token (admin/service/readonly/default)
            ttl_hours: Session time-to-live in hours

        Returns:
            session_id: Cryptographically random session identifier
        """
        session_id = secrets.token_urlsafe(32)

        self.sessions[session_id] = {
            "token": token,
            "user_scope": user_scope,
            "created": datetime.utcnow(),
            "expires": datetime.utcnow() + timedelta(hours=ttl_hours),
            "metadata": {},
            "memory_count": 0,
        }

        logger.info(f"Created memory session {session_id[:16]}... for scope={user_scope}, ttl={ttl_hours}h")
        return session_id

    def get_or_create_session(self, token: str, user_scope: str = "default", session_id: Optional[str] = None) -> str:
        """
        Get existing session or create new one.

        Args:
            token: Bearer token
            user_scope: User scope
            session_id: Optional existing session ID (from X-Session-ID header)

        Returns:
            session_id: Valid session identifier
        """
        if session_id and self.validate_session(session_id, token):
            return session_id

        return self.create_session(token, user_scope)

    def validate_session(self, session_id: str, token: str) -> bool:
        """
        Validate that session exists, is not expired, and matches token.

        Args:
            session_id: Session identifier
            token: Bearer token to verify

        Returns:
            True if session is valid, False otherwise
        """
        session = self.sessions.get(session_id)

        if not session:
            logger.warning(f"Memory session {session_id[:16]}... not found")
            return False

        # Check expiration
        if session["expires"] < datetime.utcnow():
            logger.info(f"Memory session {session_id[:16]}... expired")
            del self.sessions[session_id]
            return False

        # Verify token match
        if session["token"] != token:
            logger.warning(f"Token mismatch for memory session {session_id[:16]}...")
            return False

        return True

    def get_session_scope(self, session_id: str) -> Optional[str]:
        """Get the user scope for a session."""
        session = self.sessions.get(session_id)
        return session["user_scope"] if session else None

    def increment_memory_count(self, session_id: str):
        """Track memory operations per session."""
        if session_id in self.sessions:
            self.sessions[session_id]["memory_count"] += 1

    def cleanup_expired(self):
        """Remove expired sessions (call periodically)."""
        now = datetime.utcnow()
        expired = [sid for sid, s in self.sessions.items() if s["expires"] < now]

        for sid in expired:
            logger.info(f"Cleaning up expired memory session {sid[:16]}...")
            del self.sessions[sid]

        return len(expired)

    def get_stats(self) -> Dict:
        """Get session statistics."""
        now = datetime.utcnow()
        active = sum(1 for s in self.sessions.values() if s["expires"] > now)

        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active,
            "total_memory_operations": sum(s["memory_count"] for s in self.sessions.values()),
        }
