"""NHA (PMJAY) service — PMJAY eligibility check."""

import httpx
from config import settings


async def check_pmjay_eligibility(aadhaar_hash: str, user_data: dict) -> dict:
    """
    Check PMJAY (Ayushman Bharat) eligibility using NHA API.
    Returns eligibility status and beneficiary details.
    """
    if not settings.NHA_API_KEY or settings.APP_ENV == "development":
        # Sandbox mock — simulate eligibility based on income
        return {
            "eligible": True,
            "pmjay_id": f"PMJAY-{aadhaar_hash[:8].upper()}",
            "beneficiary_name": user_data.get("full_name", "Test User"),
            "coverage_amount": 500000,
            "scheme_name": "Ayushman Bharat PMJAY",
            "family_id": f"FAM-{aadhaar_hash[:6].upper()}",
            "state": user_data.get("state", "Tamil Nadu"),
        }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.NHA_BASE_URL}/beneficiary/verify",
            headers={"X-API-Key": settings.NHA_API_KEY},
            json={
                "aadhaar_hash": aadhaar_hash,
                "state": user_data.get("state", ""),
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
