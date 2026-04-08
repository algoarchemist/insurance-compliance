"""Policies router — /api/v1/policies/*"""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import PolicyNotFound
from app.models.user import User
from app.models.policy import Policy
from app.schemas.policy import (
    PolicyCreate, PolicyResponse, PolicyListResponse,
    PmjayCheckResponse, EligibilityCheckRequest, EligibilityCheckResponse,
)
from app.services.nha_service import check_pmjay_eligibility
from app.services.eligibility_service import check_all_eligibility

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all policies for current user."""
    stmt = select(Policy).where(Policy.user_id == current_user.id, Policy.is_active == True)
    result = await db.execute(stmt)
    policies = result.scalars().all()

    total_coverage = sum(p.coverage_amount or 0 for p in policies)
    return PolicyListResponse(
        policies=[PolicyResponse.model_validate(p) for p in policies],
        total_coverage=total_coverage,
        active_count=len(policies),
    )


@router.post("/pmjay/check", response_model=PmjayCheckResponse)
async def check_pmjay(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check PMJAY eligibility and auto-link if eligible."""
    result = await check_pmjay_eligibility(
        current_user.aadhaar_hash,
        {"full_name": current_user.full_name, "state": current_user.state},
    )

    policy_id = None
    if result.get("eligible"):
        policy = Policy(
            user_id=current_user.id,
            policy_type="pmjay",
            insurer_name="National Health Authority",
            scheme_name="Ayushman Bharat PMJAY",
            policy_number=result.get("pmjay_id"),
            coverage_amount=result.get("coverage_amount", 500000),
            sum_insured_remaining=result.get("coverage_amount", 500000),
        )
        db.add(policy)
        await db.flush()
        policy_id = str(policy.id)

    return PmjayCheckResponse(
        eligible=result.get("eligible", False),
        pmjay_id=result.get("pmjay_id"),
        beneficiary_name=result.get("beneficiary_name"),
        coverage_amount=result.get("coverage_amount"),
        policy_id=policy_id,
    )


@router.post("", response_model=PolicyResponse)
async def add_policy(
    request: PolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a private/employer policy manually."""
    policy = Policy(
        user_id=current_user.id,
        policy_number=request.policy_number,
        policy_type=request.policy_type,
        insurer_name=request.insurer_name,
        scheme_name=request.scheme_name,
        coverage_amount=request.coverage_amount,
        sum_insured_remaining=request.coverage_amount,
        valid_from=request.valid_from,
        valid_until=request.valid_until,
        tpa_name=request.tpa_name,
        tpa_code=request.tpa_code,
        tpa_phone=request.tpa_phone,
        state_code=request.state_code,
    )
    db.add(policy)
    await db.flush()
    return PolicyResponse.model_validate(policy)


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single policy detail."""
    stmt = select(Policy).where(Policy.id == policy_id, Policy.user_id == current_user.id)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        raise PolicyNotFound()
    return PolicyResponse.model_validate(policy)


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a policy."""
    stmt = select(Policy).where(Policy.id == policy_id, Policy.user_id == current_user.id)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        raise PolicyNotFound()
    policy.is_active = False
    return {"message": "Policy removed"}


@router.post("/eligibility/check", response_model=EligibilityCheckResponse)
async def check_eligibility(
    request: EligibilityCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """AI eligibility checker."""
    profile = request.model_dump()
    result = await check_all_eligibility(
        profile,
        aadhaar_hash=current_user.aadhaar_hash,
        language=current_user.preferred_lang or "en",
    )
    return EligibilityCheckResponse(schemes=result.get("schemes", []))
