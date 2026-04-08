"""Auth router — /api/v1/auth/*"""

import hashlib
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user
from app.core.security import (
    create_access_token, create_refresh_token, verify_token,
    hash_aadhaar, hash_otp,
)
from app.core.redis_client import store_otp, get_otp, delete_key, blacklist_token
from app.core.exceptions import UidaiOtpExpired, UidaiOtpInvalid
from app.models.user import User
from app.schemas.auth import (
    AadhaarInitiateRequest, AadhaarInitiateResponse,
    AadhaarVerifyRequest, AadhaarVerifyResponse,
    RefreshTokenRequest, RefreshTokenResponse,
    OtpSendRequest, OtpSendResponse,
    OtpVerifyRequest, OtpVerifyResponse,
)
from app.services.uidai_service import initiate_aadhaar_otp, verify_aadhaar_otp, generate_swasth_id
from app.services.sms_service import send_otp_sms

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/aadhaar/initiate", response_model=AadhaarInitiateResponse)
async def aadhaar_initiate(request: AadhaarInitiateRequest):
    """Initiate Aadhaar OTP for login/registration."""
    result = await initiate_aadhaar_otp(request.aadhaar_number)
    return AadhaarInitiateResponse(
        txn_id=result["txn_id"],
        message=result["message"],
    )


@router.post("/aadhaar/verify", response_model=AadhaarVerifyResponse)
async def aadhaar_verify(
    request: AadhaarVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify Aadhaar OTP and login or register."""
    result = await verify_aadhaar_otp(request.txn_id, request.otp)

    if not result.get("verified"):
        raise UidaiOtpInvalid()

    kyc_data = result["kyc_data"]
    aadhaar_hash_value = result["aadhaar_hash"]

    # Check if user exists
    stmt = select(User).where(User.aadhaar_hash == aadhaar_hash_value)
    db_result = await db.execute(stmt)
    user = db_result.scalar_one_or_none()

    is_new_user = False

    if not user:
        # Register new user
        is_new_user = True
        dob_str = kyc_data.get("dob", "1990-01-01")
        try:
            dob = date.fromisoformat(dob_str)
        except (ValueError, TypeError):
            dob = date(1990, 1, 1)

        # Calculate age for elder check
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        is_elder = age >= 60

        swasth_id = generate_swasth_id(aadhaar_hash_value)

        address_data = kyc_data.get("address", {})
        user = User(
            aadhaar_hash=aadhaar_hash_value,
            swasth_id=swasth_id,
            full_name=kyc_data.get("name", "User"),
            date_of_birth=dob,
            gender=kyc_data.get("gender"),
            phone=address_data.get("phone", f"9{aadhaar_hash_value[:9]}"),
            state=address_data.get("state", ""),
            district=address_data.get("district", ""),
            address_json=address_data,
            is_elder=is_elder,
            role="elder" if is_elder else "user",
        )
        db.add(user)
        await db.flush()

    # Create tokens
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    from app.schemas.user import UserResponse
    user_response = UserResponse.model_validate(user)

    return AadhaarVerifyResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response,
        is_new_user=is_new_user,
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token."""
    payload = verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = create_access_token({"sub": payload["sub"], "role": payload.get("role", "user")})
    return RefreshTokenResponse(access_token=new_access)


@router.post("/logout")
async def logout(
    req: Request,
    current_user: User = Depends(get_current_user),
):
    """Logout — blacklist refresh token."""
    auth_header = req.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    await blacklist_token(token)
    return {"message": "Logged out successfully"}


@router.post("/otp/send", response_model=OtpSendResponse)
async def send_otp(request: OtpSendRequest):
    """Send OTP for non-login purposes."""
    result = await send_otp_sms(request.phone, request.purpose)
    return OtpSendResponse(txn_id=result["txn_id"], expires_in=result["expires_in"])


@router.post("/otp/verify", response_model=OtpVerifyResponse)
async def verify_otp(request: OtpVerifyRequest):
    """Verify OTP for non-login purposes."""
    stored = await get_otp(f"otp:{request.txn_id}")
    if not stored:
        raise UidaiOtpExpired()

    parts = stored.split(":")
    stored_hash = parts[0]
    otp_hash_value = hashlib.sha256(request.otp.encode()).hexdigest()

    if otp_hash_value != stored_hash:
        raise UidaiOtpInvalid()

    await delete_key(f"otp:{request.txn_id}")

    # For caregiver consent, create a consent token
    consent_token = None
    if request.purpose == "caregiver_consent":
        from app.core.security import create_consent_token
        consent_token = create_consent_token("", "", "caregiver_action")

    return OtpVerifyResponse(verified=True, consent_token=consent_token)
