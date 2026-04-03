"""Creator CRUD + merge/deduplication endpoint."""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Creator, CreatorRole, TargetType, Work, Artifact, _uuid
from schemas.creators import (
    CreatorCreate, CreatorUpdate, CreatorSummary, CreatorDetail,
    CreatorMergeRequest, CreatorMergeResponse,
)
from schemas.common import CreatorRoleBrief, CreatorBrief
from services.creators import merge_creators

router = APIRouter(tags=["creators"])


@router.get("/creators", response_model=List[CreatorSummary])
def list_creators(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Creator)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            (Creator.display_name.ilike(pattern))
            | (Creator.sort_name.ilike(pattern))
        )
    return query.order_by(Creator.sort_name).limit(200).all()


@router.get("/creators/{creator_id}", response_model=CreatorDetail)
def get_creator(creator_id: str, db: Session = Depends(get_db)):
    creator = db.query(Creator).filter(Creator.creator_id == creator_id).first()
    if not creator:
        raise HTTPException(404, "Creator not found")

    result = CreatorDetail.model_validate(creator)
    # Enrich roles with target titles
    for role in result.roles:
        if role.target_type == TargetType.WORK.value:
            work = db.query(Work).filter(Work.work_id == role.target_id).first()
            role.target_title = work.title if work else None
        elif role.target_type == TargetType.ARTIFACT.value:
            artifact = db.query(Artifact).filter(Artifact.artifact_id == role.target_id).first()
            role.target_title = artifact.title if artifact else None
    return result


@router.post("/creators", response_model=CreatorSummary, status_code=201)
def create_creator(body: CreatorCreate, db: Session = Depends(get_db)):
    creator = Creator(
        creator_id=_uuid(),
        first_name=body.first_name,
        last_name=body.last_name,
        display_name=body.display_name,
        sort_name=body.sort_name,
        aliases=body.aliases,
    )
    db.add(creator)
    db.commit()
    db.refresh(creator)
    return creator


@router.put("/creators/{creator_id}", response_model=CreatorSummary)
def update_creator(
    creator_id: str, body: CreatorUpdate, db: Session = Depends(get_db),
):
    creator = db.query(Creator).filter(Creator.creator_id == creator_id).first()
    if not creator:
        raise HTTPException(404, "Creator not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(creator, field, value)
    db.commit()
    db.refresh(creator)
    return creator


@router.post("/creators/merge", response_model=CreatorMergeResponse)
def merge_creator_endpoint(
    body: CreatorMergeRequest, db: Session = Depends(get_db),
):
    try:
        target, roles_transferred = merge_creators(
            db, body.source_creator_id, body.target_creator_id,
        )
        db.commit()
        db.refresh(target)
    except ValueError as e:
        raise HTTPException(404, str(e))

    return CreatorMergeResponse(
        merged_creator=CreatorSummary.model_validate(target),
        roles_transferred=roles_transferred,
    )
