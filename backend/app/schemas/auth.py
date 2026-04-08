"""Auth Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class AadhaarInitiateRequest(BaseModel):
    aadhaar_number: str = Field(..., min_length=12, max_length=12, pattern=r"^\d{12}$")


class AadhaarInitiateResponse(BaseModel):
    txn_id: str
    message: str = "OTP sent to registered mobile"


class AadhaarVerifyRequest(BaseModel):
    txn_id: str
    otp: str = Field(..., min_length=6, max_length=6)


class AadhaarVerifyResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse
    is_new_user: bool = False


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str


class OtpSendRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    purpose: str = Field(..., pattern=r"^(login|caregiver_consent|bank_verify)$")


class OtpSendResponse(BaseModel):
    txn_id: str
    expires_in: int = 300


class OtpVerifyRequest(BaseModel):
    txn_id: str
    otp: str = Field(..., min_length=6, max_length=6)
    purpose: str


class OtpVerifyResponse(BaseModel):
    verified: bool
    consent_token: Optional[str] = None
