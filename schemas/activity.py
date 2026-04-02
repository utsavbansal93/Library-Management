"""Pydantic schemas for Activity Ledger endpoints."""

from typing import Optional, Any

from pydantic import BaseModel

from schemas.common import OrmBase, WorkBrief


class ActivityCreate(BaseModel):
    user_profile: str
    work_id: str
    event_type: str
    event_value: Optional[str] = None
    timestamp: str  # ISO format datetime


class ActivityEntry(OrmBase):
    log_id: str
    user_profile: str
    work_id: str
    event_type: str
    event_value: Optional[str] = None
    timestamp: Any
    work: Optional[WorkBrief] = None


class ReadingStatusResponse(OrmBase):
    id: str
    user_profile: str
    work_id: str
    status: str
    current_rating: Optional[float] = None
    last_event_at: Optional[Any] = None
