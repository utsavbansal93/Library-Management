"""Global search endpoint across all entity types."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Artifact, Work, Creator, Collection, StoryArc
from schemas.search import SearchResults
from schemas.common import CreatorBrief, CollectionBrief, ArcBrief
from schemas.artifacts import ArtifactSummary
from schemas.works import WorkSummary

router = APIRouter(tags=["search"])

MAX_PER_TYPE = 20


@router.get("/search", response_model=SearchResults)
def global_search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    pattern = f"%{q}%"

    artifacts = (
        db.query(Artifact)
        .options(joinedload(Artifact.volume_run))
        .filter(Artifact.title.ilike(pattern))
        .limit(MAX_PER_TYPE)
        .all()
    )

    works = (
        db.query(Work)
        .options(joinedload(Work.volume_run))
        .filter(Work.title.ilike(pattern))
        .limit(MAX_PER_TYPE)
        .all()
    )

    creators = (
        db.query(Creator)
        .filter(
            (Creator.display_name.ilike(pattern))
            | (Creator.sort_name.ilike(pattern))
        )
        .limit(MAX_PER_TYPE)
        .all()
    )

    collections = (
        db.query(Collection)
        .filter(Collection.name.ilike(pattern))
        .limit(MAX_PER_TYPE)
        .all()
    )

    arcs = (
        db.query(StoryArc)
        .filter(StoryArc.name.ilike(pattern))
        .limit(MAX_PER_TYPE)
        .all()
    )

    return SearchResults(
        artifacts=[ArtifactSummary.model_validate(a) for a in artifacts],
        works=[WorkSummary.model_validate(w) for w in works],
        creators=[CreatorBrief.model_validate(c) for c in creators],
        collections=[CollectionBrief.model_validate(c) for c in collections],
        arcs=[ArcBrief.model_validate(a) for a in arcs],
    )
