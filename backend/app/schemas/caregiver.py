"""Caregiver Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class CaregiverInviteRequest(BaseModel):
    caregiver_phone: str


class CaregiverInviteResponse(BaseModel):
    invitation_id: str
    status: str = "pending"


class CaregiverAcceptRequest(BaseModel):
    elder_phone: str
    otp: str


class CaregiverAcceptResponse(BaseModel):
    status: str = "active"
    elder_id: str


class ElderSummary(BaseModel):
    elder_id: UUID
    name: str
    abha_number: Optional[str] = None
    policy_count: int = 0
    claim_count: int = 0


class MyEldersResponse(BaseModel):
    elders: List[ElderSummary]


class ActionRequestBody(BaseModel):
    action_type: str
    resource_id: Optional[str] = None


class ActionRequestResponse(BaseModel):
    consent_request_id: str
    message: str = "OTP sent to elder's registered mobile"


class ActionExecuteRequest(BaseModel):
    consent_request_id: str
    consent_token: str
    action_type: str
    payload: Optional[dict] = None


class ActionExecuteResponse(BaseModel):
    success: bool
    result: Optional[dict] = None
