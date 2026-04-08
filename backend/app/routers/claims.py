"""Claims router — /api/v1/claims/*"""

import uuid as uuid_lib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import ClaimGapDetected, NhcxSubmissionFailed
from app.core.minio_client import upload_file
from app.models.user import User
from app.models.claim import Claim, ClaimStatusHistory, BankAccount
from app.models.policy import Policy
from app.models.hospital import Hospital
from app.schemas.claim import (
    PreAuthRequest, PreAuthResponse,
    CashlessInitiateRequest, CashlessDischargeRequest,
    ReimbursementRequest, DocumentUploadResponse,
    OcrParseResponse, OcrExtractedItem,
    FhirBuildResponse, GapCheckResponse, GapItem,
    ClaimSubmitRequest, ClaimSubmitResponse,
    ClaimDetailResponse, ClaimListResponse, ClaimSummaryResponse,
    ClaimStatusEntry, QueryRespondRequest,
    BankAccountCreate, BankAccountResponse,
)
from app.services.nhcx_service import submit_pre_auth, submit_claim
from app.services.fhir_builder import build_pre_auth_bundle, build_claim_bundle, validate_fhir_bundle
from app.services.ocr_service import extract_bill_with_ocr
from app.services.ai_service import detect_claim_gaps, explain_rejection
from app.core.security import encrypt_bank_account
from app.tasks.claim_tasks import poll_pre_auth_status as poll_pre_auth_task, poll_claim_status as poll_claim_task, trigger_ocr_parsing

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.get("", response_model=ClaimListResponse)
async def list_claims(
    status: Optional[str] = Query(None),
    claim_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List claims for current user."""
    stmt = select(Claim).where(Claim.user_id == current_user.id)
    if status:
        stmt = stmt.where(Claim.status == status)
    if claim_type:
        stmt = stmt.where(Claim.claim_type == claim_type)
    stmt = stmt.order_by(Claim.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    claims = result.scalars().all()

    # Get total count
    count_stmt = select(Claim).where(Claim.user_id == current_user.id)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    summaries = []
    for c in claims:
        hospital_name = None
        if c.hospital_id:
            h = await db.execute(select(Hospital).where(Hospital.id == c.hospital_id))
            hosp = h.scalar_one_or_none()
            hospital_name = hosp.name if hosp else None
        summaries.append(ClaimSummaryResponse(
            id=c.id, claim_type=c.claim_type, status=c.status,
            claim_amount=c.claim_amount, approved_amount=c.approved_amount,
            settled_amount=c.settled_amount, hospital_name=hospital_name,
            created_at=c.created_at,
        ))

    return ClaimListResponse(claims=summaries, total=total, page=page)


@router.post("/pre-auth", response_model=PreAuthResponse)
async def initiate_pre_auth(
    request: PreAuthRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initiate pre-authorization."""
    claim = Claim(
        user_id=current_user.id,
        policy_id=UUID(request.policy_id),
        hospital_id=UUID(request.hospital_id),
        claim_type="cashless",
        status="pre_auth_pending",
        claim_amount=request.estimated_amount,
    )
    db.add(claim)
    await db.flush()

    # Build FHIR bundle
    patient = {"id": str(current_user.id), "full_name": current_user.full_name,
               "date_of_birth": str(current_user.date_of_birth), "gender": current_user.gender,
               "abha_number": current_user.abha_number or ""}
    procedure = {"procedure_code": request.procedure_code, "procedure_name": request.procedure_name}
    fhir_bundle = build_pre_auth_bundle(patient, {}, {}, procedure, float(request.estimated_amount))
    claim.fhir_bundle = fhir_bundle

    # Submit to NHCX
    nhcx_result = await submit_pre_auth({"hospital_nhcx_id": ""}, fhir_bundle)
    claim.nhcx_pre_auth_id = nhcx_result.get("pre_auth_id")

    # Record history
    history = ClaimStatusHistory(claim_id=claim.id, status="pre_auth_pending", changed_by="user")
    db.add(history)
    await db.flush()

    # Start polling task
    try:
        poll_pre_auth_task.delay(str(claim.id), claim.nhcx_pre_auth_id or "")
    except Exception:
        pass  # Queue might not be running in dev

    return PreAuthResponse(claim_id=str(claim.id), nhcx_pre_auth_id=claim.nhcx_pre_auth_id, status="pre_auth_pending")


@router.get("/{claim_id}/pre-auth/status")
async def get_pre_auth_status(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll pre-auth status."""
    stmt = select(Claim).where(Claim.id == claim_id, Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"claim_id": str(claim.id), "status": claim.status, "approved_amount": claim.approved_amount}


@router.post("/cashless/initiate")
async def initiate_cashless(
    request: CashlessInitiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start cashless claim at hospital admission."""
    stmt = select(Claim).where(Claim.nhcx_pre_auth_id == request.pre_auth_id, Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Pre-auth not found")
    return {"claim_id": str(claim.id), "status": claim.status}


@router.post("/cashless/discharge")
async def cashless_discharge(
    request: CashlessDischargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit discharge claim."""
    stmt = select(Claim).where(Claim.id == UUID(request.claim_id), Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim.status = "submitted"
    claim.submitted_at = datetime.now(timezone.utc)
    history = ClaimStatusHistory(claim_id=claim.id, status="submitted", changed_by="user")
    db.add(history)
    return {"claim_id": str(claim.id), "status": "submitted"}


@router.post("/reimbursement")
async def create_reimbursement(
    request: ReimbursementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start reimbursement claim."""
    claim = Claim(
        user_id=current_user.id,
        policy_id=UUID(request.policy_id),
        hospital_id=UUID(request.hospital_id) if request.hospital_id else None,
        claim_type="reimbursement",
        status="draft",
        claim_amount=request.claim_amount,
    )
    db.add(claim)
    await db.flush()
    history = ClaimStatusHistory(claim_id=claim.id, status="draft", changed_by="user")
    db.add(history)
    return {"claim_id": str(claim.id)}


@router.post("/{claim_id}/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    claim_id: UUID,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a claim document."""
    stmt = select(Claim).where(Claim.id == claim_id, Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    file_data = await file.read()
    minio_key = upload_file(file_data, file.content_type or "application/octet-stream", f"claims/{claim_id}")
    doc_id = str(uuid_lib.uuid4())

    if not claim.documents:
        claim.documents = []
    claim.documents = claim.documents + [{"doc_id": doc_id, "doc_type": doc_type, "minio_key": minio_key, "uploaded_at": datetime.now(timezone.utc).isoformat()}]

    # Auto OCR for hospital bills
    if doc_type == "hospital_bill":
        try:
            trigger_ocr_parsing.delay(str(claim_id), doc_id, minio_key)
        except Exception:
            pass

    return DocumentUploadResponse(doc_id=doc_id, minio_key=minio_key, doc_type=doc_type)


@router.post("/{claim_id}/ocr/parse")
async def parse_ocr(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger OCR parsing on uploaded bill."""
    stmt = select(Claim).where(Claim.id == claim_id, Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Find the hospital_bill document
    bill_doc = None
    for doc in (claim.documents or []):
        if doc.get("doc_type") == "hospital_bill":
            bill_doc = doc
            break

    if bill_doc:
        ocr_result = await extract_bill_with_ocr(bill_doc["minio_key"])
        claim.ocr_extracted = ocr_result
    else:
        from app.services.ocr_service import _mock_ocr_result
        ocr_result = _mock_ocr_result()
        claim.ocr_extracted = ocr_result

    return ocr_result


@router.post("/{claim_id}/fhir/build")
async def build_fhir(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Build FHIR R4 claim bundle."""
    stmt = select(Claim).where(Claim.id == claim_id, Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    patient = {"id": str(current_user.id), "full_name": current_user.full_name}
    ocr_items = claim.ocr_extracted.get("items", []) if claim.ocr_extracted else []

    fhir_bundle = build_claim_bundle(patient, {}, {}, ocr_items, claim.pre_auth_reference or "", claim.documents or [])
    errors = validate_fhir_bundle(fhir_bundle)

    claim.fhir_bundle = fhir_bundle
    gaps = await detect_claim_gaps(
        {"ocr_extracted": claim.ocr_extracted, "pre_auth_reference": claim.pre_auth_reference},
        claim.documents or [], fhir_bundle
    )

    return {"fhir_bundle": fhir_bundle, "validation_errors": errors, "gap_alerts": gaps}


@router.get("/{claim_id}/gap-check")
async def gap_check(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI gap check before submission."""
    stmt = select(Claim).where(Claim.id == claim_id, Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    gaps = await detect_claim_gaps(
        {"ocr_extracted": claim.ocr_extracted},
        claim.documents or [], claim.fhir_bundle or {}
    )
    claim.gap_alerts = gaps
    return {"ready_to_submit": len(gaps) == 0, "gaps": gaps}


@router.post("/{claim_id}/submit", response_model=ClaimSubmitResponse)
async def submit_claim_endpoint(
    claim_id: UUID,
    request: ClaimSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit claim to NHCX."""
    stmt = select(Claim).where(Claim.id == claim_id, Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim.bank_account_id = UUID(request.bank_account_id)
    claim.submitted_by = current_user.id
    claim.submitted_at = datetime.now(timezone.utc)

    nhcx_result = await submit_claim(claim.fhir_bundle or {}, claim.pre_auth_reference or "")
    claim.nhcx_claim_id = nhcx_result.get("nhcx_claim_id")
    claim.status = "submitted"

    history = ClaimStatusHistory(claim_id=claim.id, status="submitted", changed_by="user")
    db.add(history)

    try:
        poll_claim_task.delay(str(claim.id), claim.nhcx_claim_id or "")
    except Exception:
        pass

    return ClaimSubmitResponse(
        nhcx_claim_id=claim.nhcx_claim_id,
        correlation_id=nhcx_result.get("correlation_id"),
        status="submitted",
    )


@router.get("/{claim_id}", response_model=ClaimDetailResponse)
async def get_claim(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full claim detail including timeline."""
    stmt = select(Claim).where(Claim.id == claim_id, Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    timeline = [
        ClaimStatusEntry(status=h.status, timestamp=h.created_at, notes=h.notes)
        for h in (claim.status_history or [])
    ]

    return ClaimDetailResponse(
        id=claim.id, user_id=claim.user_id, policy_id=claim.policy_id,
        hospital_id=claim.hospital_id, claim_type=claim.claim_type,
        status=claim.status, nhcx_claim_id=claim.nhcx_claim_id,
        claim_amount=claim.claim_amount, approved_amount=claim.approved_amount,
        settled_amount=claim.settled_amount, rejection_code=claim.rejection_code,
        rejection_reason=claim.rejection_reason,
        ai_rejection_explanation=claim.ai_rejection_explanation,
        documents=claim.documents, ocr_extracted=claim.ocr_extracted,
        gap_alerts=claim.gap_alerts, fhir_bundle=claim.fhir_bundle,
        timeline=timeline, created_at=claim.created_at, updated_at=claim.updated_at,
    )


@router.post("/{claim_id}/query/respond")
async def respond_to_query(
    claim_id: UUID,
    request: QueryRespondRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Respond to TPA query with additional documents."""
    stmt = select(Claim).where(Claim.id == claim_id, Claim.user_id == current_user.id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim.status = "submitted"
    history = ClaimStatusHistory(claim_id=claim.id, status="submitted", notes=f"Query response: {request.response_text[:100]}", changed_by="user")
    db.add(history)
    return {"status": "submitted"}
