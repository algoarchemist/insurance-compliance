"""UIDAI (Aadhaar) service — sandbox integration with mock fallback."""

import hashlib
import uuid
import random
import string
from datetime import datetime, timezone

import httpx
from config import settings
from app.core.redis_client import store_otp, get_otp, delete_key


async def initiate_aadhaar_otp(aadhaar_number: str) -> dict:
    """
    Initiate Aadhaar OTP authentication.
    In sandbox/dev mode without credentials, returns mock response.
    """
    txn_id = str(uuid.uuid4())

    if not settings.UIDAI_AUA_CODE or settings.APP_ENV == "development":
        # Dev/sandbox mock — store txn_id in Redis
        await store_otp(f"aadhaar_txn:{txn_id}", aadhaar_number, ttl=600)
        return {
            "txn_id": txn_id,
            "message": "OTP sent to registered mobile (sandbox mode)",
        }

    # Production UIDAI call
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.UIDAI_AUTH_URL}/otp",
            json={
                "uid": aadhaar_number,
                "auaCode": settings.UIDAI_AUA_CODE,
                "licenseKey": settings.UIDAI_LICENSE_KEY,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

    await store_otp(f"aadhaar_txn:{txn_id}", aadhaar_number, ttl=600)
    return {"txn_id": txn_id, "message": "OTP sent to registered mobile"}


async def verify_aadhaar_otp(txn_id: str, otp: str) -> dict:
    """
    Verify Aadhaar OTP and return eKYC data.
    In sandbox/dev mode, accepts any 6-digit OTP and returns mock eKYC.
    """
    stored_aadhaar = await get_otp(f"aadhaar_txn:{txn_id}")
    if not stored_aadhaar:
        return {"verified": False, "error": "Transaction expired or not found"}

    if not settings.UIDAI_AUA_CODE or settings.APP_ENV == "development":
        # Dev/sandbox mock — accept any 6-digit OTP
        if len(otp) != 6:
            return {"verified": False, "error": "Invalid OTP"}

        await delete_key(f"aadhaar_txn:{txn_id}")
        aadhaar_hash = hashlib.sha256(stored_aadhaar.encode()).hexdigest()

        # Mock eKYC data
        return {
            "verified": True,
            "kyc_data": {
                "name": "Test User",
                "dob": "1990-01-15",
                "gender": "M",
                "address": {
                    "house": "123",
                    "street": "MG Road",
                    "landmark": "Near Park",
                    "locality": "Anna Nagar",
                    "vtc": "Chennai",
                    "district": "Chennai",
                    "state": "Tamil Nadu",
                    "pincode": "600040",
                },
                "photo": None,
            },
            "aadhaar_hash": aadhaar_hash,
        }

    # Production UIDAI verification
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.UIDAI_AUTH_URL}/kyc",
            json={
                "txnId": txn_id,
                "otp": otp,
                "auaCode": settings.UIDAI_AUA_CODE,
                "licenseKey": settings.UIDAI_LICENSE_KEY,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

    await delete_key(f"aadhaar_txn:{txn_id}")
    aadhaar_hash = hashlib.sha256(stored_aadhaar.encode()).hexdigest()

    return {
        "verified": True,
        "kyc_data": data.get("kyc", {}),
        "aadhaar_hash": aadhaar_hash,
    }


def generate_swasth_id(aadhaar_hash: str) -> str:
    """
    Generate a unique SwasthID: SWA + timestamp + 4 random chars.
    Example: SWA202502150001XKQP
    """
    now = datetime.now(timezone.utc)
    timestamp_part = now.strftime("%Y%m%d%H%M")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SWA{timestamp_part}{random_part}"
