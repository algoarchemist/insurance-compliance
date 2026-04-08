"""Policy SQLAlchemy model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_number = Column(String(100), nullable=True)
    policy_type = Column(String(30), nullable=False)  # pmjay, state_scheme, private, employer
    insurer_name = Column(String(200), nullable=False)
    scheme_name = Column(String(200), nullable=True)
    coverage_amount = Column(Numeric(12, 2), nullable=True)
    sum_insured_remaining = Column(Numeric(12, 2), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    tpa_name = Column(String(200), nullable=True)
    tpa_phone = Column(String(20), nullable=True)
    tpa_code = Column(String(50), nullable=True)
    state_code = Column(String(5), nullable=True)
    raw_data = Column(JSONB, nullable=True)
    abha_synced = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="policies")
    claims = relationship("Claim", back_populates="policy", lazy="selectin")
