import hashlib
import hmac


def sign_bytes(data: bytes, key: str) -> str:
    """Generate HMAC-SHA256 signature for bytes."""
    if not key:
        raise ValueError("Signing key is missing")
    return hmac.new(key.encode(), data, hashlib.sha256).hexdigest()


def verify_signature(data: bytes, signature: str, key: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    if not signature or not key:
        return False
    expected = sign_bytes(data, key)
    return hmac.compare_digest(expected, signature)
