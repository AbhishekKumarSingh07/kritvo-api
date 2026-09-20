"""Password hashing, and OTP/phone/refresh-token hashing (LLD 12.1-12.2).

No plain OTP code or refresh token is ever persisted or logged from this module — only
an HMAC (OTP) or SHA-256 digest (refresh token, already 256 random bits, so a keyed hash
buys nothing a plain one doesn't). JWT access-token signing lives in ``core.tokens``, not
here: ``core.deps`` has to decode tokens too, and core may not import a feature module,
so the key-handling code that both sides need has to sit in core instead.
"""

import hashlib
import hmac
import secrets

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_phone(phone: str, key: str) -> bytes:
    return hmac.new(key.encode(), phone.encode(), hashlib.sha256).digest()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp_code(code: str, key: str) -> bytes:
    return hmac.new(key.encode(), code.encode(), hashlib.sha256).digest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)  # 256 bits of entropy


def hash_refresh_token(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


def encrypt_totp_secret(secret: str, key: str) -> bytes:
    return Fernet(key.encode()).encrypt(secret.encode())


def decrypt_totp_secret(encrypted: bytes, key: str) -> str:
    return Fernet(key.encode()).decrypt(encrypted).decode()


def verify_totp_code(secret: str, code: str) -> bool:
    # valid_window=1 accepts the previous/next 30-second step too, for clock drift.
    return bool(pyotp.TOTP(secret).verify(code, valid_window=1))
