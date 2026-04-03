"""Pydantic schemas for global search endpoint."""

from typing import List

from pydantic import BaseModel

from schemas.common import CreatorBrief, CollectionBrief, ArcBrief, VolumeRunBrief
from schemas.artifacts import ArtifactSummary
from schemas.works import WorkSummary


class SearchResults(BaseModel):
    artifacts: List[ArtifactSummary] = []
    works: List[WorkSummary] = []
    creators: List[CreatorBrief] = []
    collections: List[CollectionBrief] = []
    arcs: List[ArcBrief] = []
    volume_runs: List[VolumeRunBrief] = []
