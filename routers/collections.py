"""Collection CRUD endpoints with tree view support."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Collection, WorkCollection, ArtifactWork, _uuid
from schemas.collections import (
    CollectionCreate, CollectionUpdate, CollectionSummary,
    CollectionDetail, CollectionTree, WorkInCollection,
)
from schemas.common import WorkBrief

router = APIRouter(tags=["collections"])


def _build_tree(
    collections: List[Collection],
) -> List[dict]:
    """Build hierarchical tree from flat list of collections."""
    by_id = {}
    for c in collections:
        by_id[c.collection_id] = {
            "collection_id": c.collection_id,
            "name": c.name,
            "collection_type": c.collection_type,
            "parent_collection_id": c.parent_collection_id,
            "description": c.description,
            "children": [],
        }

    roots = []
    for c in collections:
        node = by_id[c.collection_id]
        if c.parent_collection_id and c.parent_collection_id in by_id:
            by_id[c.parent_collection_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


@router.get("/collections")
def list_collections(
    tree: bool = Query(False),
    db: Session = Depends(get_db),
):
    all_collections = db.query(Collection).order_by(Collection.name).all()
    if tree:
        return _build_tree(all_collections)
    return [CollectionSummary.model_validate(c) for c in all_collections]


@router.get("/collections/{collection_id}", response_model=CollectionDetail)
def get_collection(collection_id: str, db: Session = Depends(get_db)):
    coll = (
        db.query(Collection)
        .filter(Collection.collection_id == collection_id)
        .first()
    )
    if not coll:
        raise HTTPException(404, "Collection not found")

    # Get works in this collection
    wc_rows = (
        db.query(WorkCollection)
        .options(joinedload(WorkCollection.work))
        .filter(WorkCollection.collection_id == collection_id)
        .order_by(WorkCollection.sequence_number)
        .all()
    )
    # Count artifacts per work in one query
    work_ids = [wc.work.work_id for wc in wc_rows]
    artifact_counts = {}
    if work_ids:
        counts = (
            db.query(ArtifactWork.work_id, func.count(ArtifactWork.id))
            .filter(ArtifactWork.work_id.in_(work_ids))
            .group_by(ArtifactWork.work_id)
            .all()
        )
        artifact_counts = {wid: cnt for wid, cnt in counts}

    works = [
        WorkInCollection(
            work=WorkBrief.model_validate(wc.work),
            sequence_number=wc.sequence_number,
            artifact_count=artifact_counts.get(wc.work.work_id, 0),
        )
        for wc in wc_rows
    ]

    # Get direct children
    children = (
        db.query(Collection)
        .filter(Collection.parent_collection_id == collection_id)
        .order_by(Collection.name)
        .all()
    )

    return CollectionDetail(
        collection_id=coll.collection_id,
        name=coll.name,
        collection_type=coll.collection_type,
        parent_collection_id=coll.parent_collection_id,
        description=coll.description,
        created_at=str(coll.created_at) if coll.created_at else None,
        updated_at=str(coll.updated_at) if coll.updated_at else None,
        works=works,
        children=[CollectionSummary.model_validate(c) for c in children],
    )


@router.post("/collections", response_model=CollectionSummary, status_code=201)
def create_collection(body: CollectionCreate, db: Session = Depends(get_db)):
    coll = Collection(collection_id=_uuid(), **body.model_dump())
    db.add(coll)
    db.commit()
    db.refresh(coll)
    return coll


@router.put("/collections/{collection_id}", response_model=CollectionSummary)
def update_collection(
    collection_id: str, body: CollectionUpdate, db: Session = Depends(get_db),
):
    coll = (
        db.query(Collection)
        .filter(Collection.collection_id == collection_id)
        .first()
    )
    if not coll:
        raise HTTPException(404, "Collection not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(coll, field, value)
    db.commit()
    db.refresh(coll)
    return coll
