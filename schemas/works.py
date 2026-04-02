"""Pydantic schemas for Work endpoints."""

from typing import Optional, List, Any

from pydantic import BaseModel

from schemas.common import (
    OrmBase, ArtifactWorkWithArtifact, WorkArcBrief,
    WorkCollectionBrief, VolumeRunBrief,
)


class WorkCreate(BaseModel):
    title: str
    work_type: str
    original_publication_year: Optional[int] = None
    volume_run_id: Optional[str] = None
    issue_number: Optional[str] = None
    subject_tags: Optional[List[str]] = None
    is_narrative_nonfiction: Optional[bool] = None
    is_coffee_table_book: Optional[bool] = None
    goodreads_url: Optional[str] = None
    comicvine_url: Optional[str] = None
    notes: Optional[str] = None


class WorkUpdate(BaseModel):
    title: Optional[str] = None
    work_type: Optional[str] = None
    original_publication_year: Optional[int] = None
    volume_run_id: Optional[str] = None
    issue_number: Optional[str] = None
    subject_tags: Optional[List[str]] = None
    is_narrative_nonfiction: Optional[bool] = None
    is_coffee_table_book: Optional[bool] = None
    goodreads_url: Optional[str] = None
    comicvine_url: Optional[str] = None
    notes: Optional[str] = None


class WorkSummary(OrmBase):
    work_id: str
    title: str
    work_type: str
    original_publication_year: Optional[int] = None
    issue_number: Optional[str] = None
    volume_run: Optional[VolumeRunBrief] = None


class WorkDetail(OrmBase):
    work_id: str
    title: str
    work_type: str
    original_publication_year: Optional[int] = None
    volume_run_id: Optional[str] = None
    issue_number: Optional[str] = None
    subject_tags: Optional[List[str]] = None
    is_narrative_nonfiction: Optional[bool] = None
    is_coffee_table_book: Optional[bool] = None
    goodreads_url: Optional[str] = None
    comicvine_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    volume_run: Optional[VolumeRunBrief] = None
    artifact_works: List[ArtifactWorkWithArtifact] = []
    arc_memberships: List[WorkArcBrief] = []
    work_collections: List[WorkCollectionBrief] = []
    creators: List[Any] = []
