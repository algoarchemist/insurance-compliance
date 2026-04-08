"""JWT token creation/verification and password hashing utilities."""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_aadhaar(aadhaar_number: str) -> str:
    """SHA-256 hash of Aadhaar number. Never store raw Aadhaar."""
    return hashlib.sha256(aadhaar_number.encode()).hexdigest()


def hash_otp(otp: str) -> str:
    """SHA-256 hash of OTP."""
    return hashlib.sha256(otp.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def create_consent_token(caregiver_id: str, elder_id: str, action_type: str) -> str:
    """Create a short-lived consent token for caregiver actions (15 min)."""
    data = {
        "caregiver_id": caregiver_id,
        "elder_id": elder_id,
        "action_type": action_type,
        "type": "consent",
    }
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    data["exp"] = expire
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_consent_token(token: str) -> Optional[dict]:
    """Verify a caregiver consent token."""
    return verify_token(token, token_type="consent")


def encrypt_bank_account(account_number: str) -> str:
    """AES-256 encrypt bank account number at rest."""
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(account_number.encode()) + encryptor.finalize()
    return base64.b64encode(iv + encrypted).decode()


def decrypt_bank_account(encrypted_data: str) -> str:
    """Decrypt AES-256 encrypted bank account number."""
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    raw = base64.b64decode(encrypted_data)
    iv = raw[:16]
    encrypted = raw[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    return (decryptor.update(encrypted) + decryptor.finalize()).decode()
