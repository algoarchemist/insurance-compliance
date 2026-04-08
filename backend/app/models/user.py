"""User SQLAlchemy model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aadhaar_hash = Column(String(64), unique=True, nullable=False)
    swasth_id = Column(String(20), unique=True, nullable=False)
    abha_number = Column(String(17), nullable=True)
    abha_address = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=True)
    phone = Column(String(15), unique=True, nullable=False)
    state = Column(String(50), nullable=True)
    district = Column(String(100), nullable=True)
    address_json = Column(JSONB, nullable=True)
    is_elder = Column(Boolean, default=False)
    preferred_lang = Column(String(10), default="en")
    accessibility_prefs = Column(JSONB, nullable=True)
    role = Column(String(20), default="user")  # user, elder, caregiver, hospital_admin, tpa_officer, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    policies = relationship("Policy", back_populates="user", lazy="selectin")
    claims = relationship("Claim", back_populates="user", foreign_keys="Claim.user_id", lazy="selectin")
    bank_accounts = relationship("BankAccount", back_populates="user", lazy="selectin")
    elder_caregivers = relationship("Caregiver", foreign_keys="Caregiver.elder_id", back_populates="elder", lazy="selectin")
    caregiver_relations = relationship("Caregiver", foreign_keys="Caregiver.caregiver_id", back_populates="caregiver", lazy="selectin")
