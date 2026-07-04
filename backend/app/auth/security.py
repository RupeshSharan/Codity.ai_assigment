from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import os
import secrets

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError


PASSWORD_ITERATIONS = 260_000


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${_b64url(salt)}${_b64url(digest)}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded_hash.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), _b64url_decode(salt), int(iterations)
    )
    return hmac.compare_digest(_b64url(digest), expected)


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iss": settings.jwt_issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
    }
    payload.update(extra_claims or {})
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}.{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.jwt_secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signing_input = f"{header_segment}.{payload_segment}"
        expected = hmac.new(settings.jwt_secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url(expected), signature_segment):
            raise AuthenticationError("Invalid token signature.")
        payload = json.loads(_b64url_decode(payload_segment))
    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError("Invalid bearer token.") from exc
    if payload.get("iss") != settings.jwt_issuer:
        raise AuthenticationError("Invalid token issuer.")
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise AuthenticationError("Token has expired.")
    return payload


def new_worker_id(prefix: str = "worker") -> str:
    hostname = os.getenv("HOSTNAME", "local")
    return f"{prefix}-{hostname}-{secrets.token_hex(4)}"

