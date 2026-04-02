"""Pydantic schemas for Creator endpoints."""

from typing import Optional, List, Any

from pydantic import BaseModel

from schemas.common import OrmBase, CreatorRoleBrief


class CreatorCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: str
    sort_name: str
    aliases: Optional[List[str]] = None


class CreatorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    sort_name: Optional[str] = None
    aliases: Optional[List[str]] = None


class CreatorSummary(OrmBase):
    creator_id: str
    display_name: str
    sort_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    aliases: Optional[List[str]] = None


class CreatorDetail(CreatorSummary):
    roles: List[CreatorRoleBrief] = []
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class CreatorMergeRequest(BaseModel):
    source_creator_id: str
    target_creator_id: str


class CreatorMergeResponse(OrmBase):
    merged_creator: CreatorSummary
    roles_transferred: int
