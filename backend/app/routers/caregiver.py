"""Caregiver router — /api/v1/caregiver/*"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import CaregiverConsentRequired, CaregiverConsentExpired
from app.core.security import verify_consent_token
from app.models.user import User
from app.models.caregiver import Caregiver
from app.models.policy import Policy
from app.models.claim import Claim
from app.models.audit_log import AuditLog
from app.schemas.caregiver import (
    CaregiverInviteRequest, CaregiverInviteResponse,
    CaregiverAcceptRequest, CaregiverAcceptResponse,
    MyEldersResponse, ElderSummary,
    ActionRequestBody, ActionRequestResponse,
    ActionExecuteRequest, ActionExecuteResponse,
)
from app.services.sms_service import send_otp_sms

router = APIRouter(prefix="/caregiver", tags=["Caregiver"])


@router.post("/invite", response_model=CaregiverInviteResponse)
async def invite_caregiver(
    request: CaregiverInviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Elder invites a caregiver."""
    # Find caregiver user by phone
    stmt = select(User).where(User.phone == request.caregiver_phone)
    result = await db.execute(stmt)
    caregiver_user = result.scalar_one_or_none()

    if not caregiver_user:
        raise HTTPException(status_code=404, detail="User with that phone not found. They must register first.")

    # Check existing relationship
    existing = await db.execute(
        select(Caregiver).where(
            Caregiver.elder_id == current_user.id,
            Caregiver.caregiver_id == caregiver_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Caregiver relationship already exists")

    # Check max 2 caregivers
    count_stmt = select(Caregiver).where(
        Caregiver.elder_id == current_user.id,
        Caregiver.status == "active",
    )
    count_result = await db.execute(count_stmt)
    if len(count_result.scalars().all()) >= 2:
        raise HTTPException(status_code=422, detail="Maximum 2 caregivers allowed")

    caregiver_record = Caregiver(elder_id=current_user.id, caregiver_id=caregiver_user.id, status="pending")
    db.add(caregiver_record)
    await db.flush()

    # Send OTP to caregiver
    await send_otp_sms(request.caregiver_phone, "caregiver_consent")

    # Audit log
    audit = AuditLog(actor_id=current_user.id, target_user_id=caregiver_user.id, action="caregiver_invited", resource_type="caregiver", resource_id=caregiver_record.id)
    db.add(audit)

    return CaregiverInviteResponse(invitation_id=str(caregiver_record.id), status="pending")


@router.post("/accept", response_model=CaregiverAcceptResponse)
async def accept_invitation(
    request: CaregiverAcceptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Caregiver accepts invitation."""
    # Find elder by phone
    stmt = select(User).where(User.phone == request.elder_phone)
    result = await db.execute(stmt)
    elder = result.scalar_one_or_none()
    if not elder:
        raise HTTPException(status_code=404, detail="Elder not found")

    # Find pending invitation
    inv_stmt = select(Caregiver).where(
        Caregiver.elder_id == elder.id,
        Caregiver.caregiver_id == current_user.id,
        Caregiver.status == "pending",
    )
    inv_result = await db.execute(inv_stmt)
    invitation = inv_result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="No pending invitation found")

    invitation.status = "active"
    invitation.accepted_at = datetime.now(timezone.utc)
    current_user.role = "caregiver"

    return CaregiverAcceptResponse(status="active", elder_id=str(elder.id))


@router.get("/my-elders", response_model=MyEldersResponse)
async def list_my_elders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List elders the caregiver manages."""
    stmt = select(Caregiver).where(Caregiver.caregiver_id == current_user.id, Caregiver.status == "active")
    result = await db.execute(stmt)
    relations = result.scalars().all()

    elders = []
    for rel in relations:
        elder_stmt = select(User).where(User.id == rel.elder_id)
        elder_result = await db.execute(elder_stmt)
        elder = elder_result.scalar_one_or_none()
        if elder:
            policy_count = len(elder.policies) if elder.policies else 0
            claim_count = len(elder.claims) if elder.claims else 0
            elders.append(ElderSummary(
                elder_id=elder.id, name=elder.full_name,
                abha_number=elder.abha_number, policy_count=policy_count, claim_count=claim_count,
            ))

    return MyEldersResponse(elders=elders)


@router.get("/elders/{elder_id}/dashboard")
async def elder_dashboard(
    elder_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Caregiver view of elder's data (read-only)."""
    # Verify relationship
    rel_stmt = select(Caregiver).where(
        Caregiver.elder_id == elder_id,
        Caregiver.caregiver_id == current_user.id,
        Caregiver.status == "active",
    )
    rel_result = await db.execute(rel_stmt)
    if not rel_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized to view this elder's data")

    policies = await db.execute(select(Policy).where(Policy.user_id == elder_id, Policy.is_active == True))
    claims = await db.execute(select(Claim).where(Claim.user_id == elder_id))

    return {
        "policies": [{"id": str(p.id), "insurer_name": p.insurer_name, "policy_type": p.policy_type, "coverage_amount": float(p.coverage_amount or 0)} for p in policies.scalars().all()],
        "claims": [{"id": str(c.id), "status": c.status, "claim_type": c.claim_type, "amount": float(c.claim_amount or 0)} for c in claims.scalars().all()],
    }


@router.post("/elders/{elder_id}/action/request", response_model=ActionRequestResponse)
async def request_action_consent(
    elder_id: UUID,
    request: ActionRequestBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request OTP consent for a write action."""
    elder_stmt = select(User).where(User.id == elder_id)
    elder_result = await db.execute(elder_stmt)
    elder = elder_result.scalar_one_or_none()
    if not elder:
        raise HTTPException(status_code=404, detail="Elder not found")

    import uuid
    consent_request_id = str(uuid.uuid4())
    otp_result = await send_otp_sms(elder.phone, "caregiver_consent")

    from app.core.redis_client import store_otp
    import asyncio
    await store_otp(f"consent:{consent_request_id}", f"{str(current_user.id)}:{str(elder_id)}:{request.action_type}", ttl=900)

    return ActionRequestResponse(consent_request_id=consent_request_id)


@router.post("/elders/{elder_id}/action/execute", response_model=ActionExecuteResponse)
async def execute_action(
    elder_id: UUID,
    request: ActionExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute write action after OTP consent."""
    payload = verify_consent_token(request.consent_token)
    if not payload:
        raise CaregiverConsentExpired()

    # Audit
    audit = AuditLog(
        actor_id=current_user.id, target_user_id=elder_id,
        action=f"caregiver_action:{request.action_type}",
        resource_type="caregiver_action", details=request.payload,
    )
    db.add(audit)

    return ActionExecuteResponse(success=True, result={"message": "Action executed successfully"})


@router.delete("/elders/{elder_id}")
async def revoke_caregiver(
    elder_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Elder revokes caregiver access."""
    stmt = select(Caregiver).where(
        Caregiver.elder_id == current_user.id,
        Caregiver.caregiver_id == elder_id,
        Caregiver.status == "active",
    )
    result = await db.execute(stmt)
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=404, detail="Caregiver relationship not found")

    relation.status = "revoked"
    relation.revoked_at = datetime.now(timezone.utc)
    return {"message": "Caregiver access revoked"}
