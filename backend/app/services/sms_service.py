"""SMS service — OTP delivery via Twilio."""

import random
import hashlib
from datetime import datetime, timedelta, timezone

from config import settings
from app.core.redis_client import store_otp

try:
    from twilio.rest import Client as TwilioClient
    HAS_TWILIO = True
except ImportError:
    HAS_TWILIO = False


async def send_otp_sms(phone: str, purpose: str = "login") -> dict:
    """Send OTP via SMS. Returns txn_id and OTP hash."""
    import uuid
    otp = str(random.randint(100000, 999999))
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    txn_id = str(uuid.uuid4())

    # Store in Redis with 5 min TTL
    await store_otp(f"otp:{txn_id}", f"{otp_hash}:{phone}:{purpose}", ttl=300)

    if HAS_TWILIO and settings.TWILIO_ACCOUNT_SID and settings.APP_ENV != "development":
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f"Your Sugamai OTP is: {otp}. Valid for 5 minutes. Do not share.",
            from_=settings.TWILIO_FROM_NUMBER,
            to=f"+91{phone}" if not phone.startswith("+") else phone,
        )
    else:
        # Dev mode — log the OTP
        print(f"[DEV] OTP for {phone}: {otp} (purpose: {purpose})")

    return {"txn_id": txn_id, "otp_hash": otp_hash, "expires_in": 300}


async def send_notification_sms(phone: str, message: str) -> bool:
    """Send a notification SMS (non-OTP)."""
    if HAS_TWILIO and settings.TWILIO_ACCOUNT_SID and settings.APP_ENV != "development":
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_FROM_NUMBER,
            to=f"+91{phone}" if not phone.startswith("+") else phone,
        )
        return True
    else:
        print(f"[DEV] SMS to {phone}: {message}")
        return True
