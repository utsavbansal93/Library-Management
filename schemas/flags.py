"""Pydantic schemas for DataQualityFlag endpoints."""

from typing import Optional, Any

from pydantic import BaseModel

from schemas.common import OrmBase


class FlagSummary(OrmBase):
    flag_id: str
    entity_type: str
    entity_id: str
    flag_type: str
    description: str
    suggested_fix: Optional[str] = None
    status: str
    created_at: Optional[Any] = None
    resolved_at: Optional[Any] = None


class FlagUpdate(BaseModel):
    action: str  # "resolve" or "dismiss"
    applied_fix: Optional[str] = None
