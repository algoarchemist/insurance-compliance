"""Hospitals router — /api/v1/hospitals/*"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.hospital import Hospital, HospitalPolicyCoverage
from app.models.policy import Policy
from app.schemas.hospital import (
    HospitalResponse, HospitalListResponse, CoverageResponse,
    ServiceCoverage, TpaContact, NhcxCoverageCheckRequest, NhcxCoverageCheckResponse,
)
from app.services.maps_service import calculate_distance
from app.services.nhcx_service import check_coverage_eligibility
from app.services.ai_service import generate_coverage_summary, generate_admission_checklist

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.get("", response_model=HospitalListResponse)
async def list_hospitals(
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    policy_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    radius_km: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    """Search hospitals with filters."""
    stmt = select(Hospital).where(Hospital.is_active == True)

    if city:
        stmt = stmt.where(Hospital.city.ilike(f"%{city}%"))
    if state:
        stmt = stmt.where(Hospital.state.ilike(f"%{state}%"))
    if type and type not in ("all", ""):
        stmt = stmt.where(Hospital.type == type)

    result = await db.execute(stmt)
    hospitals = result.scalars().all()

    # Calculate distances and filter
    hospital_list = []
    for h in hospitals:
        resp = HospitalResponse.model_validate(h)
        if lat and lng and h.lat and h.lng:
            dist = calculate_distance(lat, lng, float(h.lat), float(h.lng))
            if dist <= radius_km:
                resp.distance_km = round(dist, 1)
                hospital_list.append(resp)
        else:
            hospital_list.append(resp)

    # Sort by distance if available
    hospital_list.sort(key=lambda x: x.distance_km if x.distance_km else 999)

    return HospitalListResponse(hospitals=hospital_list, total=len(hospital_list))


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(hospital_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get hospital detail."""
    stmt = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    if not hospital:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Hospital not found")
    return HospitalResponse.model_validate(hospital)


@router.get("/{hospital_id}/coverage", response_model=CoverageResponse)
async def get_hospital_coverage(
    hospital_id: UUID,
    policy_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-service coverage for this hospital under a given policy."""
    stmt = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    if not hospital:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Get coverage mapping
    services = {
        "surgery": ServiceCoverage(status="covered"),
        "icu": ServiceCoverage(status="covered"),
        "general_ward": ServiceCoverage(status="sub_limit", cap_per_day=2000),
        "private_ward": ServiceCoverage(status="not_covered"),
        "ambulance": ServiceCoverage(status="covered", cap=1000),
        "opd": ServiceCoverage(status="not_covered"),
        "pharmacy": ServiceCoverage(status="sub_limit", cap_per_claim=5000),
    }

    if policy_id:
        stmt = select(HospitalPolicyCoverage).where(
            HospitalPolicyCoverage.hospital_id == hospital_id
        )
        cov_result = await db.execute(stmt)
        coverage = cov_result.scalar_one_or_none()
        if coverage and coverage.services:
            for svc, status in coverage.services.items():
                if isinstance(status, str):
                    if "sub_limit" in status:
                        parts = status.split(":")
                        cap = int(parts[1]) if len(parts) > 1 else None
                        services[svc] = ServiceCoverage(status="sub_limit", cap_per_day=cap)
                    else:
                        services[svc] = ServiceCoverage(status=status)

    # AI summary
    coverage_dict = {k: v.model_dump() for k, v in services.items()}
    ai_summary = await generate_coverage_summary(
        coverage_dict, current_user.preferred_lang or "en"
    )

    # Admission checklist
    policy_data = {}
    if policy_id:
        p_stmt = select(Policy).where(Policy.id == UUID(policy_id))
        p_result = await db.execute(p_stmt)
        policy = p_result.scalar_one_or_none()
        if policy:
            policy_data = {"insurer_name": policy.insurer_name, "policy_type": policy.policy_type}

    checklist = await generate_admission_checklist(
        {"name": hospital.name}, policy_data, "general"
    )

    return CoverageResponse(
        hospital_id=str(hospital_id),
        policy_id=policy_id or "",
        empanelment_type=hospital.empanelment_type or "cashless",
        services=services,
        ai_summary=ai_summary,
        tpa_contact=TpaContact(name="Vidal Health TPA", phone="1800-200-1234") if hospital.tpa_codes else None,
        admission_checklist=checklist,
    )


@router.post("/{hospital_id}/nhcx/coverage-check", response_model=NhcxCoverageCheckResponse)
async def nhcx_coverage_check(
    hospital_id: UUID,
    request: NhcxCoverageCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Live NHCX coverageEligibility API call."""
    stmt = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    if not hospital:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Hospital not found")

    nhcx_result = await check_coverage_eligibility(
        request.policy_id,
        hospital.nhcx_provider_id or "",
        str(current_user.id),
    )

    return NhcxCoverageCheckResponse(
        covered=nhcx_result.get("covered", False),
        empanelment_type=nhcx_result.get("empanelment_type"),
        tpa_code=nhcx_result.get("tpa_code"),
    )
