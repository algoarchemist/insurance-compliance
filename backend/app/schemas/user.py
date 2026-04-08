"""User Pydantic schemas."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    full_name: str
    date_of_birth: date
    gender: Optional[str] = None
    phone: str
    state: Optional[str] = None
    district: Optional[str] = None


class UserCreate(UserBase):
    aadhaar_hash: str
    swasth_id: str


class UserResponse(BaseModel):
    id: UUID
    swasth_id: str
    abha_number: Optional[str] = None
    abha_address: Optional[str] = None
    full_name: str
    date_of_birth: date
    gender: Optional[str] = None
    phone: str
    state: Optional[str] = None
    district: Optional[str] = None
    is_elder: bool = False
    preferred_lang: str = "en"
    accessibility_prefs: Optional[dict] = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    preferred_lang: Optional[str] = None
    accessibility_prefs: Optional[dict] = None
