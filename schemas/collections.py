"""Pydantic schemas for Collection endpoints."""

from __future__ import annotations

from typing import Optional, List, Any

from pydantic import BaseModel

from schemas.common import OrmBase, WorkBrief


class CollectionCreate(BaseModel):
    name: str
    collection_type: str
    parent_collection_id: Optional[str] = None
    description: Optional[str] = None


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    collection_type: Optional[str] = None
    parent_collection_id: Optional[str] = None
    description: Optional[str] = None


class CollectionSummary(OrmBase):
    collection_id: str
    name: str
    collection_type: str
    parent_collection_id: Optional[str] = None
    description: Optional[str] = None


class WorkInCollection(OrmBase):
    work: WorkBrief
    sequence_number: Optional[float] = None


class CollectionDetail(CollectionSummary):
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    works: List[WorkInCollection] = []
    children: List[CollectionSummary] = []


class CollectionTree(CollectionSummary):
    children: List[CollectionTree] = []
