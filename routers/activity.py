"""Activity Ledger endpoints with automatic reading_status cache updates."""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import ActivityLedger, Work, _uuid
from schemas.activity import ActivityCreate, ActivityEntry, ReadingStatusResponse
from services.activity import update_reading_status

router = APIRouter(tags=["activity"])


@router.post("/activity", response_model=ActivityEntry, status_code=201)
def log_activity(body: ActivityCreate, db: Session = Depends(get_db)):
    # Verify work exists
    work = db.query(Work).filter(
        Work.work_id == body.work_id,
    ).first()
    if not work:
        raise HTTPException(404, "Work not found")

    ts = datetime.fromisoformat(body.timestamp)

    entry = ActivityLedger(
        log_id=_uuid(),
        user_profile=body.user_profile,
        work_id=body.work_id,
        event_type=body.event_type,
        event_value=body.event_value,
        timestamp=ts,
    )
    db.add(entry)

    # Auto-update reading_status cache in same transaction
    update_reading_status(
        db,
        user_profile=body.user_profile,
        work_id=body.work_id,
        event_type=body.event_type,
        event_value=body.event_value,
        timestamp=ts,
    )

    db.commit()
    db.refresh(entry)
    return entry


@router.get("/activity", response_model=List[ActivityEntry])
def list_activity(
    work_id: Optional[str] = Query(None),
    profile: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(ActivityLedger).options(
        joinedload(ActivityLedger.work),
    )
    if work_id:
        query = query.filter(ActivityLedger.work_id == work_id)
    if profile:
        query = query.filter(ActivityLedger.user_profile == profile)
    return (
        query.order_by(ActivityLedger.timestamp.desc())
        .limit(limit)
        .all()
    )
