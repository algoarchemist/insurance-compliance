"""Bank service — Penny drop verification via Razorpay."""

import httpx
from config import settings


async def verify_bank_account_penny_drop(account_number: str, ifsc_code: str, account_holder: str) -> dict:
    """
    Verify bank account via penny drop (₹1 transfer and verify).
    Uses Razorpay Fund Account API in sandbox.
    """
    if not settings.RAZORPAY_KEY_ID or settings.APP_ENV == "development":
        # Dev mock — always return verified
        return {
            "verified": True,
            "bank_name": _get_bank_name_from_ifsc(ifsc_code),
            "account_holder_name": account_holder,
        }

    import base64
    auth = base64.b64encode(
        f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        # Create fund account
        response = await client.post(
            "https://api.razorpay.com/v1/fund_accounts/validations",
            headers={"Authorization": f"Basic {auth}"},
            json={
                "account_number": account_number,
                "ifsc": ifsc_code,
                "fund_account": {
                    "account_type": "bank_account",
                    "bank_account": {
                        "ifsc": ifsc_code,
                        "beneficiary_name": account_holder,
                        "account_number": account_number,
                    },
                },
                "amount": 100,  # ₹1 in paise
                "currency": "INR",
                "notes": {"purpose": "sugamai_verification"},
            },
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

    return {
        "verified": result.get("status") == "completed",
        "bank_name": _get_bank_name_from_ifsc(ifsc_code),
        "account_holder_name": result.get("fund_account", {}).get("bank_account", {}).get("beneficiary_name", ""),
    }


def _get_bank_name_from_ifsc(ifsc: str) -> str:
    """Derive bank name from IFSC code prefix."""
    bank_map = {
        "SBIN": "State Bank of India",
        "HDFC": "HDFC Bank",
        "ICIC": "ICICI Bank",
        "UTIB": "Axis Bank",
        "PUNB": "Punjab National Bank",
        "CNRB": "Canara Bank",
        "BKID": "Bank of India",
        "UBIN": "Union Bank of India",
        "IOBA": "Indian Overseas Bank",
        "KKBK": "Kotak Mahindra Bank",
    }
    prefix = ifsc[:4].upper()
    return bank_map.get(prefix, f"Bank ({prefix})")
