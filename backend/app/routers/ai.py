"""AI router — /api/v1/ai/*"""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import (
    EligibilityChatRequest, EligibilityChatResponse,
    CoverageSummarizeRequest, CoverageSummarizeResponse,
    RejectionExplainRequest, RejectionExplainResponse,
    BillParseRequest, BillParseResponse,
    ChecklistRequest, ChecklistResponse,
)
from app.services.ai_service import (
    chat_eligibility, generate_coverage_summary,
    explain_rejection, generate_admission_checklist,
)
from app.services.ocr_service import extract_bill_with_ocr

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/eligibility/chat", response_model=EligibilityChatResponse)
async def eligibility_chat(
    request: EligibilityChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Conversational AI for eligibility."""
    messages = request.history + [{"role": "user", "content": request.message}]
    reply = await chat_eligibility(messages, current_user.preferred_lang or "en")
    return EligibilityChatResponse(reply=reply, schemes_identified=[])


@router.post("/coverage/summarize", response_model=CoverageSummarizeResponse)
async def coverage_summarize(
    request: CoverageSummarizeRequest,
    current_user: User = Depends(get_current_user),
):
    """Summarize coverage grid in plain language."""
    summary = await generate_coverage_summary(request.coverage_grid, request.language)
    return CoverageSummarizeResponse(summary=summary)


@router.post("/rejection/explain", response_model=RejectionExplainResponse)
async def rejection_explain(
    request: RejectionExplainRequest,
    current_user: User = Depends(get_current_user),
):
    """Explain claim rejection."""
    result = await explain_rejection(request.rejection_code, {"claim_id": request.claim_id}, request.language)
    return RejectionExplainResponse(
        explanation=result.get("explanation", ""),
        remediation_steps=result.get("remediation_steps", []),
    )


@router.post("/bill/parse", response_model=BillParseResponse)
async def bill_parse(
    request: BillParseRequest,
    current_user: User = Depends(get_current_user),
):
    """Parse uploaded bill image/PDF."""
    result = await extract_bill_with_ocr(request.doc_id)
    return BillParseResponse(
        extracted_items=result.get("items", []),
        totals={"total_amount": result.get("total_amount", 0)},
        metadata={
            "hospital_name": result.get("hospital_name", ""),
            "doctor_name": result.get("doctor_name", ""),
            "admission_date": result.get("admission_date", ""),
            "discharge_date": result.get("discharge_date", ""),
        },
    )


@router.post("/checklist/generate", response_model=ChecklistResponse)
async def generate_checklist(
    request: ChecklistRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate pre-admission checklist."""
    checklist = await generate_admission_checklist(
        {"id": request.hospital_id, "name": "Hospital"},
        {"id": request.policy_id, "insurer_name": "Insurance", "policy_type": "private"},
        request.procedure,
    )
    return ChecklistResponse(checklist=checklist)
