"""Admin router — /api/v1/admin/*"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user import User
from app.models.hospital import Hospital
from app.models.claim import Claim
from app.models.audit_log import AuditLog
from app.schemas.user import UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """List all users (admin only)."""
    stmt = select(User).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return {"users": [UserResponse.model_validate(u) for u in users]}


@router.get("/claims")
async def list_all_claims(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "tpa_officer")),
):
    """List all claims (admin/TPA only)."""
    stmt = select(Claim)
    if status:
        stmt = stmt.where(Claim.status == status)
    stmt = stmt.order_by(Claim.created_at.desc()).offset((page - 1) * 20).limit(20)
    result = await db.execute(stmt)
    claims = result.scalars().all()
    return {"claims": [{"id": str(c.id), "status": c.status, "claim_type": c.claim_type, "amount": float(c.claim_amount or 0)} for c in claims]}


@router.get("/audit-logs")
async def list_audit_logs(
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """View audit logs (admin only)."""
    stmt = select(AuditLog)
    if user_id:
        stmt = stmt.where(AuditLog.target_user_id == UUID(user_id))
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset((page - 1) * 50).limit(50)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return {"logs": [{"id": str(l.id), "action": l.action, "actor_id": str(l.actor_id) if l.actor_id else None, "created_at": l.created_at.isoformat()} for l in logs]}


@router.put("/hospitals/{hospital_id}")
async def update_hospital(
    hospital_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "hospital_admin")),
):
    """Update hospital data (admin/hospital_admin only)."""
    stmt = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    for key, value in data.items():
        if hasattr(hospital, key) and key not in ("id", "created_at"):
            setattr(hospital, key, value)

    return {"message": "Hospital updated"}


# Bank accounts sub-router (mounted under /api/v1 directly in main.py)
bank_router = APIRouter(prefix="/bank-accounts", tags=["Bank Accounts"])


@bank_router.post("")
async def add_bank_account(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add bank account."""
    from app.core.security import encrypt_bank_account
    from app.models.claim import BankAccount
    from app.services.bank_service import _get_bank_name_from_ifsc

    encrypted_account = encrypt_bank_account(request.get("account_number", ""))
    bank_name = _get_bank_name_from_ifsc(request.get("ifsc_code", ""))

    account = BankAccount(
        user_id=current_user.id,
        account_number=encrypted_account,
        ifsc_code=request.get("ifsc_code", ""),
        bank_name=bank_name,
        account_holder=request.get("account_holder", ""),
    )
    db.add(account)
    await db.flush()

    # Trigger penny drop verification
    try:
        from app.tasks.claim_tasks import verify_bank_account
        verify_bank_account.delay(str(account.id))
    except Exception:
        pass

    return {"bank_account_id": str(account.id), "status": "verification_pending"}


@bank_router.get("")
async def list_bank_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's bank accounts."""
    from app.models.claim import BankAccount
    stmt = select(BankAccount).where(BankAccount.user_id == current_user.id)
    result = await db.execute(stmt)
    accounts = result.scalars().all()
    return {"accounts": [{"id": str(a.id), "bank_name": a.bank_name, "ifsc_code": a.ifsc_code, "account_holder": a.account_holder, "is_verified": a.is_verified, "is_primary": a.is_primary} for a in accounts]}


@bank_router.delete("/{account_id}")
async def delete_bank_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove bank account."""
    from app.models.claim import BankAccount
    stmt = select(BankAccount).where(BankAccount.id == account_id, BankAccount.user_id == current_user.id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    await db.delete(account)
    return {"message": "Bank account removed"}
