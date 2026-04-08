"""Claim Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class PreAuthRequest(BaseModel):
    policy_id: str
    hospital_id: str
    procedure_code: str
    procedure_name: str
    estimated_amount: Decimal
    expected_admission_date: date
    doctor_referral_doc_id: Optional[str] = None


class PreAuthResponse(BaseModel):
    claim_id: str
    nhcx_pre_auth_id: Optional[str] = None
    status: str = "pre_auth_pending"


class CashlessInitiateRequest(BaseModel):
    pre_auth_id: str
    hospital_id: str
    admission_date: date


class CashlessDischargeRequest(BaseModel):
    claim_id: str
    discharge_date: date
    final_bill_doc_id: str
    discharge_summary_doc_id: str


class ReimbursementRequest(BaseModel):
    policy_id: str
    hospital_id: Optional[str] = None
    admission_date: date
    discharge_date: date
    claim_amount: Decimal


class DocumentUploadResponse(BaseModel):
    doc_id: str
    minio_key: str
    doc_type: str


class OcrExtractedItem(BaseModel):
    description: str
    amount: Decimal
    quantity: Optional[int] = None
    unit: Optional[str] = None
    amount_type: Optional[str] = None


class OcrParseResponse(BaseModel):
    extracted_items: List[OcrExtractedItem]
    total_extracted: Decimal
    icd_codes_detected: List[str] = []
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None


class FhirBuildResponse(BaseModel):
    fhir_bundle: dict
    validation_errors: List[str] = []
    gap_alerts: List[dict] = []


class GapItem(BaseModel):
    field: str
    severity: str  # required, optional
    message: str


class GapCheckResponse(BaseModel):
    ready_to_submit: bool
    gaps: List[GapItem] = []


class ClaimSubmitRequest(BaseModel):
    bank_account_id: str
    confirmed_by_user: bool = True


class ClaimSubmitResponse(BaseModel):
    nhcx_claim_id: Optional[str] = None
    correlation_id: Optional[str] = None
    status: str = "submitted"
    estimated_settlement_days: int = 7


class ClaimStatusEntry(BaseModel):
    status: str
    timestamp: datetime
    notes: Optional[str] = None


class ClaimSummaryResponse(BaseModel):
    id: UUID
    claim_type: str
    status: str
    claim_amount: Optional[Decimal] = None
    approved_amount: Optional[Decimal] = None
    settled_amount: Optional[Decimal] = None
    hospital_name: Optional[str] = None
    created_at: datetime


class ClaimDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    policy_id: UUID
    hospital_id: Optional[UUID] = None
    claim_type: str
    status: str
    nhcx_claim_id: Optional[str] = None
    claim_amount: Optional[Decimal] = None
    approved_amount: Optional[Decimal] = None
    settled_amount: Optional[Decimal] = None
    rejection_code: Optional[str] = None
    rejection_reason: Optional[str] = None
    ai_rejection_explanation: Optional[str] = None
    documents: Optional[list] = None
    ocr_extracted: Optional[dict] = None
    gap_alerts: Optional[list] = None
    fhir_bundle: Optional[dict] = None
    timeline: List[ClaimStatusEntry] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClaimListResponse(BaseModel):
    claims: List[ClaimSummaryResponse]
    total: int
    page: int = 1


class QueryRespondRequest(BaseModel):
    response_text: str
    additional_doc_ids: List[str] = []


class BankAccountCreate(BaseModel):
    account_number: str
    ifsc_code: str
    account_holder: Optional[str] = None


class BankAccountResponse(BaseModel):
    id: UUID
    bank_name: Optional[str] = None
    ifsc_code: str
    account_holder: Optional[str] = None
    is_verified: bool = False
    is_primary: bool = False

    class Config:
        from_attributes = True
