from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr

from app.models import DeviceStatus, UserRole, EventType


# ---------- Device ----------

class DeviceBase(BaseModel):
    manufacturer: str
    model: str
    serial_number: str
    department: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: DeviceStatus = DeviceStatus.in_service
    managed_by_vendor: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    department: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[DeviceStatus] = None
    managed_by_vendor: Optional[str] = None


class DeviceOut(DeviceBase):
    id: str
    last_patch_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Lifecycle Event ----------

class LifecycleEventCreate(BaseModel):
    event_type: EventType
    description: str
    source: Optional[str] = "manual"


class LifecycleEventOut(BaseModel):
    id: str
    device_id: str
    event_type: EventType
    description: str
    source: Optional[str]
    created_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


# ---------- User / Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.viewer


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
