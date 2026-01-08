"""User schemas"""
from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import Optional
from datetime import datetime


class RoleEnum(str, Enum):
    """User role enumeration"""
    user = "user"
    group_admin = "group_admin"


class UserCreate(BaseModel):
    """User creation schema"""
    name: str
    phone_number: str
    email: Optional[str] = None
    role: RoleEnum


class UserOut(BaseModel):
    """User output schema"""
    id: str
    name: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    role: RoleEnum
    avatar_url: Optional[str] = None
    card_number: Optional[str] = None
    card_holder_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pending_updates: Optional[list[str]] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """User update schema"""
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    card_number: Optional[str] = None
    card_holder_name: Optional[str] = None

