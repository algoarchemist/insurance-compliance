"""JWE encrypt/decrypt utilities for NHCX protocol."""

import json
import uuid
from datetime import datetime, timezone

try:
    from jose import jwe
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False


def encrypt_payload_jwe(payload: dict, recipient_public_key: str) -> str:
    """
    Encrypt FHIR bundle payload for NHCX.
    Algorithm: RSA-OAEP, Encryption: A256GCM
    """
    if not HAS_JOSE or not recipient_public_key:
        # Dev fallback — return base64 encoded JSON
        import base64
        return base64.b64encode(json.dumps(payload).encode()).decode()

    return jwe.encrypt(
        json.dumps(payload).encode(),
        recipient_public_key,
        algorithm="RSA-OAEP",
        encryption="A256GCM",
    ).decode()


def decrypt_payload_jwe(token: str, private_key: str) -> dict:
    """Decrypt incoming NHCX response."""
    if not HAS_JOSE or not private_key:
        import base64
        try:
            return json.loads(base64.b64decode(token))
        except Exception:
            return {}

    decrypted = jwe.decrypt(token, private_key)
    return json.loads(decrypted)


def build_nhcx_request(
    payload: dict, sender_code: str, recipient_code: str, api_call_id: str
) -> dict:
    """Wrap JWE payload in NHCX request envelope."""
    from config import settings

    jwe_token = encrypt_payload_jwe(payload, settings.NHCX_ENCRYPTION_CERT)

    return {
        "payload": jwe_token,
        "protected": {
            "alg": "RSA-OAEP",
            "enc": "A256GCM",
            "x-hcx-sender_code": sender_code,
            "x-hcx-recipient_code": recipient_code,
            "x-hcx-api_call_id": api_call_id or str(uuid.uuid4()),
            "x-hcx-timestamp": datetime.now(timezone.utc).isoformat(),
            "x-hcx-status": "request.initiate",
        },
    }
