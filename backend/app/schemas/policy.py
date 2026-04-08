"""Policy Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class PolicyBase(BaseModel):
    policy_type: str
    insurer_name: str
    scheme_name: Optional[str] = None
    coverage_amount: Optional[Decimal] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    tpa_name: Optional[str] = None
    tpa_code: Optional[str] = None


class PolicyCreate(PolicyBase):
    policy_number: Optional[str] = None
    tpa_phone: Optional[str] = None
    state_code: Optional[str] = None


class PolicyResponse(PolicyBase):
    id: UUID
    user_id: UUID
    policy_number: Optional[str] = None
    sum_insured_remaining: Optional[Decimal] = None
    tpa_phone: Optional[str] = None
    state_code: Optional[str] = None
    abha_synced: bool = False
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class PolicyListResponse(BaseModel):
    policies: List[PolicyResponse]
    total_coverage: Decimal = Decimal("0")
    active_count: int = 0


class PmjayCheckResponse(BaseModel):
    eligible: bool
    pmjay_id: Optional[str] = None
    beneficiary_name: Optional[str] = None
    coverage_amount: Optional[Decimal] = None
    policy_id: Optional[str] = None


class EligibilityCheckRequest(BaseModel):
    income_annual: int
    family_size: int
    state: str
    employment_type: str
    has_bpl_card: bool = False
    age: int
    health_conditions: Optional[List[str]] = None


class SchemeResult(BaseModel):
    scheme_name: str
    eligible: bool
    score: float
    reason: str
    enrollment_steps: List[str]


class EligibilityCheckResponse(BaseModel):
    schemes: List[SchemeResult]
