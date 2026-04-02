"""Artifact CRUD + copy creation endpoints."""

from typing import Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Artifact, ArtifactWork, Copy, CreatorRole, TargetType, _uuid

BASE_DIR = Path(__file__).resolve().parent.parent
from schemas.artifacts import (
    ArtifactCreate, ArtifactUpdate, ArtifactSummary, ArtifactDetail,
    CopyCreate, CopyDetail,
)
from schemas.common import CreatorRoleBrief

router = APIRouter(tags=["artifacts"])


def _get_artifact_creators(db: Session, artifact_id: str) -> List[dict]:
    """Get creators for an artifact via polymorphic CreatorRole table."""
    roles = (
        db.query(CreatorRole)
        .options(joinedload(CreatorRole.creator))
        .filter(
            CreatorRole.target_type == TargetType.ARTIFACT.value,
            CreatorRole.target_id == artifact_id,
        )
        .all()
    )
    return [
        CreatorRoleBrief.model_validate(r).model_dump()
        for r in roles
    ]


@router.get("/artifacts", response_model=List[ArtifactSummary])
def list_artifacts(
    format: Optional[str] = Query(None),
    publisher: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Artifact).filter(Artifact.deleted_at.is_(None))
    if format:
        query = query.filter(Artifact.format == format)
    if publisher:
        query = query.filter(Artifact.publisher.ilike(f"%{publisher}%"))
    if owner:
        query = query.filter(Artifact.owner == owner)
    if location:
        query = query.join(Copy).filter(Copy.location == location)
    if q:
        query = query.filter(Artifact.title.ilike(f"%{q}%"))
    return (
        query.options(joinedload(Artifact.volume_run))
        .order_by(Artifact.title)
        .offset(offset).limit(limit)
        .all()
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDetail)
def get_artifact(artifact_id: str, db: Session = Depends(get_db)):
    artifact = (
        db.query(Artifact)
        .options(
            joinedload(Artifact.volume_run),
            joinedload(Artifact.artifact_works).joinedload(ArtifactWork.work),
            joinedload(Artifact.copies),
        )
        .filter(
            Artifact.artifact_id == artifact_id,
            Artifact.deleted_at.is_(None),
        )
        .first()
    )
    if not artifact:
        raise HTTPException(404, "Artifact not found")

    result = ArtifactDetail.model_validate(artifact)
    result.creators = _get_artifact_creators(db, artifact_id)
    return result


@router.post("/artifacts", response_model=ArtifactSummary, status_code=201)
def create_artifact(body: ArtifactCreate, db: Session = Depends(get_db)):
    data = body.model_dump()
    artifact = Artifact(artifact_id=_uuid(), **data)
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.put("/artifacts/{artifact_id}", response_model=ArtifactSummary)
def update_artifact(
    artifact_id: str, body: ArtifactUpdate, db: Session = Depends(get_db),
):
    artifact = (
        db.query(Artifact)
        .filter(
            Artifact.artifact_id == artifact_id,
            Artifact.deleted_at.is_(None),
        )
        .first()
    )
    if not artifact:
        raise HTTPException(404, "Artifact not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(artifact, field, value)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.delete("/artifacts/{artifact_id}", status_code=204)
def delete_artifact(artifact_id: str, db: Session = Depends(get_db)):
    artifact = (
        db.query(Artifact)
        .filter(
            Artifact.artifact_id == artifact_id,
            Artifact.deleted_at.is_(None),
        )
        .first()
    )
    if not artifact:
        raise HTTPException(404, "Artifact not found")
    artifact.deleted_at = datetime.utcnow()
    db.commit()


@router.post(
    "/artifacts/{artifact_id}/copies",
    response_model=CopyDetail,
    status_code=201,
)
def create_copy(
    artifact_id: str, body: CopyCreate, db: Session = Depends(get_db),
):
    artifact = (
        db.query(Artifact)
        .filter(
            Artifact.artifact_id == artifact_id,
            Artifact.deleted_at.is_(None),
        )
        .first()
    )
    if not artifact:
        raise HTTPException(404, "Artifact not found")
    copy = Copy(
        copy_id=_uuid(),
        artifact_id=artifact_id,
        **body.model_dump(),
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


def _generate_placeholder_svg(title: str) -> str:
    """Generate a book-spine style SVG placeholder for artifacts without covers."""
    import html
    safe_title = html.escape(title)
    # Split long titles into lines (~20 chars each)
    words = safe_title.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > 20 and current:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip() if current else word
    if current:
        lines.append(current)
    lines = lines[:6]  # max 6 lines

    y_start = 200 - (len(lines) * 14)
    text_elements = "\n".join(
        f'    <text x="150" y="{y_start + i * 28}" '
        f'font-family="Georgia, serif" font-size="16" '
        f'fill="#d4c5a9" text-anchor="middle">{line}</text>'
        for i, line in enumerate(lines)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="400" viewBox="0 0 300 400">
  <defs>
    <linearGradient id="spine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#2c1810"/>
      <stop offset="5%" stop-color="#4a3228"/>
      <stop offset="95%" stop-color="#4a3228"/>
      <stop offset="100%" stop-color="#2c1810"/>
    </linearGradient>
  </defs>
  <rect width="300" height="400" fill="url(#spine)" rx="4"/>
  <rect x="8" y="8" width="284" height="384" fill="none" stroke="#8b7355" stroke-width="1.5" rx="2"/>
  <rect x="14" y="14" width="272" height="372" fill="none" stroke="#8b7355" stroke-width="0.5" rx="1"/>
  <line x1="30" y1="100" x2="270" y2="100" stroke="#8b7355" stroke-width="0.8"/>
  <line x1="30" y1="300" x2="270" y2="300" stroke="#8b7355" stroke-width="0.8"/>
{text_elements}
</svg>'''


@router.get("/artifacts/{artifact_id}/cover")
def get_artifact_cover(artifact_id: str, db: Session = Depends(get_db)):
    artifact = (
        db.query(Artifact)
        .filter(Artifact.artifact_id == artifact_id, Artifact.deleted_at.is_(None))
        .first()
    )
    if not artifact:
        raise HTTPException(404, "Artifact not found")

    if artifact.cover_image_path:
        file_path = BASE_DIR / artifact.cover_image_path
        if file_path.is_file():
            return FileResponse(str(file_path), media_type="image/jpeg")

    # No cover image — return generated SVG placeholder
    svg = _generate_placeholder_svg(artifact.title)
    return Response(content=svg, media_type="image/svg+xml")
