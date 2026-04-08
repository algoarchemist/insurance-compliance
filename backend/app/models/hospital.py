"""Hospital SQLAlchemy models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Numeric, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nhcx_provider_id = Column(String(100), unique=True, nullable=True)
    name = Column(String(300), nullable=False)
    type = Column(String(20), nullable=False)  # government, private, trust
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    district = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    lat = Column(Numeric(10, 7), nullable=True)
    lng = Column(Numeric(10, 7), nullable=True)
    phone = Column(String(20), nullable=True)
    empanelment_type = Column(String(30), nullable=True)  # cashless, reimbursement, both
    tpa_codes = Column(ARRAY(String), nullable=True)
    specialities = Column(ARRAY(String), nullable=True)
    services_covered = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    coverage_mappings = relationship("HospitalPolicyCoverage", back_populates="hospital", lazy="selectin")
    claims = relationship("Claim", back_populates="hospital", lazy="selectin")


class HospitalPolicyCoverage(Base):
    __tablename__ = "hospital_policy_coverage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    policy_type = Column(String(30), nullable=True)
    tpa_code = Column(String(50), nullable=True)
    services = Column(JSONB, nullable=False)
    sub_limits = Column(JSONB, nullable=True)
    last_verified = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    hospital = relationship("Hospital", back_populates="coverage_mappings")
