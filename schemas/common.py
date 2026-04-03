"""Shared Pydantic schemas used across multiple routers."""

from typing import Optional, List, Any

from pydantic import BaseModel, ConfigDict


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Brief / summary schemas for nested references ---

class CreatorBrief(OrmBase):
    creator_id: str
    display_name: str
    sort_name: str


class CreatorRoleBrief(OrmBase):
    id: str
    creator_id: str
    role: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    target_title: Optional[str] = None
    notes: Optional[str] = None
    creator: Optional[CreatorBrief] = None


class WorkBrief(OrmBase):
    work_id: str
    title: str
    work_type: str
    issue_number: Optional[str] = None


class ArtifactBrief(OrmBase):
    artifact_id: str
    title: str
    format: str
    publisher: Optional[str] = None


class CollectionBrief(OrmBase):
    collection_id: str
    name: str
    collection_type: str


class ArcBrief(OrmBase):
    arc_id: str
    name: str
    total_parts: Optional[int] = None
    completion_status: Optional[str] = None


class VolumeRunBrief(OrmBase):
    volume_run_id: str
    name: str
    publisher: str


class CopyBrief(OrmBase):
    copy_id: str
    copy_number: int
    location: Optional[str] = None
    borrower_name: Optional[str] = None
    lent_date: Optional[Any] = None


class ArtifactWorkBrief(OrmBase):
    id: str
    work_id: str
    position: int
    is_partial: bool
    collects_note: Optional[str] = None
    work: Optional[WorkBrief] = None


class ArtifactWorkWithArtifact(OrmBase):
    id: str
    artifact_id: str
    position: int
    is_partial: bool
    collects_note: Optional[str] = None
    artifact: Optional[ArtifactBrief] = None


class WorkArcBrief(OrmBase):
    id: str
    arc_id: str
    arc_position: Optional[int] = None
    arc: Optional[ArcBrief] = None


class WorkCollectionBrief(OrmBase):
    id: str
    collection_id: str
    sequence_number: Optional[float] = None
    collection: Optional[CollectionBrief] = None


class WorkCreatorBrief(BaseModel):
    display_name: str
    role: str


class WorkArcMembershipBrief(BaseModel):
    arc_id: str
    name: Optional[str] = None
    arc_position: Optional[int] = None


class WorkCollectionMembershipBrief(BaseModel):
    collection_id: str
    name: Optional[str] = None
    sequence_number: Optional[float] = None


class MessageResponse(BaseModel):
    detail: str
