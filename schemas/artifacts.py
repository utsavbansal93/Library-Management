"""Pydantic schemas for Artifact endpoints."""

from typing import Optional, List, Any

from pydantic import BaseModel, Field

from schemas.common import (
    OrmBase, ArtifactWorkBrief, CopyBrief, VolumeRunBrief,
    WorkCreatorBrief, WorkArcMembershipBrief, WorkCollectionMembershipBrief,
)


class ArtifactCreate(BaseModel):
    title: str = Field(..., max_length=255)
    format: str = Field(..., max_length=30)
    publisher: Optional[str] = Field(None, max_length=255)
    edition_year: Optional[int] = None
    isbn_or_upc: Optional[str] = Field(None, max_length=50)
    is_reprint: bool = False
    original_publisher: Optional[str] = Field(None, max_length=255)
    date_added: Optional[Any] = None
    owner: str = Field("The Bansal Brothers", max_length=30)
    is_pirated: bool = False
    issue_number: Optional[str] = Field(None, max_length=50)
    volume_run_id: Optional[str] = Field(None, max_length=36)
    main_genre: Optional[str] = Field(None, max_length=100)
    sous_genre: Optional[str] = Field(None, max_length=100)
    goodreads_url: Optional[str] = Field(None, max_length=500)
    cover_image_path: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)


class ArtifactUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    format: Optional[str] = Field(None, max_length=30)
    publisher: Optional[str] = Field(None, max_length=255)
    edition_year: Optional[int] = None
    isbn_or_upc: Optional[str] = Field(None, max_length=50)
    is_reprint: Optional[bool] = None
    original_publisher: Optional[str] = Field(None, max_length=255)
    date_added: Optional[Any] = None
    owner: Optional[str] = Field(None, max_length=30)
    is_pirated: Optional[bool] = None
    issue_number: Optional[str] = Field(None, max_length=50)
    volume_run_id: Optional[str] = Field(None, max_length=36)
    main_genre: Optional[str] = Field(None, max_length=100)
    sous_genre: Optional[str] = Field(None, max_length=100)
    goodreads_url: Optional[str] = Field(None, max_length=500)
    cover_image_path: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)


class ArtifactSummary(OrmBase):
    artifact_id: str
    title: str
    format: str
    publisher: Optional[str] = None
    owner: Optional[str] = None
    issue_number: Optional[str] = None
    is_reprint: bool = False
    original_publisher: Optional[str] = None
    is_lent: bool = False
    cover_image_path: Optional[str] = None
    volume_run: Optional[VolumeRunBrief] = None


class PaginatedArtifacts(BaseModel):
    items: List[ArtifactSummary]
    total: int


class ArtifactWorkEnriched(BaseModel):
    id: str
    work_id: str
    position: int
    is_partial: bool
    collects_note: Optional[str] = None
    title: str
    work_type: str
    issue_number: Optional[str] = None
    original_publication_year: Optional[int] = None
    subject_tags: Optional[List[str]] = None
    creators: List[WorkCreatorBrief] = []
    arc_memberships: List[WorkArcMembershipBrief] = []
    collection_memberships: List[WorkCollectionMembershipBrief] = []


class ArtifactArcMembership(BaseModel):
    arc_id: str
    name: Optional[str] = None
    arc_position: Optional[int] = None
    total_parts: Optional[int] = None
    completion_status: Optional[str] = None


class ArtifactCollectionMembership(BaseModel):
    collection_id: str
    name: Optional[str] = None
    collection_type: Optional[str] = None
    sequence_number: Optional[float] = None


class ArtifactDetail(OrmBase):
    artifact_id: str
    title: str
    format: str
    publisher: Optional[str] = None
    edition_year: Optional[int] = None
    isbn_or_upc: Optional[str] = None
    is_reprint: bool
    original_publisher: Optional[str] = None
    date_added: Optional[Any] = None
    owner: Optional[str] = None
    is_pirated: bool
    issue_number: Optional[str] = None
    volume_run_id: Optional[str] = None
    main_genre: Optional[str] = None
    sous_genre: Optional[str] = None
    goodreads_url: Optional[str] = None
    cover_image_path: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    volume_run: Optional[VolumeRunBrief] = None
    artifact_works: List[ArtifactWorkBrief] = []
    copies: List[CopyBrief] = []
    creators: List[Any] = []
    artifact_works_enriched: List[ArtifactWorkEnriched] = []
    arc_memberships: List[ArtifactArcMembership] = []
    collection_memberships: List[ArtifactCollectionMembership] = []


class CopyCreate(BaseModel):
    copy_number: int = 1
    internal_sku: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=2000)


class CopyUpdate(BaseModel):
    copy_number: Optional[int] = None
    internal_sku: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=20)
    borrower_name: Optional[str] = Field(None, max_length=255)
    lent_date: Optional[Any] = None
    notes: Optional[str] = Field(None, max_length=2000)


class CopyDetail(OrmBase):
    copy_id: str
    artifact_id: str
    copy_number: int
    internal_sku: Optional[str] = None
    location: Optional[str] = None
    borrower_name: Optional[str] = None
    lent_date: Optional[Any] = None
    notes: Optional[str] = None
