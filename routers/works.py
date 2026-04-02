"""Work CRUD endpoints."""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Work, ArtifactWork, Artifact, WorkArcMembership, StoryArc, WorkCollection, Collection, CreatorRole, TargetType, _uuid
from schemas.works import WorkCreate, WorkUpdate, WorkSummary, WorkDetail
from schemas.common import CreatorRoleBrief, CreatorBrief

router = APIRouter(tags=["works"])


def _get_work_creators(db: Session, work_id: str) -> List[dict]:
    """Get creators for a work via polymorphic CreatorRole table."""
    roles = (
        db.query(CreatorRole)
        .options(joinedload(CreatorRole.creator))
        .filter(
            CreatorRole.target_type == TargetType.WORK.value,
            CreatorRole.target_id == work_id,
        )
        .all()
    )
    return [
        CreatorRoleBrief.model_validate(r).model_dump()
        for r in roles
    ]


@router.get("/works", response_model=List[WorkSummary])
def list_works(
    work_type: Optional[str] = Query(None),
    collection: Optional[str] = Query(None),
    arc: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Work).filter(Work.deleted_at.is_(None))
    if work_type:
        query = query.filter(Work.work_type == work_type)
    if collection:
        from models import WorkCollection
        query = query.join(WorkCollection).filter(
            WorkCollection.collection_id == collection,
        )
    if arc:
        from models import WorkArcMembership
        query = query.join(WorkArcMembership).filter(
            WorkArcMembership.arc_id == arc,
        )
    if q:
        query = query.filter(Work.title.ilike(f"%{q}%"))
    return (
        query.options(joinedload(Work.volume_run))
        .order_by(Work.title)
        .offset(offset).limit(limit)
        .all()
    )


@router.get("/works/{work_id}", response_model=WorkDetail)
def get_work(work_id: str, db: Session = Depends(get_db)):
    work = (
        db.query(Work)
        .options(
            joinedload(Work.volume_run),
            joinedload(Work.artifact_works).joinedload(ArtifactWork.artifact),
            joinedload(Work.arc_memberships).joinedload(WorkArcMembership.arc),
            joinedload(Work.work_collections).joinedload(WorkCollection.collection),
        )
        .filter(Work.work_id == work_id, Work.deleted_at.is_(None))
        .first()
    )
    if not work:
        raise HTTPException(404, "Work not found")

    result = WorkDetail.model_validate(work)
    result.creators = _get_work_creators(db, work_id)
    return result


@router.post("/works", response_model=WorkSummary, status_code=201)
def create_work(body: WorkCreate, db: Session = Depends(get_db)):
    work = Work(work_id=_uuid(), **body.model_dump())
    db.add(work)
    db.commit()
    db.refresh(work)
    return work


@router.put("/works/{work_id}", response_model=WorkSummary)
def update_work(
    work_id: str, body: WorkUpdate, db: Session = Depends(get_db),
):
    work = (
        db.query(Work)
        .filter(Work.work_id == work_id, Work.deleted_at.is_(None))
        .first()
    )
    if not work:
        raise HTTPException(404, "Work not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(work, field, value)
    db.commit()
    db.refresh(work)
    return work


@router.delete("/works/{work_id}", status_code=204)
def delete_work(work_id: str, db: Session = Depends(get_db)):
    work = (
        db.query(Work)
        .filter(Work.work_id == work_id, Work.deleted_at.is_(None))
        .first()
    )
    if not work:
        raise HTTPException(404, "Work not found")
    work.deleted_at = datetime.utcnow()
    db.commit()
