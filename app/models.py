"""
Core data model.

Device        - the persistent system-of-record for a hospital's medical devices,
                independent of whichever biomed vendor currently manages them.
LifecycleEvent - append-only audit log of patch/remediation/status history.
                This is the record that stays with the hospital even when the
                vendor relationship ends.
User          - role-based access (security_admin can write, viewer is read-only).
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class DeviceStatus(str, enum.Enum):
    in_service = "in_service"
    in_repair = "in_repair"
    quarantined = "quarantined"
    retired = "retired"


class UserRole(str, enum.Enum):
    security_admin = "security_admin"
    viewer = "viewer"


class EventType(str, enum.Enum):
    patch_applied = "patch_applied"
    status_change = "status_change"
    reconciliation_flag = "reconciliation_flag"
    note = "note"


class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, default=gen_uuid)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    serial_number = Column(String, unique=True, nullable=False, index=True)
    department = Column(String, nullable=True)
    location = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.in_service, nullable=False)
    last_patch_date = Column(DateTime, nullable=True)
    managed_by_vendor = Column(String, nullable=True)  # e.g. "TriMedx", "Renovo", "in-house"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("LifecycleEvent", back_populates="device", cascade="all, delete-orphan")


class LifecycleEvent(Base):
    """
    Append-only log. Never update or delete rows here — this table IS the
    persistent record that survives vendor turnover. Corrections should be
    added as new events, not edits to old ones.
    """
    __tablename__ = "lifecycle_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String, nullable=True)  # e.g. "vendor_report", "network_scan", "manual"
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)  # user id/email

    device = relationship("Device", back_populates="events")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
