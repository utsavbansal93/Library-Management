"""Pydantic schemas for StoryArc endpoints."""

from __future__ import annotations

from typing import Optional, List, Any

from pydantic import BaseModel

from schemas.common import OrmBase, WorkBrief, VolumeRunBrief, ArcBrief


class ArcCreate(BaseModel):
    name: str
    parent_arc_id: Optional[str] = None
    total_parts: Optional[int] = None
    completion_status: Optional[str] = None
    description: Optional[str] = None


class ArcUpdate(BaseModel):
    name: Optional[str] = None
    parent_arc_id: Optional[str] = None
    total_parts: Optional[int] = None
    completion_status: Optional[str] = None
    description: Optional[str] = None


class ArcSummary(OrmBase):
    arc_id: str
    name: str
    total_parts: Optional[int] = None
    completion_status: Optional[str] = None
    parent_arc_id: Optional[str] = None
    description: Optional[str] = None


class WorkInArc(BaseModel):
    work: WorkBrief
    arc_position: Optional[int] = None
    volume_run: Optional[VolumeRunBrief] = None


class ArcDetail(ArcSummary):
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    works: List[WorkInArc] = []
    children: List[ArcBrief] = []


class ArcTree(ArcSummary):
    children: List[ArcTree] = []
