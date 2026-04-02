"""Pydantic schemas for global search endpoint."""

from typing import List

from pydantic import BaseModel

from schemas.common import (
    ArtifactBrief, WorkBrief, CreatorBrief, CollectionBrief, ArcBrief,
)


class SearchResults(BaseModel):
    artifacts: List[ArtifactBrief] = []
    works: List[WorkBrief] = []
    creators: List[CreatorBrief] = []
    collections: List[CollectionBrief] = []
    arcs: List[ArcBrief] = []
