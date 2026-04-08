"""Caregiver SQLAlchemy model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Caregiver(Base):
    __tablename__ = "caregivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    elder_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending, active, revoked
    invited_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("elder_id", "caregiver_id"),)

    # Relationships
    elder = relationship("User", foreign_keys=[elder_id], back_populates="elder_caregivers")
    caregiver = relationship("User", foreign_keys=[caregiver_id], back_populates="caregiver_relations")
