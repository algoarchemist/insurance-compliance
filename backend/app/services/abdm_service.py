"""ABDM (ABHA) service — sandbox integration with mock fallback."""

import httpx
from config import settings
from app.core.redis_client import cache_set, cache_get


async def get_abdm_token() -> str:
    """Get ABDM API token, cached in Redis."""
    cached = await cache_get("abdm_token")
    if cached:
        return cached

    if not settings.ABDM_CLIENT_ID or settings.APP_ENV == "development":
        token = "mock-abdm-token-sandbox"
        await cache_set("abdm_token", token, ttl=1800)
        return token

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ABDM_BASE_URL}/v0.5/sessions",
            json={
                "clientId": settings.ABDM_CLIENT_ID,
                "clientSecret": settings.ABDM_CLIENT_SECRET,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

    token = data.get("accessToken", "")
    await cache_set("abdm_token", token, ttl=1800)
    return token


async def create_abha(aadhaar_txn_id: str, token: str) -> dict:
    """Create new ABHA number via ABDM sandbox."""
    if not settings.ABDM_CLIENT_ID or settings.APP_ENV == "development":
        import random
        abha_num = f"{random.randint(10,99)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        return {
            "healthIdNumber": abha_num,
            "healthId": "testuser@abdm",
            "name": "Test User",
            "token": "mock-health-id-token",
        }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ABDM_BASE_URL}/v1/registration/aadhaar/createHealthIdWithPreVerified",
            headers={"Authorization": f"Bearer {token}"},
            json={"txnId": aadhaar_txn_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


async def link_existing_abha(abha_number: str, otp: str) -> dict:
    """Link an existing ABHA to the current user account."""
    if not settings.ABDM_CLIENT_ID or settings.APP_ENV == "development":
        return {
            "linked": True,
            "abha_details": {
                "healthIdNumber": abha_number,
                "healthId": "user@abdm",
                "name": "Test User",
            },
        }

    token = await get_abdm_token()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ABDM_BASE_URL}/v1/registration/aadhaar/verifyOtp",
            headers={"Authorization": f"Bearer {token}"},
            json={"otp": otp, "healthId": abha_number},
            timeout=30,
        )
        response.raise_for_status()
        return {"linked": True, "abha_details": response.json()}


async def get_abha_profile(token: str) -> dict:
    """Fetch ABHA profile details."""
    if not settings.ABDM_CLIENT_ID or settings.APP_ENV == "development":
        return {
            "healthIdNumber": "12-3456-7890-1234",
            "healthId": "testuser@abdm",
            "name": "Test User",
            "yearOfBirth": "1990",
            "gender": "M",
            "state": "Tamil Nadu",
            "district": "Chennai",
        }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.ABDM_BASE_URL}/v1/account/profile",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
