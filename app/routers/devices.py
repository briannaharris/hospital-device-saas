from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=List[schemas.DeviceOut])
def list_devices(
    status: Optional[models.DeviceStatus] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Device)
    if status:
        query = query.filter(models.Device.status == status)
    if department:
        query = query.filter(models.Device.department == department)
    return query.order_by(models.Device.updated_at.desc()).all()


@router.post("", response_model=schemas.DeviceOut)
def create_device(
    device_in: schemas.DeviceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    existing = db.query(models.Device).filter(models.Device.serial_number == device_in.serial_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device with this serial number already exists")

    device = models.Device(**device_in.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)

    # Log the creation itself as the first lifecycle event
    event = models.LifecycleEvent(
        device_id=device.id,
        event_type=models.EventType.note,
        description="Device added to system of record.",
        source="manual",
        created_by=current_user.email,
    )
    db.add(event)
    db.commit()

    return device


@router.get("/{device_id}", response_model=schemas.DeviceOut)
def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch("/{device_id}", response_model=schemas.DeviceOut)
def update_device(
    device_id: str,
    device_in: schemas.DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    changes = device_in.model_dump(exclude_unset=True)
    old_status = device.status
    for field, value in changes.items():
        setattr(device, field, value)
    device.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(device)

    if "status" in changes and changes["status"] != old_status:
        event = models.LifecycleEvent(
            device_id=device.id,
            event_type=models.EventType.status_change,
            description=f"Status changed from {old_status} to {changes['status']}.",
            source="manual",
            created_by=current_user.email,
        )
        db.add(event)
        db.commit()

    return device


@router.get("/{device_id}/events", response_model=List[schemas.LifecycleEventOut])
def get_device_events(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return (
        db.query(models.LifecycleEvent)
        .filter(models.LifecycleEvent.device_id == device_id)
        .order_by(models.LifecycleEvent.created_at.desc())
        .all()
    )


@router.post("/{device_id}/events", response_model=schemas.LifecycleEventOut)
def add_device_event(
    device_id: str,
    event_in: schemas.LifecycleEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    event = models.LifecycleEvent(
        device_id=device_id,
        event_type=event_in.event_type,
        description=event_in.description,
        source=event_in.source,
        created_by=current_user.email,
    )
    db.add(event)

    if event_in.event_type == models.EventType.patch_applied:
        device.last_patch_date = datetime.utcnow()

    db.commit()
    db.refresh(event)
    return event
