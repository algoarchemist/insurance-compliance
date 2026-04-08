"""Custom HTTP exceptions with localized error messages."""

from fastapi import HTTPException, status
from typing import Optional


class SugamaiException(HTTPException):
    """Base exception with error code and optional Tamil translation."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        message_ta: str = "",
        details: Optional[dict] = None,
    ):
        detail = {
            "error": {
                "code": code,
                "message": message,
                "message_ta": message_ta,
                "details": details or {},
            }
        }
        super().__init__(status_code=status_code, detail=detail)


# Auth errors
class UidaiOtpExpired(SugamaiException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="UIDAI_OTP_EXPIRED",
            message="The OTP has expired. Please request a new one.",
            message_ta="OTP காலாவதியானது. புதிதாக கோரவும்.",
        )


class UidaiOtpInvalid(SugamaiException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="UIDAI_OTP_INVALID",
            message="Invalid OTP. Please check and try again.",
            message_ta="தவறான OTP. சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
        )


class AbhaAlreadyLinked(SugamaiException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="ABHA_ALREADY_LINKED",
            message="An ABHA number is already linked to this account.",
            message_ta="இந்த கணக்கில் ஏற்கனவே ABHA எண் இணைக்கப்பட்டுள்ளது.",
        )


# Policy errors
class PolicyNotFound(SugamaiException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="POLICY_NOT_FOUND",
            message="Policy not found.",
            message_ta="காப்பீடு பாலிசி கிடைக்கவில்லை.",
        )


# Hospital errors
class HospitalNotEmpanelled(SugamaiException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="HOSPITAL_NOT_EMPANELLED",
            message="This hospital is not empanelled under the selected policy.",
            message_ta="இந்த மருத்துவமனை தேர்ந்தெடுக்கப்பட்ட பாலிசியில் பதிவு செய்யப்படவில்லை.",
        )


# Claims errors
class ClaimGapDetected(SugamaiException):
    def __init__(self, gaps: list):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="CLAIM_GAP_DETECTED",
            message="Required documents or information are missing from the claim.",
            message_ta="க்ளெய்மில் தேவையான ஆவணங்கள் அல்லது தகவல்கள் இல்லை.",
            details={"gaps": gaps},
        )


class NhcxSubmissionFailed(SugamaiException):
    def __init__(self, details: dict = None):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="NHCX_SUBMISSION_FAILED",
            message="Failed to submit claim to NHCX. Please try again later.",
            message_ta="NHCX-க்கு க்ளெய்ம் சமர்ப்பிக்க முடியவில்லை. பின்னர் மீண்டும் முயற்சிக்கவும்.",
            details=details,
        )


class OcrParseFailed(SugamaiException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="OCR_PARSE_FAILED",
            message="Failed to parse the uploaded document. Please upload a clearer image.",
            message_ta="பதிவேற்றிய ஆவணத்தை படிக்க முடியவில்லை. தெளிவான படத்தை பதிவேற்றவும்.",
        )


# Caregiver errors
class CaregiverConsentRequired(SugamaiException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="CAREGIVER_CONSENT_REQUIRED",
            message="Elder's OTP consent is required for this action.",
            message_ta="இந்த செயலுக்கு முதியவரின் OTP ஒப்புதல் தேவை.",
        )


class CaregiverConsentExpired(SugamaiException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="CAREGIVER_CONSENT_EXPIRED",
            message="The consent token has expired. Please request a new OTP.",
            message_ta="ஒப்புதல் டோக்கன் காலாவதியானது. புதிய OTP கோரவும்.",
        )


# Bank errors
class BankVerificationPending(SugamaiException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="BANK_VERIFICATION_PENDING",
            message="Bank account verification is still pending.",
            message_ta="வங்கிக் கணக்கு சரிபார்ப்பு நிலுவையில் உள்ளது.",
        )
