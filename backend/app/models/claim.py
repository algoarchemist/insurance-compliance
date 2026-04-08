"""Claim SQLAlchemy models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Numeric, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)
    claim_type = Column(String(20), nullable=False)  # cashless, reimbursement
    status = Column(String(30), nullable=False, default="draft")
    nhcx_claim_id = Column(String(200), nullable=True)
    nhcx_pre_auth_id = Column(String(200), nullable=True)
    pre_auth_reference = Column(String(200), nullable=True)
    claim_amount = Column(Numeric(12, 2), nullable=True)
    approved_amount = Column(Numeric(12, 2), nullable=True)
    settled_amount = Column(Numeric(12, 2), nullable=True)
    fhir_bundle = Column(JSONB, nullable=True)
    rejection_code = Column(String(50), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    ai_rejection_explanation = Column(Text, nullable=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=True)
    documents = Column(JSONB, nullable=True)
    ocr_extracted = Column(JSONB, nullable=True)
    gap_alerts = Column(JSONB, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="claims", foreign_keys=[user_id])
    policy = relationship("Policy", back_populates="claims")
    hospital = relationship("Hospital", back_populates="claims")
    bank_account = relationship("BankAccount")
    submitter = relationship("User", foreign_keys=[submitted_by])
    status_history = relationship("ClaimStatusHistory", back_populates="claim", lazy="selectin", order_by="ClaimStatusHistory.created_at")


class ClaimStatusHistory(Base):
    __tablename__ = "claim_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    status = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)
    changed_by = Column(String(50), nullable=True)  # user, caregiver, nhcx, system
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    claim = relationship("Claim", back_populates="status_history")


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    account_number = Column(String(200), nullable=False)  # Stored encrypted
    ifsc_code = Column(String(15), nullable=False)
    bank_name = Column(String(200), nullable=True)
    account_holder = Column(String(200), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="bank_accounts")


from sqlalchemy import Boolean
