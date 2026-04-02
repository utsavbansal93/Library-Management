"""Pydantic schemas for Artifact endpoints."""

from typing import Optional, List, Any

from pydantic import BaseModel

from schemas.common import (
    OrmBase, ArtifactWorkBrief, CopyBrief, VolumeRunBrief,
)


class ArtifactCreate(BaseModel):
    title: str
    format: str
    publisher: Optional[str] = None
    edition_year: Optional[int] = None
    isbn_or_upc: Optional[str] = None
    is_reprint: bool = False
    original_publisher: Optional[str] = None
    date_added: Optional[Any] = None
    owner: str = "The Bansal Brothers"
    is_pirated: bool = False
    issue_number: Optional[str] = None
    volume_run_id: Optional[str] = None
    size: Optional[str] = None
    main_genre: Optional[str] = None
    sous_genre: Optional[str] = None
    goodreads_url: Optional[str] = None
    cover_image_path: Optional[str] = None
    notes: Optional[str] = None


class ArtifactUpdate(BaseModel):
    title: Optional[str] = None
    format: Optional[str] = None
    publisher: Optional[str] = None
    edition_year: Optional[int] = None
    isbn_or_upc: Optional[str] = None
    is_reprint: Optional[bool] = None
    original_publisher: Optional[str] = None
    date_added: Optional[Any] = None
    owner: Optional[str] = None
    is_pirated: Optional[bool] = None
    issue_number: Optional[str] = None
    volume_run_id: Optional[str] = None
    size: Optional[str] = None
    main_genre: Optional[str] = None
    sous_genre: Optional[str] = None
    goodreads_url: Optional[str] = None
    cover_image_path: Optional[str] = None
    notes: Optional[str] = None


class ArtifactSummary(OrmBase):
    artifact_id: str
    title: str
    format: str
    publisher: Optional[str] = None
    owner: Optional[str] = None
    issue_number: Optional[str] = None
    cover_image_path: Optional[str] = None
    volume_run: Optional[VolumeRunBrief] = None


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
    size: Optional[str] = None
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


class CopyCreate(BaseModel):
    copy_number: int = 1
    internal_sku: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None


class CopyDetail(OrmBase):
    copy_id: str
    artifact_id: str
    copy_number: int
    internal_sku: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    borrower_name: Optional[str] = None
    lent_date: Optional[Any] = None
    notes: Optional[str] = None
