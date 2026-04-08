"""Seed script — populate database with sample hospitals and policies."""

import asyncio
import uuid
from decimal import Decimal
from datetime import date

from app.core.database import async_session, engine, Base
from app.models.hospital import Hospital, HospitalPolicyCoverage
from app.models.policy import Policy
from app.models.user import User
from app.core.security import hash_aadhaar

SAMPLE_HOSPITALS = [
    {
        "name": "Apollo Hospital Chennai",
        "type": "private",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "address": "21, Greams Lane, Off Greams Road, Chennai 600006",
        "pincode": "600006",
        "lat": Decimal("13.0632"),
        "lng": Decimal("80.2519"),
        "phone": "044-28290200",
        "empanelment_type": "cashless",
        "tpa_codes": ["VHTPA", "MDTPA"],
        "specialities": ["cardiology", "orthopedics", "neurology", "oncology"],
        "nhcx_provider_id": "HCX-APOLLO-CHN-001",
    },
    {
        "name": "Government General Hospital Chennai",
        "type": "government",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "address": "Park Town, Chennai 600003",
        "pincode": "600003",
        "lat": Decimal("13.0858"),
        "lng": Decimal("80.2855"),
        "phone": "044-25305000",
        "empanelment_type": "both",
        "tpa_codes": ["NHA"],
        "specialities": ["general", "surgery", "orthopedics", "gynecology"],
        "nhcx_provider_id": "HCX-GGH-CHN-001",
    },
    {
        "name": "AIIMS Delhi",
        "type": "government",
        "city": "New Delhi",
        "state": "Delhi",
        "district": "New Delhi",
        "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi 110029",
        "pincode": "110029",
        "lat": Decimal("28.5672"),
        "lng": Decimal("77.2100"),
        "phone": "011-26588500",
        "empanelment_type": "both",
        "tpa_codes": ["NHA", "CGHS"],
        "specialities": ["all"],
        "nhcx_provider_id": "HCX-AIIMS-DEL-001",
    },
    {
        "name": "Fortis Hospital Bangalore",
        "type": "private",
        "city": "Bangalore",
        "state": "Karnataka",
        "district": "Bangalore",
        "address": "154/9, Bannerghatta Road, Bangalore 560076",
        "pincode": "560076",
        "lat": Decimal("12.8879"),
        "lng": Decimal("77.5979"),
        "phone": "080-66214444",
        "empanelment_type": "cashless",
        "tpa_codes": ["VHTPA", "PHTPA"],
        "specialities": ["cardiology", "orthopedics", "urology", "oncology"],
        "nhcx_provider_id": "HCX-FORTIS-BLR-001",
    },
    {
        "name": "Sri Ramachandra Hospital",
        "type": "trust",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "address": "Porur, Chennai 600116",
        "pincode": "600116",
        "lat": Decimal("13.0365"),
        "lng": Decimal("80.1576"),
        "phone": "044-45928500",
        "empanelment_type": "cashless",
        "tpa_codes": ["VHTPA"],
        "specialities": ["general", "cardiology", "nephrology"],
        "nhcx_provider_id": "HCX-SRMC-CHN-001",
    },
]

SAMPLE_COVERAGE = {
    "surgery": "covered",
    "icu": "covered",
    "general_ward": "sub_limit:2000",
    "private_ward": "not_covered",
    "ambulance": "sub_limit:1000",
    "opd": "not_covered",
    "pharmacy": "sub_limit:5000",
    "diagnostics": "covered",
}


async def seed_hospitals(session):
    """Insert sample hospitals."""
    for h_data in SAMPLE_HOSPITALS:
        hospital = Hospital(**h_data)
        session.add(hospital)
        await session.flush()
        coverage = HospitalPolicyCoverage(
            hospital_id=hospital.id,
            policy_type="private",
            tpa_code="VHTPA",
            services=SAMPLE_COVERAGE,
        )
        session.add(coverage)
    print(f"[SEED] Inserted {len(SAMPLE_HOSPITALS)} hospitals with coverage mappings")


async def seed_test_user(session):
    """Create a test user for development."""
    test_aadhaar = "123456789012"
    existing = None
    from sqlalchemy import select
    result = await session.execute(select(User).where(User.aadhaar_hash == hash_aadhaar(test_aadhaar)))
    existing = result.scalar_one_or_none()
    if existing:
        print("[SEED] Test user already exists")
        return existing

    user = User(
        aadhaar_hash=hash_aadhaar(test_aadhaar),
        swasth_id="SWA2025TEST0001",
        abha_number="12-3456-7890-1234",
        abha_address="testuser@abdm",
        full_name="Ramesh Kumar",
        date_of_birth=date(1960, 5, 15),
        gender="M",
        phone="9876543210",
        state="Tamil Nadu",
        district="Chennai",
        is_elder=True,
        role="elder",
    )
    session.add(user)
    await session.flush()

    policy = Policy(
        user_id=user.id,
        policy_number="PMJAY-TN-2025-001",
        policy_type="pmjay",
        insurer_name="National Health Authority",
        scheme_name="Ayushman Bharat PMJAY",
        coverage_amount=Decimal("500000"),
        sum_insured_remaining=Decimal("500000"),
        valid_from=date(2025, 1, 1),
        valid_until=date(2025, 12, 31),
    )
    session.add(policy)

    policy2 = Policy(
        user_id=user.id,
        policy_number="STAR-COMP-100234",
        policy_type="private",
        insurer_name="Star Health Insurance",
        scheme_name="Family Health Optima",
        coverage_amount=Decimal("1000000"),
        sum_insured_remaining=Decimal("800000"),
        valid_from=date(2025, 1, 1),
        valid_until=date(2026, 1, 1),
        tpa_name="Vidal Health TPA",
        tpa_code="VHTPA",
        tpa_phone="1800-200-1234",
    )
    session.add(policy2)

    print("[SEED] Created test user with 2 policies")
    return user


async def run_seed():
    """Execute all seed operations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await seed_hospitals(session)
        await seed_test_user(session)
        await session.commit()
    print("[SEED] Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(run_seed())
