"""Identity router — /api/v1/identity/* (ABHA, UIDAI)"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import AbhaAlreadyLinked
from app.models.user import User
from app.services.abdm_service import create_abha, link_existing_abha, get_abha_profile, get_abdm_token

router = APIRouter(prefix="/identity", tags=["Identity"])


@router.post("/abha/create")
async def create_abha_endpoint(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create new ABHA number via ABDM."""
    if current_user.abha_number:
        raise AbhaAlreadyLinked()

    token = await get_abdm_token()
    result = await create_abha(request.get("aadhaar_txn_id", ""), token)

    current_user.abha_number = result.get("healthIdNumber", "")
    current_user.abha_address = result.get("healthId", "")
    await db.flush()

    return {
        "abha_number": current_user.abha_number,
        "abha_address": current_user.abha_address,
        "health_id_token": result.get("token", ""),
    }


@router.post("/abha/link")
async def link_abha_endpoint(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Link existing ABHA to account."""
    if current_user.abha_number:
        raise AbhaAlreadyLinked()

    result = await link_existing_abha(
        request.get("abha_number", ""),
        request.get("otp", ""),
    )

    if result.get("linked"):
        details = result.get("abha_details", {})
        current_user.abha_number = details.get("healthIdNumber", request.get("abha_number", ""))
        current_user.abha_address = details.get("healthId", "")
        await db.flush()

    return result


@router.get("/abha/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Fetch ABHA profile details."""
    token = await get_abdm_token()
    return await get_abha_profile(token)


@router.get("/abha/health-locker")
async def get_health_locker(current_user: User = Depends(get_current_user)):
    """List documents in ABHA health locker."""
    return {"documents": [], "message": "Health locker integration — sandbox mode"}


@router.post("/abha/consent")
async def grant_consent(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """Grant PHR consent to a provider."""
    return {"status": "consent_granted", "message": "Consent granted — sandbox mode"}
