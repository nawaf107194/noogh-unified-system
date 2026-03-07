import hmac
import json
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class ConfirmationStore:
    """Server-side pending action store with HMAC binding."""

    def __init__(self, secret_key: bytes):
        self.pending: Dict[str, Dict] = {}
        self.secret = secret_key

    def create_pending(self, audit_id: str, actions: List[Dict[str, Any]], operator_token: str) -> str:
        """Create pending confirmation, return nonce."""
        nonce = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(minutes=5)

        # HMAC binds nonce + audit_id + actions
        message = f"{nonce}:{audit_id}:{json.dumps(actions, sort_keys=True)}".encode()
        signature = hmac.new(self.secret, message, digestmod="sha256").hexdigest()

        self.pending[nonce] = {
            "audit_id": audit_id,
            "actions": actions,
            "operator_token": operator_token,
            "signature": signature,
            "expires": expires,
        }

        return nonce

    def validate_confirmation(self, nonce: str, operator_token: str) -> Optional[List[Dict[str, Any]]]:
        """Validate nonce, return actions if valid, consume nonce."""
        pending = self.pending.get(nonce)

        if not pending:
            return None

        # Check expiry
        if pending["expires"] < datetime.utcnow():
            del self.pending[nonce]
            return None

        # Check operator identity
        if pending["operator_token"] != operator_token:
            return None

        # Consume nonce (single-use)
        actions = pending["actions"]
        del self.pending[nonce]

        return actions

    def cleanup_expired(self):
        """Remove expired nonces."""
        now = datetime.utcnow()
        expired = [n for n, p in self.pending.items() if p["expires"] < now]
        for nonce in expired:
            del self.pending[nonce]
