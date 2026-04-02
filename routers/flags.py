"""Data Quality Flag endpoints."""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import DataQualityFlag, FlagStatus
from schemas.flags import FlagSummary, FlagUpdate

router = APIRouter(tags=["flags"])


@router.get("/flags", response_model=List[FlagSummary])
def list_flags(
    type: Optional[str] = Query(None, alias="type"),
    status: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(DataQualityFlag)
    if type:
        query = query.filter(DataQualityFlag.flag_type == type)
    if status:
        query = query.filter(DataQualityFlag.status == status)
    else:
        # Default to open flags
        query = query.filter(DataQualityFlag.status == FlagStatus.OPEN.value)
    return query.order_by(DataQualityFlag.created_at.desc()).limit(limit).all()


@router.put("/flags/{flag_id}", response_model=FlagSummary)
def update_flag(
    flag_id: str, body: FlagUpdate, db: Session = Depends(get_db),
):
    flag = (
        db.query(DataQualityFlag)
        .filter(DataQualityFlag.flag_id == flag_id)
        .first()
    )
    if not flag:
        raise HTTPException(404, "Flag not found")

    if body.action == "resolve":
        flag.status = FlagStatus.RESOLVED.value
        flag.resolved_at = datetime.utcnow()
        if body.applied_fix:
            flag.suggested_fix = body.applied_fix
    elif body.action == "dismiss":
        flag.status = FlagStatus.DISMISSED.value
        flag.resolved_at = datetime.utcnow()
    else:
        raise HTTPException(400, "Action must be 'resolve' or 'dismiss'")

    db.commit()
    db.refresh(flag)
    return flag
