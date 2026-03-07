"""
P1.9 - HMAC-based Audit Log Integrity
Ensures audit logs cannot be tampered with and are cryptographically verifiable.
"""

import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class AuditEvent:
    """Signed audit event with HMAC verification."""

    event_id: str
    timestamp: float
    event_type: str
    payload: Dict[str, Any]
    hmac_signature: str
    previous_hash: Optional[str] = None  # Chain to previous event


class HMACLogger:
    """
    Tamper-evident audit logger using HMAC signatures.

    Features:
    - Each event is signed with HMAC-SHA256
    - Events are chained (blockchain-style)
    - Tampering is detectable
    - Verification endpoint available
    """

    def __init__(self, secret_key: bytes, log_file: str = "audit_hmac.log"):
        """
        Initialize HMAC logger.

        Args:
            secret_key: Secret key for HMAC (32+ bytes recommended)
            log_file: Path to audit log file
        """
        if len(secret_key) < 16:
            raise ValueError("Secret key must be at least 16 bytes")

        self.secret_key = secret_key
        self.log_file = log_file
        self.last_hash: Optional[str] = None

        # Load last hash from existing log
        self._load_last_hash()

    def _load_last_hash(self):
        """Load the hash of the last event from log file."""
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        event = json.loads(last_line)
                        self.last_hash = event.get("hmac_signature")
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Fresh log

    def _compute_hmac(
        self, event_id: str, timestamp: float, event_type: str, payload: Dict[str, Any], previous_hash: Optional[str]
    ) -> str:
        """
        Compute HMAC signature for an event.

        The signature includes all event data plus the previous hash (chaining).
        """
        # Canonical representation
        data = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
        }

        # Sort keys for deterministic JSON
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))

        # Compute HMAC-SHA256
        signature = hmac.new(self.secret_key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()

        return signature

    def log_event(self, event_id: str, event_type: str, payload: Dict[str, Any]) -> AuditEvent:
        """
        Log a tamper-evident event.

        Args:
            event_id: Unique event identifier
            event_type: Type of event (e.g., "memory_access", "intent")
            payload: Event data

        Returns:
            Signed AuditEvent
        """
        timestamp = time.time()

        # Compute HMAC signature with chaining
        signature = self._compute_hmac(
            event_id=event_id, timestamp=timestamp, event_type=event_type, payload=payload, previous_hash=self.last_hash
        )

        # Create event
        event = AuditEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            payload=payload,
            hmac_signature=signature,
            previous_hash=self.last_hash,
        )

        # Write to log
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

        # Update chain
        self.last_hash = signature

        return event

    def verify_event(self, event: AuditEvent) -> bool:
        """
        Verify an event's HMAC signature.

        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = self._compute_hmac(
            event_id=event.event_id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            payload=event.payload,
            previous_hash=event.previous_hash,
        )

        return hmac.compare_digest(event.hmac_signature, expected_signature)

    def verify_log(self) -> Dict[str, Any]:
        """
        Verify the entire audit log for tampering.

        Returns:
            Dict with verification results
        """
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()

            if not lines:
                return {"valid": True, "events_checked": 0, "message": "Empty log"}

            previous_hash = None
            tampered_events = []
            chain_broken = []

            for i, line in enumerate(lines, start=1):
                try:
                    event_data = json.loads(line.strip())
                    event = AuditEvent(**event_data)

                    # Verify HMAC
                    if not self.verify_event(event):
                        tampered_events.append(i)

                    # Verify chain
                    if event.previous_hash != previous_hash:
                        chain_broken.append(i)

                    previous_hash = event.hmac_signature

                except json.JSONDecodeError:
                    tampered_events.append(i)

            valid = len(tampered_events) == 0 and len(chain_broken) == 0

            return {
                "valid": valid,
                "events_checked": len(lines),
                "tampered_events": tampered_events,
                "chain_broken": chain_broken,
                "message": "Log is valid" if valid else "TAMPERING DETECTED",
            }

        except FileNotFoundError:
            return {"valid": True, "events_checked": 0, "message": "No log file"}

    def get_integrity_proof(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cryptographic proof that an event is in the log.

        Returns:
            Dict with event and verification info, or None if not found
        """
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    event_data = json.loads(line.strip())
                    if event_data["event_id"] == event_id:
                        event = AuditEvent(**event_data)
                        is_valid = self.verify_event(event)

                        return {
                            "event": asdict(event),
                            "verified": is_valid,
                            "timestamp_readable": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event.timestamp)),
                        }
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        return None


# Singleton instance (will be initialized with secret from .env)
_hmac_logger: Optional[HMACLogger] = None


def get_hmac_logger(secret_key: Optional[bytes] = None) -> HMACLogger:
    """
    Get or create the HMAC logger singleton.

    Args:
        secret_key: Secret key (required on first call)
    """
    global _hmac_logger

    if _hmac_logger is None:
        if secret_key is None:
            raise ValueError("Secret key required to initialize HMAC logger")
        _hmac_logger = HMACLogger(secret_key)

    return _hmac_logger
