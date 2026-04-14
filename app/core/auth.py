from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def create_session_token(member_id: str, email: str, secret: str, ttl_seconds: int) -> str:
    payload = {
        "member_id": member_id,
        "email": email,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _base64url_encode(payload_json)
    signature = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256)
    sig_b64 = _base64url_encode(signature.digest())
    return f"{payload_b64}.{sig_b64}"


def decode_session_token(token: str, secret: str) -> dict | None:
    if not token or "." not in token:
        return None
    payload_b64, sig_b64 = token.split(".", 1)
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    )
    if not hmac.compare_digest(_base64url_encode(expected_sig.digest()), sig_b64):
        return None
    try:
        payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
    except json.JSONDecodeError:
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None
    return payload
