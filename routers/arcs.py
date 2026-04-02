"""Story Arc CRUD endpoints with tree view and cross-volume reading order."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import StoryArc, WorkArcMembership, Work, _uuid
from schemas.arcs import (
    ArcCreate, ArcUpdate, ArcSummary, ArcDetail,
    ArcTree, WorkInArc,
)
from schemas.common import WorkBrief, VolumeRunBrief, ArcBrief

router = APIRouter(tags=["arcs"])


def _build_arc_tree(arcs: List[StoryArc]) -> List[dict]:
    """Build hierarchical tree from flat list of arcs."""
    by_id = {}
    for a in arcs:
        by_id[a.arc_id] = {
            "arc_id": a.arc_id,
            "name": a.name,
            "total_parts": a.total_parts,
            "completion_status": a.completion_status,
            "parent_arc_id": a.parent_arc_id,
            "description": a.description,
            "children": [],
        }

    roots = []
    for a in arcs:
        node = by_id[a.arc_id]
        if a.parent_arc_id and a.parent_arc_id in by_id:
            by_id[a.parent_arc_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


@router.get("/arcs")
def list_arcs(
    tree: bool = Query(False),
    db: Session = Depends(get_db),
):
    all_arcs = db.query(StoryArc).order_by(StoryArc.name).all()
    if tree:
        return _build_arc_tree(all_arcs)
    return [ArcSummary.model_validate(a) for a in all_arcs]


@router.get("/arcs/{arc_id}", response_model=ArcDetail)
def get_arc(arc_id: str, db: Session = Depends(get_db)):
    arc = db.query(StoryArc).filter(StoryArc.arc_id == arc_id).first()
    if not arc:
        raise HTTPException(404, "Story arc not found")

    # Get works in reading order with their volume runs
    memberships = (
        db.query(WorkArcMembership)
        .options(
            joinedload(WorkArcMembership.work).joinedload(Work.volume_run),
        )
        .filter(WorkArcMembership.arc_id == arc_id)
        .order_by(WorkArcMembership.arc_position)
        .all()
    )

    works = []
    for m in memberships:
        w = m.work
        works.append(WorkInArc(
            work=WorkBrief.model_validate(w),
            arc_position=m.arc_position,
            volume_run=(
                VolumeRunBrief.model_validate(w.volume_run)
                if w.volume_run else None
            ),
        ))

    # Get direct child arcs
    children = (
        db.query(StoryArc)
        .filter(StoryArc.parent_arc_id == arc_id)
        .order_by(StoryArc.name)
        .all()
    )

    return ArcDetail(
        arc_id=arc.arc_id,
        name=arc.name,
        total_parts=arc.total_parts,
        completion_status=arc.completion_status,
        parent_arc_id=arc.parent_arc_id,
        description=arc.description,
        created_at=str(arc.created_at) if arc.created_at else None,
        updated_at=str(arc.updated_at) if arc.updated_at else None,
        works=works,
        children=[ArcBrief.model_validate(c) for c in children],
    )


@router.post("/arcs", response_model=ArcSummary, status_code=201)
def create_arc(body: ArcCreate, db: Session = Depends(get_db)):
    arc = StoryArc(arc_id=_uuid(), **body.model_dump())
    db.add(arc)
    db.commit()
    db.refresh(arc)
    return arc


@router.put("/arcs/{arc_id}", response_model=ArcSummary)
def update_arc(
    arc_id: str, body: ArcUpdate, db: Session = Depends(get_db),
):
    arc = db.query(StoryArc).filter(StoryArc.arc_id == arc_id).first()
    if not arc:
        raise HTTPException(404, "Story arc not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(arc, field, value)
    db.commit()
    db.refresh(arc)
    return arc
