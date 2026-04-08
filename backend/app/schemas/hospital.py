"""Hospital Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel


class HospitalBase(BaseModel):
    name: str
    type: str  # government, private, trust
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


class HospitalResponse(HospitalBase):
    id: UUID
    nhcx_provider_id: Optional[str] = None
    district: Optional[str] = None
    lat: Optional[Decimal] = None
    lng: Optional[Decimal] = None
    phone: Optional[str] = None
    empanelment_type: Optional[str] = None
    tpa_codes: Optional[List[str]] = None
    specialities: Optional[List[str]] = None
    services_covered: Optional[dict] = None
    is_active: bool = True
    created_at: datetime
    distance_km: Optional[float] = None

    class Config:
        from_attributes = True


class HospitalListResponse(BaseModel):
    hospitals: List[HospitalResponse]
    total: int


class ServiceCoverage(BaseModel):
    status: str  # covered, sub_limit, not_covered
    notes: Optional[str] = None
    cap_per_day: Optional[int] = None
    cap_per_claim: Optional[int] = None
    cap: Optional[int] = None


class TpaContact(BaseModel):
    name: str
    phone: str


class CoverageResponse(BaseModel):
    hospital_id: str
    policy_id: str
    empanelment_type: str
    services: Dict[str, ServiceCoverage]
    ai_summary: Optional[str] = None
    tpa_contact: Optional[TpaContact] = None
    admission_checklist: List[str] = []


class NhcxCoverageCheckRequest(BaseModel):
    policy_id: str


class NhcxCoverageCheckResponse(BaseModel):
    covered: bool
    empanelment_type: Optional[str] = None
    tpa_code: Optional[str] = None
