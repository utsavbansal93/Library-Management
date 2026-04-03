"""Global search endpoint across all entity types."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from database import get_db
from models import Artifact, Work, Creator, Collection, StoryArc, VolumeRun, CreatorRole, TargetType
from schemas.search import SearchResults
from schemas.common import CreatorBrief, CollectionBrief, ArcBrief, VolumeRunBrief
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

    # --- Artifacts: match title OR publisher ---
    artifacts = (
        db.query(Artifact)
        .options(joinedload(Artifact.volume_run))
        .filter(
            or_(
                Artifact.title.ilike(pattern),
                Artifact.publisher.ilike(pattern),
            )
        )
        .limit(MAX_PER_TYPE)
        .all()
    )

    # Also find artifacts linked to creators matching the query
    found_artifact_ids = {a.artifact_id for a in artifacts}
    if len(artifacts) < MAX_PER_TYPE:
        creator_artifact_ids = (
            db.query(CreatorRole.target_id)
            .join(Creator, CreatorRole.creator_id == Creator.creator_id)
            .filter(
                CreatorRole.target_type == TargetType.ARTIFACT.value,
                or_(
                    Creator.display_name.ilike(pattern),
                    Creator.sort_name.ilike(pattern),
                ),
            )
            .limit(MAX_PER_TYPE)
            .all()
        )
        extra_ids = {r[0] for r in creator_artifact_ids} - found_artifact_ids
        if extra_ids:
            extra = (
                db.query(Artifact)
                .options(joinedload(Artifact.volume_run))
                .filter(Artifact.artifact_id.in_(extra_ids))
                .limit(MAX_PER_TYPE - len(artifacts))
                .all()
            )
            artifacts.extend(extra)

    # --- Works: match title ---
    works = (
        db.query(Work)
        .options(joinedload(Work.volume_run))
        .filter(Work.title.ilike(pattern))
        .limit(MAX_PER_TYPE)
        .all()
    )

    # Also find works linked to creators matching the query
    found_work_ids = {w.work_id for w in works}
    if len(works) < MAX_PER_TYPE:
        creator_work_ids = (
            db.query(CreatorRole.target_id)
            .join(Creator, CreatorRole.creator_id == Creator.creator_id)
            .filter(
                CreatorRole.target_type == TargetType.WORK.value,
                or_(
                    Creator.display_name.ilike(pattern),
                    Creator.sort_name.ilike(pattern),
                ),
            )
            .limit(MAX_PER_TYPE)
            .all()
        )
        extra_ids = {r[0] for r in creator_work_ids} - found_work_ids
        if extra_ids:
            extra = (
                db.query(Work)
                .options(joinedload(Work.volume_run))
                .filter(Work.work_id.in_(extra_ids))
                .limit(MAX_PER_TYPE - len(works))
                .all()
            )
            works.extend(extra)

    # --- Creators: match display_name, sort_name, first_name, last_name ---
    creators = (
        db.query(Creator)
        .filter(
            or_(
                Creator.display_name.ilike(pattern),
                Creator.sort_name.ilike(pattern),
                Creator.first_name.ilike(pattern),
                Creator.last_name.ilike(pattern),
            )
        )
        .limit(MAX_PER_TYPE)
        .all()
    )

    # --- Collections ---
    collections = (
        db.query(Collection)
        .filter(Collection.name.ilike(pattern))
        .limit(MAX_PER_TYPE)
        .all()
    )

    # --- Story Arcs ---
    arcs = (
        db.query(StoryArc)
        .filter(StoryArc.name.ilike(pattern))
        .limit(MAX_PER_TYPE)
        .all()
    )

    # --- Volume Runs (Series): match name or publisher ---
    volume_runs = (
        db.query(VolumeRun)
        .filter(
            or_(
                VolumeRun.name.ilike(pattern),
                VolumeRun.publisher.ilike(pattern),
            )
        )
        .limit(MAX_PER_TYPE)
        .all()
    )

    return SearchResults(
        artifacts=[ArtifactSummary.model_validate(a) for a in artifacts],
        works=[WorkSummary.model_validate(w) for w in works],
        creators=[CreatorBrief.model_validate(c) for c in creators],
        collections=[CollectionBrief.model_validate(c) for c in collections],
        arcs=[ArcBrief.model_validate(a) for a in arcs],
        volume_runs=[VolumeRunBrief.model_validate(vr) for vr in volume_runs],
    )
