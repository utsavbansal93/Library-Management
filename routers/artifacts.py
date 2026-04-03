"""Artifact CRUD + copy creation endpoints."""

from typing import Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Artifact, ArtifactWork, Work, Copy, CreatorRole, TargetType, WorkArcMembership, StoryArc, WorkCollection, Collection, _uuid

BASE_DIR = Path(__file__).resolve().parent.parent
from schemas.artifacts import (
    ArtifactCreate, ArtifactUpdate, ArtifactSummary, ArtifactDetail,
    PaginatedArtifacts, CopyCreate, CopyDetail, CopyUpdate,
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


@router.get("/artifacts", response_model=PaginatedArtifacts)
def list_artifacts(
    format: Optional[str] = Query(None),
    publisher: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    volume_run_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    sort: Optional[str] = Query("title"),
    limit: int = Query(20, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Artifact)
    if format:
        query = query.filter(Artifact.format == format)
    if publisher:
        query = query.filter(Artifact.publisher.ilike(f"%{publisher}%"))
    if owner:
        query = query.filter(Artifact.owner == owner)
    if location:
        query = query.join(Copy).filter(Copy.location == location)
    if category:
        if category == "comics":
            query = query.filter(Artifact.format.in_(["Comic Issue", "Graphic Novel"]))
        elif category == "magazines":
            query = query.filter(Artifact.format == "Magazine")
        elif category == "novels":
            query = (
                query.join(ArtifactWork, Artifact.artifact_id == ArtifactWork.artifact_id)
                .join(Work, ArtifactWork.work_id == Work.work_id)
                .filter(Work.work_type == "Novel")
            )
        elif category == "nonfiction":
            query = (
                query.join(ArtifactWork, Artifact.artifact_id == ArtifactWork.artifact_id)
                .join(Work, ArtifactWork.work_id == Work.work_id)
                .filter(Work.work_type == "Non-fiction")
            )
    if volume_run_id:
        query = query.filter(Artifact.volume_run_id == volume_run_id)
    if q:
        query = query.filter(Artifact.title.ilike(f"%{q}%"))

    total = query.count()

    sort_map = {
        "title": Artifact.title.asc(),
        "date_added": Artifact.date_added.desc().nullslast(),
        "edition_year": Artifact.edition_year.desc().nullslast(),
    }
    order = sort_map.get(sort, Artifact.title.asc())

    items = (
        query.options(joinedload(Artifact.volume_run), joinedload(Artifact.copies))
        .order_by(order)
        .offset(offset).limit(limit)
        .all()
    )
    summaries = []
    for a in items:
        s = ArtifactSummary.model_validate(a)
        s.is_lent = any(c.location == "Lent" for c in a.copies)
        summaries.append(s)
    return PaginatedArtifacts(items=summaries, total=total)


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDetail)
def get_artifact(artifact_id: str, db: Session = Depends(get_db)):
    artifact = (
        db.query(Artifact)
        .options(
            joinedload(Artifact.volume_run),
            joinedload(Artifact.artifact_works).joinedload(ArtifactWork.work),
            joinedload(Artifact.copies),
        )
        .filter(Artifact.artifact_id == artifact_id)
        .first()
    )
    if not artifact:
        raise HTTPException(404, "Artifact not found")

    result = ArtifactDetail.model_validate(artifact)
    result.creators = _get_artifact_creators(db, artifact_id)

    # Gather arc & collection memberships for all linked works
    work_ids = [aw.work_id for aw in artifact.artifact_works if aw.work_id]
    if work_ids:
        arc_rows = (
            db.query(WorkArcMembership)
            .options(joinedload(WorkArcMembership.arc))
            .filter(WorkArcMembership.work_id.in_(work_ids))
            .all()
        )
        coll_rows = (
            db.query(WorkCollection)
            .options(joinedload(WorkCollection.collection))
            .filter(WorkCollection.work_id.in_(work_ids))
            .all()
        )
        # Deduplicate by arc/collection id (multiple works may share the same arc)
        seen_arcs: dict = {}
        for r in arc_rows:
            if r.arc_id not in seen_arcs:
                seen_arcs[r.arc_id] = {
                    "arc_id": r.arc_id,
                    "name": r.arc.name if r.arc else None,
                    "arc_position": r.arc_position,
                    "total_parts": r.arc.total_parts if r.arc else None,
                    "completion_status": r.arc.completion_status if r.arc else None,
                }
        seen_colls: dict = {}
        for r in coll_rows:
            if r.collection_id not in seen_colls:
                seen_colls[r.collection_id] = {
                    "collection_id": r.collection_id,
                    "name": r.collection.name if r.collection else None,
                    "collection_type": r.collection.collection_type if r.collection else None,
                    "sequence_number": r.sequence_number,
                }
        result.arc_memberships = list(seen_arcs.values())
        result.collection_memberships = list(seen_colls.values())

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
        .filter(Artifact.artifact_id == artifact_id)
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
        .filter(Artifact.artifact_id == artifact_id)
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
        .filter(Artifact.artifact_id == artifact_id)
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


@router.put(
    "/artifacts/{artifact_id}/copies/{copy_id}",
    response_model=CopyDetail,
)
def update_copy(
    artifact_id: str, copy_id: str, body: CopyUpdate, db: Session = Depends(get_db),
):
    artifact = (
        db.query(Artifact)
        .filter(Artifact.artifact_id == artifact_id)
        .first()
    )
    if not artifact:
        raise HTTPException(404, "Artifact not found")

    copy = db.query(Copy).filter(Copy.copy_id == copy_id, Copy.artifact_id == artifact_id).first()
    if not copy:
        raise HTTPException(404, "Copy not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(copy, field, value)

    db.commit()
    db.refresh(copy)
    return copy


def _placeholder_colors(fmt: str):
    """Return (bg_dark, bg_main, accent, text_fill) for format-specific placeholders."""
    f = fmt.lower() if fmt else ""
    if f in ("comic issue", "graphic novel"):
        return "#0d1b2a", "#1b3a5c", "#4a90d9", "#8bb8e8"
    elif f == "magazine":
        return "#2a0b0b", "#5c1a1a", "#d94a4a", "#e88b8b"
    elif f in ("kindle", "audible"):
        return "#0b1a0b", "#1a3c1a", "#4a8c4a", "#8bc88b"
    elif f in ("hardcover", "paperback"):
        return "#0f1a0b", "#1e3c1a", "#4a8c4a", "#8bc88b"
    return "#2c1810", "#4a3228", "#8b7355", "#d4c5a9"


def _generate_placeholder_svg(title: str, fmt: str = "") -> str:
    """Generate a book-spine style SVG placeholder for artifacts without covers."""
    import html
    safe_title = html.escape(title)
    bg_dark, bg_main, accent, text_fill = _placeholder_colors(fmt)

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
    lines = lines[:6]

    y_start = 200 - (len(lines) * 14)
    text_elements = "\n".join(
        f'    <text x="150" y="{y_start + i * 28}" '
        f'font-family="Georgia, serif" font-size="16" '
        f'fill="{text_fill}" text-anchor="middle">{line}</text>'
        for i, line in enumerate(lines)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="400" viewBox="0 0 300 400">
  <defs>
    <linearGradient id="spine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{bg_dark}"/>
      <stop offset="5%" stop-color="{bg_main}"/>
      <stop offset="95%" stop-color="{bg_main}"/>
      <stop offset="100%" stop-color="{bg_dark}"/>
    </linearGradient>
  </defs>
  <rect width="300" height="400" fill="url(#spine)" rx="4"/>
  <rect x="8" y="8" width="284" height="384" fill="none" stroke="{accent}" stroke-width="1.5" rx="2"/>
  <rect x="14" y="14" width="272" height="372" fill="none" stroke="{accent}" stroke-width="0.5" rx="1"/>
  <line x1="30" y1="100" x2="270" y2="100" stroke="{accent}" stroke-width="0.8"/>
  <line x1="30" y1="300" x2="270" y2="300" stroke="{accent}" stroke-width="0.8"/>
{text_elements}
</svg>'''


@router.get("/artifacts/{artifact_id}/cover")
def get_artifact_cover(artifact_id: str, db: Session = Depends(get_db)):
    artifact = (
        db.query(Artifact)
        .filter(Artifact.artifact_id == artifact_id)
        .first()
    )
    if not artifact:
        raise HTTPException(404, "Artifact not found")

    if artifact.cover_image_path:
        file_path = BASE_DIR / artifact.cover_image_path
        if file_path.is_file():
            # Use file mod time as ETag so browser refetches after cover changes
            import hashlib
            etag = hashlib.md5(f"{artifact.cover_image_path}:{file_path.stat().st_mtime}".encode()).hexdigest()
            return FileResponse(
                str(file_path),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600", "ETag": etag}
            )

    # No cover image — return generated SVG placeholder
    svg = _generate_placeholder_svg(artifact.title, artifact.format)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@router.post("/artifacts/{artifact_id}/cover")
async def upload_cover(
    artifact_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a cover image for an artifact."""
    artifact = db.query(Artifact).filter(Artifact.artifact_id == artifact_id).first()
    if not artifact:
        raise HTTPException(404, "Artifact not found")

    # Validate file type
    allowed = ("image/jpeg", "image/png", "image/webp")
    if file.content_type not in allowed:
        raise HTTPException(400, f"Only JPEG, PNG, and WebP images are accepted (got {file.content_type})")

    # Determine extension
    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    ext = ext_map.get(file.content_type, "jpg")
    filename = f"{artifact_id}.{ext}"
    dest = BASE_DIR / "cover_images" / filename

    # Save file
    content = await file.read()
    dest.write_bytes(content)

    # Update DB
    artifact.cover_image_path = f"cover_images/{filename}"
    db.commit()

    return {"cover_image_path": artifact.cover_image_path}
