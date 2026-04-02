"""
Utskomia Library — Migration Script

Reads Our Library-3.xlsx and populates utskomia.db.
Idempotent: drops all tables and recreates on each run.

Usage:
    python3 migrate.py
"""

import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

import pandas as pd

from models import (
    ENGINE, SessionLocal, Base,
    drop_all_tables, create_all_tables,
    Creator, CreatorRole, Collection, VolumeRun,
    Work, WorkCollection, StoryArc, WorkArcMembership,
    Artifact, ArtifactWork, Copy,
    ActivityLedger, ReadingStatus, FieldProvenance, DataQualityFlag,
    WorkType, ArtifactFormat, CollectionType, CreatorRoleEnum,
    TargetType, Owner, Location, UserProfile, EventType,
    ReadingStatusEnum, ProvenanceSource, FlagType, FlagStatus,
    NarrativeFormat, CompletionStatus,
)

XLSX_PATH = os.path.join(os.path.dirname(__file__), "Our Library-3.xlsx")
MIGRATION_DATE = date.today()
MIGRATION_TIMESTAMP = datetime.utcnow()


# ---------------------------------------------------------------------------
# Migration report accumulator
# ---------------------------------------------------------------------------

@dataclass
class SheetReport:
    sheet_name: str = ""
    source_rows: int = 0
    artifacts_created: int = 0
    works_created: int = 0
    creators_found: int = 0
    collections_created: int = 0
    volume_runs_created: int = 0
    story_arcs_created: int = 0
    activity_entries: int = 0
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


@dataclass
class MigrationReport:
    migration_timestamp: str = ""
    source_file: str = XLSX_PATH
    overall_status: str = "PASS"
    sheet_results: dict = field(default_factory=dict)
    entity_totals: dict = field(default_factory=dict)
    collects_parsing: dict = field(default_factory=lambda: {"parsed": 0, "flagged": 0, "skipped": 0})
    creator_stats: dict = field(default_factory=lambda: {"raw_names_seen": 0, "unique_creators": 0, "dedup_hits": 0})
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


report = MigrationReport()


# ---------------------------------------------------------------------------
# Caches for deduplication
# ---------------------------------------------------------------------------

# sort_name (lowercase) -> Creator object
_creator_cache: dict[str, Creator] = {}
# (name, collection_type) -> Collection object
_collection_cache: dict[tuple, Collection] = {}
# (name_lower, publisher_lower) -> VolumeRun object
_volume_run_cache: dict[tuple, VolumeRun] = {}
# (name, total_parts) -> StoryArc object
_arc_cache: dict[tuple, StoryArc] = {}
# (volume_run_id, issue_number) -> Work object (for comic work dedup)
_comic_work_cache: dict[tuple, Work] = {}


# ---------------------------------------------------------------------------
# Helper: safe value extraction from pandas
# ---------------------------------------------------------------------------

def safe_str(val) -> Optional[str]:
    """Convert a pandas cell value to string or None."""
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    return s if s else None


def safe_int(val) -> Optional[int]:
    """Convert a pandas cell value to int or None."""
    if pd.isna(val) or val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def safe_float(val) -> Optional[float]:
    """Convert a pandas cell value to float or None."""
    if pd.isna(val) or val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Helper: ISBN parsing
# ---------------------------------------------------------------------------

def parse_isbn(raw) -> Optional[str]:
    """Convert raw ISBN value (possibly float) to properly formatted string."""
    if pd.isna(raw) or raw is None:
        return None
    # Handle float (scientific notation from Excel)
    if isinstance(raw, float):
        raw = str(int(raw))
    else:
        raw = str(raw).strip()
    if not raw or raw in ("-", "0"):
        return None
    # Remove any hyphens
    raw = raw.replace("-", "")
    # Pad to 10 or 13 digits
    if len(raw) <= 10:
        raw = raw.zfill(10)
    elif len(raw) <= 13:
        raw = raw.zfill(13)
    return raw


# ---------------------------------------------------------------------------
# Helper: Creator parsing
# ---------------------------------------------------------------------------

def _normalize_sort_name(raw: str) -> str:
    """
    Normalize a creator name to canonical 'Last, First' form for dedup.
    Input might be 'Gaiman, Neil' or 'Neil Gaiman' or 'Zen'.
    """
    raw = raw.strip()
    if "," in raw:
        # Already in "Last, First" form
        parts = raw.split(",", 1)
        return f"{parts[0].strip()}, {parts[1].strip()}".lower()
    # No comma — could be single name or "First Last"
    parts = raw.split()
    if len(parts) >= 2:
        # Assume last token is last name: "Neil Gaiman" -> "gaiman, neil"
        return f"{parts[-1]}, {' '.join(parts[:-1])}".lower()
    # Single name
    return raw.lower()


def get_or_create_creator(session, raw_name: str) -> Optional[Creator]:
    """
    Parse a single creator name and return a Creator, creating if needed.
    Deduplicates by normalized sort_name.
    """
    if not raw_name or not raw_name.strip():
        return None

    raw_name = raw_name.strip()

    # Handle "Various" — create as a special creator
    # Handle "et al" — strip suffix, note it
    et_al = False
    if raw_name.lower().endswith("et al"):
        raw_name = raw_name[: raw_name.lower().rfind("et al")].rstrip(", ")
        et_al = True

    # Parse into first/last/display/sort
    if "," in raw_name:
        parts = raw_name.split(",", 1)
        last_name = parts[0].strip()
        first_name = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
        display_name = f"{first_name} {last_name}" if first_name else last_name
        sort_name = f"{last_name}, {first_name}" if first_name else last_name
    else:
        # No comma — could be "First Last" or single name
        words = raw_name.split()
        if len(words) == 1:
            first_name = None
            last_name = None
            display_name = raw_name
            sort_name = raw_name
        else:
            # Treat as "First Last" (no comma format)
            first_name = " ".join(words[:-1])
            last_name = words[-1]
            display_name = raw_name
            sort_name = f"{last_name}, {first_name}"

    # Dedup by normalized sort_name
    norm_key = _normalize_sort_name(raw_name)

    if norm_key in _creator_cache:
        report.creator_stats["dedup_hits"] += 1
        return _creator_cache[norm_key]

    report.creator_stats["raw_names_seen"] += 1

    creator = Creator(
        first_name=first_name,
        last_name=last_name,
        display_name=display_name,
        sort_name=sort_name,
    )
    if et_al:
        creator.aliases = ["et al"]

    session.add(creator)
    session.flush()
    _creator_cache[norm_key] = creator
    report.creator_stats["unique_creators"] += 1
    return creator


def parse_creators(session, raw_field) -> list[Creator]:
    """Split a semicolon-separated creator field and return list of Creator objects."""
    val = safe_str(raw_field)
    if not val:
        return []
    creators = []
    for name in val.split(";"):
        name = name.strip()
        if not name:
            continue
        c = get_or_create_creator(session, name)
        if c:
            creators.append(c)
    return creators


# ---------------------------------------------------------------------------
# Helper: Collection
# ---------------------------------------------------------------------------

def get_or_create_collection(session, name: str, collection_type: str, parent=None) -> Collection:
    key = (name.strip().lower(), collection_type)
    if key in _collection_cache:
        return _collection_cache[key]

    coll = Collection(
        name=name.strip(),
        collection_type=collection_type,
        parent_collection_id=parent.collection_id if parent else None,
    )
    session.add(coll)
    session.flush()
    _collection_cache[key] = coll
    return coll


# ---------------------------------------------------------------------------
# Helper: VolumeRun
# ---------------------------------------------------------------------------

def get_or_create_volume_run(session, name: str, publisher: str) -> VolumeRun:
    key = (name.strip().lower(), publisher.strip().lower())
    if key in _volume_run_cache:
        return _volume_run_cache[key]

    vr = VolumeRun(name=name.strip(), publisher=publisher.strip())
    session.add(vr)
    session.flush()
    _volume_run_cache[key] = vr
    return vr


# ---------------------------------------------------------------------------
# Helper: StoryArc
# ---------------------------------------------------------------------------

def get_or_create_arc(session, name: str, total_parts: Optional[int] = None) -> StoryArc:
    key = (name.strip().lower(), total_parts)
    if key in _arc_cache:
        return _arc_cache[key]

    arc = StoryArc(name=name.strip(), total_parts=total_parts)
    session.add(arc)
    session.flush()
    _arc_cache[key] = arc
    return arc


def parse_story_arc_field(raw: str):
    """
    Parse story arc field like 'Knightfall (19)' or 'Snake Eyes (2), The Dogs of War (7)'.
    Returns list of (arc_name, total_parts) tuples.
    """
    if not raw or not raw.strip():
        return []

    raw = raw.strip()

    # Try to find all "Name (N)" patterns
    pattern = r'([^,;]+?)\s*\((\d+)\)'
    matches = re.findall(pattern, raw)
    if matches:
        return [(name.strip(), int(total)) for name, total in matches]

    # No parenthetical — treat entire string as one arc with no total
    # But check for comma-separated names without totals
    return [(raw.strip(), None)]


def parse_arc_positions(raw) -> list[Optional[int]]:
    """Parse arc position field, which might be comma-separated for multi-arc rows."""
    val = safe_str(raw)
    if not val:
        return [None]
    parts = [p.strip() for p in val.split(",")]
    result = []
    for p in parts:
        try:
            result.append(int(float(p)))
        except (ValueError, TypeError):
            result.append(None)
    return result


# ---------------------------------------------------------------------------
# Helper: Collects parsing (GNs)
# ---------------------------------------------------------------------------

# Values that should NOT be parsed as issue ranges
COLLECTS_SKIP_VALUES = {"-", "_", "dnf", "everything", "?"}

def parse_collects(raw_text: str):
    """
    Parse the Collects field from Comics GNs.

    Returns:
        (parsed_issues, raw_for_note, should_flag)
        - parsed_issues: list of (title, start_num, end_num) if successfully parsed
        - raw_for_note: the original text to store as a note if flagged
        - should_flag: True if this should be flagged for manual review
    """
    if not raw_text or not raw_text.strip():
        return [], None, False

    text = raw_text.strip()

    # Skip special values
    if text.lower() in COLLECTS_SKIP_VALUES:
        return [], text, False

    if text.lower().startswith("all except") or text.lower().startswith("inserts in"):
        return [], text, False

    # Try to parse: split on ";" and " and " (but not "and" within titles)
    # Pattern: Title #X-Y or Title (#X-Y) or Title #X
    issue_pattern = re.compile(
        r'(.+?)\s*(?:#|\(#?)(\d+)(?:\s*-\s*(\d+))?\)?\s*$'
    )

    # Split on ";" first
    segments = re.split(r'\s*;\s*', text)
    # Also split on " + " which appears in some entries
    expanded = []
    for seg in segments:
        expanded.extend(re.split(r'\s*\+\s*', seg))

    parsed = []
    all_success = True

    for seg in expanded:
        seg = seg.strip()
        if not seg:
            continue
        m = issue_pattern.match(seg)
        if m:
            title = m.group(1).strip()
            start = int(m.group(2))
            end = int(m.group(3)) if m.group(3) else start
            parsed.append((title, start, end))
        else:
            all_success = False

    if all_success and parsed:
        return parsed, None, False
    elif parsed:
        # Partial parse — flag the whole thing
        return [], text, True
    else:
        return [], text, True


# ---------------------------------------------------------------------------
# Helper: Location mapping
# ---------------------------------------------------------------------------

def map_location(status_val, size_val=None) -> str:
    """Map spreadsheet Status + Size to Copy location enum value."""
    status = safe_str(status_val)
    size = safe_str(size_val)

    if not status or status == "On Shelf":
        if size == "Small":
            return Location.SMALL_SHELF.value
        return Location.LARGE_SHELF.value
    if status == "Lent":
        return Location.LENT.value
    if status == "Missing":
        return Location.MISSING.value
    return Location.LARGE_SHELF.value


# ---------------------------------------------------------------------------
# Helper: Create data quality flag
# ---------------------------------------------------------------------------

def create_flag(session, entity_type: str, entity_id: str, flag_type: str,
                description: str, suggested_fix: str = None):
    flag = DataQualityFlag(
        entity_type=entity_type,
        entity_id=entity_id,
        flag_type=flag_type,
        description=description,
        suggested_fix=suggested_fix,
    )
    session.add(flag)


# ---------------------------------------------------------------------------
# Helper: Create provenance (entity-level)
# ---------------------------------------------------------------------------

def create_provenance(session, entity_type: str, entity_id: str):
    prov = FieldProvenance(
        entity_type=entity_type,
        entity_id=entity_id,
        field_name="*",
        source=ProvenanceSource.MIGRATED.value,
        approved=True,
    )
    session.add(prov)


# ---------------------------------------------------------------------------
# Helper: Create activity ledger entry for rating
# ---------------------------------------------------------------------------

def create_rating_entry(session, user_profile: str, work: Work, rating_val):
    """Create an ActivityLedger entry for a rating if value is non-null."""
    val = safe_float(rating_val)
    if val is None:
        return
    entry = ActivityLedger(
        user_profile=user_profile,
        work_id=work.work_id,
        event_type=EventType.RATED.value,
        event_value=str(val),
        timestamp=MIGRATION_TIMESTAMP,
    )
    session.add(entry)
    return entry


# ---------------------------------------------------------------------------
# Helper: get or create comic Work (with dedup)
# ---------------------------------------------------------------------------

def get_or_create_comic_work(session, title: str, volume_run: Optional[VolumeRun],
                              issue_number: Optional[str], year: Optional[int] = None,
                              subject_tags=None, comicvine_url=None) -> Work:
    """Create or reuse a Comic Story Work, deduplicating by (volume_run_id, issue_number)."""
    vr_id = volume_run.volume_run_id if volume_run else None
    dedup_key = (vr_id, issue_number)

    if dedup_key in _comic_work_cache and vr_id is not None and issue_number is not None:
        return _comic_work_cache[dedup_key]

    work = Work(
        title=title,
        work_type=WorkType.COMIC_STORY.value,
        original_publication_year=year,
        volume_run_id=vr_id,
        issue_number=issue_number,
        subject_tags=subject_tags,
        comicvine_url=comicvine_url,
    )
    session.add(work)
    session.flush()

    if vr_id is not None and issue_number is not None:
        _comic_work_cache[dedup_key] = work

    return work


# ===========================================================================
# Sheet migration functions
# ===========================================================================

def migrate_novels(session, df: pd.DataFrame):
    """Migrate the 'Novels, etc..' sheet."""
    sr = SheetReport(sheet_name="Novels, etc..")

    # Column name has leading space for Year
    year_col = " Year" if " Year" in df.columns else "Year"

    for idx, row in df.iterrows():
        title = safe_str(row.get("Title"))
        if not title:
            continue
        sr.source_rows += 1

        try:
            # Creators
            authors = parse_creators(session, row.get("Author"))
            translators = parse_creators(session, row.get("Translator"))

            year = safe_int(row.get(year_col))
            isbn = parse_isbn(row.get("ISBN"))
            goodreads = safe_str(row.get("Goodreads Link"))

            # Work
            work = Work(
                title=title,
                work_type=WorkType.NOVEL.value,
                original_publication_year=year,
                goodreads_url=goodreads,
            )
            session.add(work)
            session.flush()
            sr.works_created += 1

            # Artifact
            artifact = Artifact(
                title=title,
                format=ArtifactFormat.PAPERBACK.value,
                isbn_or_upc=isbn,
                date_added=MIGRATION_DATE,
                owner=Owner.BANSAL_BROTHERS.value,
                main_genre=safe_str(row.get("Main Genre")),
                sous_genre=safe_str(row.get("Sous Genre")),
                goodreads_url=goodreads,
                source_sheet="Novels",
            )
            session.add(artifact)
            session.flush()
            sr.artifacts_created += 1

            # ArtifactWork link
            session.add(ArtifactWork(
                artifact_id=artifact.artifact_id,
                work_id=work.work_id,
                position=1,
            ))

            # Creator roles
            for author in authors:
                session.add(CreatorRole(
                    creator_id=author.creator_id,
                    target_type=TargetType.WORK.value,
                    target_id=work.work_id,
                    role=CreatorRoleEnum.AUTHOR.value,
                ))
            for translator in translators:
                session.add(CreatorRole(
                    creator_id=translator.creator_id,
                    target_type=TargetType.ARTIFACT.value,
                    target_id=artifact.artifact_id,
                    role=CreatorRoleEnum.TRANSLATOR.value,
                ))

            # Series / Collection
            series_name = safe_str(row.get("Series"))
            if series_name:
                coll = get_or_create_collection(session, series_name, CollectionType.SERIES.value)
                seq = safe_float(row.get("Series no."))
                session.add(WorkCollection(
                    work_id=work.work_id,
                    collection_id=coll.collection_id,
                    sequence_number=seq,
                ))

            # Copy
            copy = Copy(
                artifact_id=artifact.artifact_id,
                copy_number=1,
                location=map_location(row.get("Status")),
            )
            session.add(copy)

            # Ratings
            uts_entry = create_rating_entry(session, UserProfile.UTSAV.value, work, row.get("Uts*"))
            utk_entry = create_rating_entry(session, UserProfile.UTKARSH.value, work, row.get("Utk*"))
            if uts_entry:
                sr.activity_entries += 1
            if utk_entry:
                sr.activity_entries += 1

            # ISBN flag
            if not isbn:
                create_flag(session, "artifacts", artifact.artifact_id,
                            FlagType.MISSING_ISBN.value,
                            f"Missing ISBN for novel: {title}")

            # Provenance
            create_provenance(session, "works", work.work_id)
            create_provenance(session, "artifacts", artifact.artifact_id)

        except Exception as e:
            sr.errors.append(f"Row {idx}: {e}")
            report.overall_status = "PASS_WITH_WARNINGS"

    report.sheet_results["Novels"] = sr.__dict__
    session.flush()


def migrate_hindi_books(session, df: pd.DataFrame):
    """Migrate the 'Hindi Books' sheet."""
    sr = SheetReport(sheet_name="Hindi Books")
    year_col = " Year" if " Year" in df.columns else "Year"

    for idx, row in df.iterrows():
        title = safe_str(row.get("Title"))
        if not title:
            continue
        sr.source_rows += 1

        try:
            authors = parse_creators(session, row.get("Author"))
            year = safe_int(row.get(year_col))
            isbn = parse_isbn(row.get("ISBN"))
            goodreads = safe_str(row.get("Goodreads Link"))

            work = Work(
                title=title,
                work_type=WorkType.HINDI_LITERATURE.value,
                original_publication_year=year,
                goodreads_url=goodreads,
            )
            session.add(work)
            session.flush()
            sr.works_created += 1

            artifact = Artifact(
                title=title,
                format=ArtifactFormat.PAPERBACK.value,
                isbn_or_upc=isbn,
                date_added=MIGRATION_DATE,
                owner=Owner.BANSAL_BROTHERS.value,
                goodreads_url=goodreads,
                source_sheet="Hindi Books",
            )
            session.add(artifact)
            session.flush()
            sr.artifacts_created += 1

            session.add(ArtifactWork(
                artifact_id=artifact.artifact_id,
                work_id=work.work_id,
                position=1,
            ))

            for author in authors:
                session.add(CreatorRole(
                    creator_id=author.creator_id,
                    target_type=TargetType.WORK.value,
                    target_id=work.work_id,
                    role=CreatorRoleEnum.AUTHOR.value,
                ))

            # Series
            series_name = safe_str(row.get("Series"))
            if series_name:
                coll = get_or_create_collection(session, series_name, CollectionType.SERIES.value)
                seq = safe_float(row.get("Series no."))
                session.add(WorkCollection(
                    work_id=work.work_id,
                    collection_id=coll.collection_id,
                    sequence_number=seq,
                ))

            copy = Copy(
                artifact_id=artifact.artifact_id,
                copy_number=1,
                location=map_location(row.get("Status")),
            )
            session.add(copy)

            # Ratings
            uts_entry = create_rating_entry(session, UserProfile.UTSAV.value, work, row.get("Uts*"))
            utk_entry = create_rating_entry(session, UserProfile.UTKARSH.value, work, row.get("Utk*"))
            if uts_entry:
                sr.activity_entries += 1
            if utk_entry:
                sr.activity_entries += 1

            if not isbn:
                create_flag(session, "artifacts", artifact.artifact_id,
                            FlagType.MISSING_ISBN.value,
                            f"Missing ISBN for Hindi book: {title}")

            create_provenance(session, "works", work.work_id)
            create_provenance(session, "artifacts", artifact.artifact_id)

        except Exception as e:
            sr.errors.append(f"Row {idx}: {e}")
            report.overall_status = "PASS_WITH_WARNINGS"

    report.sheet_results["Hindi Books"] = sr.__dict__
    session.flush()


def migrate_nonfiction(session, df: pd.DataFrame):
    """Migrate the 'Non-fiction' sheet."""
    sr = SheetReport(sheet_name="Non-fiction")
    year_col = " Year" if " Year" in df.columns else "Year"

    for idx, row in df.iterrows():
        title = safe_str(row.get("Title"))
        if not title:
            continue
        sr.source_rows += 1

        try:
            authors = parse_creators(session, row.get("Author"))
            year = safe_int(row.get(year_col))
            isbn = parse_isbn(row.get("ISBN"))
            goodreads = safe_str(row.get("Goodreads Link"))

            story_val = safe_str(row.get("Story"))
            coffee_val = safe_str(row.get("Coffee Table"))

            work = Work(
                title=title,
                work_type=WorkType.NONFICTION.value,
                original_publication_year=year,
                goodreads_url=goodreads,
                is_narrative_nonfiction=True if story_val and story_val.lower() == "yes" else (False if story_val else None),
                is_coffee_table_book=True if coffee_val and coffee_val.lower() == "yes" else (False if coffee_val else None),
            )
            session.add(work)
            session.flush()
            sr.works_created += 1

            artifact = Artifact(
                title=title,
                format=ArtifactFormat.PAPERBACK.value,
                isbn_or_upc=isbn,
                date_added=MIGRATION_DATE,
                owner=Owner.BANSAL_BROTHERS.value,
                goodreads_url=goodreads,
                source_sheet="Non-fiction",
            )
            session.add(artifact)
            session.flush()
            sr.artifacts_created += 1

            session.add(ArtifactWork(
                artifact_id=artifact.artifact_id,
                work_id=work.work_id,
                position=1,
            ))

            for author in authors:
                session.add(CreatorRole(
                    creator_id=author.creator_id,
                    target_type=TargetType.WORK.value,
                    target_id=work.work_id,
                    role=CreatorRoleEnum.AUTHOR.value,
                ))

            copy = Copy(
                artifact_id=artifact.artifact_id,
                copy_number=1,
                location=map_location(row.get("Status")),
            )
            session.add(copy)

            if not isbn:
                create_flag(session, "artifacts", artifact.artifact_id,
                            FlagType.MISSING_ISBN.value,
                            f"Missing ISBN for non-fiction: {title}")

            create_provenance(session, "works", work.work_id)
            create_provenance(session, "artifacts", artifact.artifact_id)

        except Exception as e:
            sr.errors.append(f"Row {idx}: {e}")
            report.overall_status = "PASS_WITH_WARNINGS"

    report.sheet_results["Non-fiction"] = sr.__dict__
    session.flush()


def migrate_magazines(session, df: pd.DataFrame):
    """Migrate the 'Magazines' sheet."""
    sr = SheetReport(sheet_name="Magazines")

    for idx, row in df.iterrows():
        mag_name = safe_str(row.get("Magazine"))
        if not mag_name:
            continue
        sr.source_rows += 1

        try:
            # Magazine collection
            coll = get_or_create_collection(session, mag_name, CollectionType.SERIES.value)

            issue_title = safe_str(row.get("Title"))
            issue_num = safe_str(row.get("Number"))
            if issue_num:
                try:
                    issue_num = str(int(float(issue_num)))
                except (ValueError, TypeError):
                    pass

            # Extract year from Date column
            date_val = row.get("Date")
            year = None
            if pd.notna(date_val):
                try:
                    if hasattr(date_val, 'year'):
                        year = date_val.year
                    else:
                        year = safe_int(date_val)
                except Exception:
                    pass

            # Work title: use issue title if available, else construct from magazine name
            work_title = issue_title if issue_title else f"{mag_name} #{issue_num}" if issue_num else mag_name

            work = Work(
                title=work_title,
                work_type=WorkType.MAGAZINE_ISSUE.value,
                original_publication_year=year,
            )
            session.add(work)
            session.flush()
            sr.works_created += 1

            # Build notes from S. no and Volume
            notes_parts = []
            sno = safe_str(row.get("S. no"))
            if sno:
                notes_parts.append(f"S. no: {sno}")
            vol = safe_str(row.get("Volume"))
            if vol:
                notes_parts.append(f"Volume: {vol}")

            publisher = safe_str(row.get("Publisher"))

            artifact = Artifact(
                title=f"{mag_name} #{issue_num}" if issue_num else mag_name,
                format=ArtifactFormat.MAGAZINE.value,
                publisher=publisher,
                issue_number=issue_num,
                edition_year=year,
                date_added=MIGRATION_DATE,
                owner=Owner.BANSAL_BROTHERS.value,
                notes="; ".join(notes_parts) if notes_parts else None,
                source_sheet="Magazines",
            )
            session.add(artifact)
            session.flush()
            sr.artifacts_created += 1

            session.add(ArtifactWork(
                artifact_id=artifact.artifact_id,
                work_id=work.work_id,
                position=1,
            ))

            # Link work to magazine collection
            session.add(WorkCollection(
                work_id=work.work_id,
                collection_id=coll.collection_id,
                sequence_number=float(issue_num) if issue_num and issue_num.isdigit() else None,
            ))

            copy = Copy(
                artifact_id=artifact.artifact_id,
                copy_number=1,
                location=map_location(row.get("Status")),
            )
            session.add(copy)

            create_provenance(session, "works", work.work_id)
            create_provenance(session, "artifacts", artifact.artifact_id)

        except Exception as e:
            sr.errors.append(f"Row {idx}: {e}")
            report.overall_status = "PASS_WITH_WARNINGS"

    report.sheet_results["Magazines"] = sr.__dict__
    session.flush()


def migrate_comics_gns(session, df: pd.DataFrame):
    """Migrate the 'Comics (GNs)' sheet."""
    sr = SheetReport(sheet_name="Comics (GNs)")

    for idx, row in df.iterrows():
        title = safe_str(row.get("Title"))
        if not title:
            continue
        sr.source_rows += 1

        try:
            writers = parse_creators(session, row.get("Writer"))
            artists = parse_creators(session, row.get("Artist"))
            is_reprint = safe_str(row.get("Reprint")) == "Yes"
            orig_vol_name = safe_str(row.get("Original Volume"))
            orig_publisher = safe_str(row.get("Original Publisher"))
            orig_year = safe_int(row.get("Original Year"))
            issue_num = safe_str(row.get("#"))
            if issue_num:
                try:
                    issue_num = str(int(float(issue_num)))
                except (ValueError, TypeError):
                    pass

            isbn = parse_isbn(row.get("ISBN"))
            link = safe_str(row.get("Link"))
            cv_link = safe_str(row.get("ComicVine Link"))
            series_name = safe_str(row.get("Series Name"))
            collects_raw = safe_str(row.get("Collects"))
            publisher = safe_str(row.get("Publisher"))

            # Determine goodreads vs comicvine from link content
            goodreads_url = None
            if link and "goodreads" in link.lower():
                goodreads_url = link
            elif link and "comicvine" not in link.lower():
                goodreads_url = link  # default to goodreads for non-CV links

            # Volume run for original (if reprint)
            orig_volume_run = None
            if is_reprint and orig_vol_name and orig_publisher:
                orig_volume_run = get_or_create_volume_run(session, orig_vol_name, orig_publisher)

            # Artifact
            artifact = Artifact(
                title=title,
                format=ArtifactFormat.GRAPHIC_NOVEL.value,
                publisher=publisher,
                issue_number=issue_num,
                isbn_or_upc=isbn,
                is_reprint=is_reprint,
                original_publisher=orig_publisher if is_reprint else None,
                date_added=MIGRATION_DATE,
                owner=Owner.BANSAL_BROTHERS.value,
                goodreads_url=goodreads_url,
                source_sheet="Comics (GNs)",
            )
            session.add(artifact)
            session.flush()
            sr.artifacts_created += 1

            # Parse Collects to create Works
            works_for_artifact = []

            if collects_raw:
                parsed_issues, raw_note, should_flag = parse_collects(collects_raw)

                if parsed_issues and not should_flag:
                    # Successfully parsed — create one Work per issue
                    report.collects_parsing["parsed"] += 1
                    for pos, (issue_title, start_num, end_num) in enumerate(parsed_issues, 1):
                        for num in range(start_num, end_num + 1):
                            work_title = f"{issue_title} #{num}"
                            # Try to find the volume run for this title
                            vr = orig_volume_run
                            if not vr and orig_publisher:
                                vr = get_or_create_volume_run(session, issue_title, orig_publisher)
                            elif not vr and publisher:
                                vr = get_or_create_volume_run(session, issue_title, publisher)
                            w = get_or_create_comic_work(
                                session, work_title, vr, str(num),
                                year=orig_year,
                            )
                            works_for_artifact.append(w)
                            sr.works_created += 1
                elif should_flag:
                    report.collects_parsing["flagged"] += 1
                    # Create one Work for the GN as a whole
                    w = Work(
                        title=title,
                        work_type=WorkType.COMIC_STORY.value,
                        original_publication_year=orig_year,
                        volume_run_id=orig_volume_run.volume_run_id if orig_volume_run else None,
                        comicvine_url=cv_link,
                    )
                    session.add(w)
                    session.flush()
                    works_for_artifact.append(w)
                    sr.works_created += 1

                    create_flag(session, "artifacts", artifact.artifact_id,
                                FlagType.UNPARSED_COLLECTS.value,
                                f"Could not parse Collects field: {collects_raw}",
                                suggested_fix="Manual review needed")
                else:
                    # Special value like "-" or "DNF"
                    report.collects_parsing["skipped"] += 1
                    w = Work(
                        title=title,
                        work_type=WorkType.COMIC_STORY.value,
                        original_publication_year=orig_year,
                        volume_run_id=orig_volume_run.volume_run_id if orig_volume_run else None,
                        comicvine_url=cv_link,
                    )
                    session.add(w)
                    session.flush()
                    works_for_artifact.append(w)
                    sr.works_created += 1
            else:
                # No Collects field at all — check if Original Volume + O# gives us a work
                o_num = safe_str(row.get("O#"))
                if o_num:
                    try:
                        o_num = str(int(float(o_num)))
                    except (ValueError, TypeError):
                        pass

                if orig_volume_run and o_num:
                    work_title = f"{orig_vol_name} #{o_num}"
                    w = get_or_create_comic_work(
                        session, work_title, orig_volume_run, o_num,
                        year=orig_year, comicvine_url=cv_link,
                    )
                else:
                    w = Work(
                        title=title,
                        work_type=WorkType.COMIC_STORY.value,
                        original_publication_year=orig_year,
                        volume_run_id=orig_volume_run.volume_run_id if orig_volume_run else None,
                        comicvine_url=cv_link,
                    )
                    session.add(w)
                    session.flush()
                works_for_artifact.append(w)
                sr.works_created += 1

            # ArtifactWork links
            for pos, w in enumerate(works_for_artifact, 1):
                aw = ArtifactWork(
                    artifact_id=artifact.artifact_id,
                    work_id=w.work_id,
                    position=pos,
                )
                # Store collects note on first link if there's a raw note
                if pos == 1 and collects_raw and (collects_raw.strip().lower() in ("dnf", "everything") or collects_raw.strip().startswith("All except")):
                    aw.collects_note = collects_raw
                session.add(aw)

            # Creator roles — link to all Works
            for w in works_for_artifact:
                for writer in writers:
                    session.add(CreatorRole(
                        creator_id=writer.creator_id,
                        target_type=TargetType.WORK.value,
                        target_id=w.work_id,
                        role=CreatorRoleEnum.WRITER.value,
                    ))
                for artist in artists:
                    session.add(CreatorRole(
                        creator_id=artist.creator_id,
                        target_type=TargetType.WORK.value,
                        target_id=w.work_id,
                        role=CreatorRoleEnum.ARTIST.value,
                    ))

            # Series collection
            if series_name:
                coll = get_or_create_collection(session, series_name, CollectionType.SERIES.value)
                for w in works_for_artifact:
                    session.add(WorkCollection(
                        work_id=w.work_id,
                        collection_id=coll.collection_id,
                    ))

            # Copy
            copy = Copy(
                artifact_id=artifact.artifact_id,
                copy_number=1,
                location=map_location(row.get("Status")),
            )
            session.add(copy)

            if not isbn:
                create_flag(session, "artifacts", artifact.artifact_id,
                            FlagType.MISSING_ISBN.value,
                            f"Missing ISBN for GN: {title}")

            create_provenance(session, "artifacts", artifact.artifact_id)
            for w in works_for_artifact:
                create_provenance(session, "works", w.work_id)

        except Exception as e:
            sr.errors.append(f"Row {idx}: {e}")
            report.overall_status = "PASS_WITH_WARNINGS"

    report.sheet_results["Comics (GNs)"] = sr.__dict__
    session.flush()


def migrate_comics_issues(session, df: pd.DataFrame):
    """Migrate the 'Comics (Issues)' sheet — the most complex migration."""
    sr = SheetReport(sheet_name="Comics (Issues)")

    # Collect Complete values per VolumeRun for batch update
    volume_run_complete_values: dict[str, list[str]] = defaultdict(list)

    # Dynamically detect multi-story columns
    story_slots = [1]  # Story 1 is always present (main columns)
    for col in df.columns:
        m = re.match(r'Original Volume Issue (\d+)', str(col))
        if m:
            n = int(m.group(1))
            if n not in story_slots:
                story_slots.append(n)
    story_slots.sort()

    for idx, row in df.iterrows():
        volume_name = safe_str(row.get("Volume"))
        if not volume_name:
            continue
        sr.source_rows += 1

        try:
            issue_num = safe_str(row.get("#"))
            if issue_num:
                try:
                    issue_num = str(int(float(issue_num)))
                except (ValueError, TypeError):
                    pass

            publisher = safe_str(row.get("Publisher"))
            is_reprint = safe_str(row.get("Reprint")) == "Yes"
            orig_publisher = safe_str(row.get("Original Publisher"))
            orig_vol_name = safe_str(row.get("Original Volume"))
            subj_category = safe_str(row.get("Subj Category"))
            complete_val = safe_str(row.get("Complete"))
            size_val = safe_str(row.get("Size"))
            notes = safe_str(row.get("Notes"))
            link = safe_str(row.get("Link"))

            # Reprint volume run (the physical item's series)
            reprint_vr = None
            if publisher:
                reprint_vr = get_or_create_volume_run(session, volume_name, publisher)

                # Collect Complete values
                if complete_val:
                    volume_run_complete_values[reprint_vr.volume_run_id].append(complete_val)

            # --- Story 1: the primary work ---
            orig_volume_run = None
            o_num = safe_str(row.get("O#"))
            if o_num:
                try:
                    o_num = str(int(float(o_num)))
                except (ValueError, TypeError):
                    pass

            if is_reprint and orig_vol_name and orig_publisher:
                orig_volume_run = get_or_create_volume_run(session, orig_vol_name, orig_publisher)
                work_title = f"{orig_vol_name} #{o_num}" if o_num else f"{orig_vol_name}"
                work1 = get_or_create_comic_work(
                    session, work_title, orig_volume_run, o_num,
                    subject_tags=[subj_category] if subj_category else None,
                    comicvine_url=link if link and "comicvine" in link.lower() else None,
                )
            else:
                # Not a reprint — the volume IS the original
                work_title = f"{volume_name} #{issue_num}" if issue_num else volume_name
                work1 = get_or_create_comic_work(
                    session, work_title, reprint_vr, issue_num,
                    subject_tags=[subj_category] if subj_category else None,
                    comicvine_url=link if link and "comicvine" in link.lower() else None,
                )

            # Set goodreads if link is not comicvine
            if link and "comicvine" not in link.lower():
                work1.goodreads_url = link

            sr.works_created += 1

            # Creator roles for story 1
            writers1 = parse_creators(session, row.get("Writer"))
            artists1 = parse_creators(session, row.get("Artist"))
            for w in writers1:
                session.add(CreatorRole(
                    creator_id=w.creator_id,
                    target_type=TargetType.WORK.value,
                    target_id=work1.work_id,
                    role=CreatorRoleEnum.WRITER.value,
                ))
            for a in artists1:
                session.add(CreatorRole(
                    creator_id=a.creator_id,
                    target_type=TargetType.WORK.value,
                    target_id=work1.work_id,
                    role=CreatorRoleEnum.ARTIST.value,
                ))

            # Story arcs for story 1
            arc_raw = safe_str(row.get("Story Arc"))
            arc_num_raw = row.get("Arc #")
            if arc_raw:
                arcs = parse_story_arc_field(arc_raw)
                positions = parse_arc_positions(arc_num_raw)

                # Pad positions to match arc count
                while len(positions) < len(arcs):
                    positions.append(None)

                for (arc_name, total_parts), pos in zip(arcs, positions):
                    arc = get_or_create_arc(session, arc_name, total_parts)
                    session.add(WorkArcMembership(
                        work_id=work1.work_id,
                        arc_id=arc.arc_id,
                        arc_position=pos,
                    ))

            # --- Additional stories (dynamically detected) ---
            all_works = [(work1, False)]  # (Work, is_partial)

            for n in story_slots:
                if n == 1:
                    continue
                col_vol = f"Original Volume Issue {n}"
                col_onum = f"O{n}#"
                col_writer = f"Writer {n}"
                col_artist = f"Artist {n}"
                col_link = f"Link {n}"

                story_vol = safe_str(row.get(col_vol))
                if not story_vol:
                    continue

                story_onum = safe_str(row.get(col_onum))
                is_partial = False
                if story_onum and "*" in str(story_onum):
                    is_partial = True
                    story_onum = str(story_onum).replace("*", "").strip()

                if story_onum:
                    try:
                        story_onum = str(int(float(story_onum)))
                    except (ValueError, TypeError):
                        pass

                # Get or create volume run for this story's original series
                story_orig_publisher = orig_publisher or publisher or "Unknown"
                story_vr = get_or_create_volume_run(session, story_vol, story_orig_publisher)

                story_title = f"{story_vol} #{story_onum}" if story_onum else story_vol
                story_link = safe_str(row.get(col_link))

                work_n = get_or_create_comic_work(
                    session, story_title, story_vr, story_onum,
                    comicvine_url=story_link if story_link and "comicvine" in story_link.lower() else None,
                )
                if story_link and "comicvine" not in story_link.lower():
                    work_n.goodreads_url = story_link

                sr.works_created += 1

                # Creator roles for story N
                writers_n = parse_creators(session, row.get(col_writer))
                artists_n = parse_creators(session, row.get(col_artist))
                for w in writers_n:
                    session.add(CreatorRole(
                        creator_id=w.creator_id,
                        target_type=TargetType.WORK.value,
                        target_id=work_n.work_id,
                        role=CreatorRoleEnum.WRITER.value,
                    ))
                for a in artists_n:
                    session.add(CreatorRole(
                        creator_id=a.creator_id,
                        target_type=TargetType.WORK.value,
                        target_id=work_n.work_id,
                        role=CreatorRoleEnum.ARTIST.value,
                    ))

                all_works.append((work_n, is_partial))

            # --- Create Artifact ---
            artifact_title = f"{volume_name} #{issue_num}" if issue_num else volume_name
            artifact = Artifact(
                title=artifact_title,
                format=ArtifactFormat.COMIC_ISSUE.value,
                publisher=publisher,
                issue_number=issue_num,
                is_reprint=is_reprint,
                original_publisher=orig_publisher if is_reprint else None,
                volume_run_id=reprint_vr.volume_run_id if reprint_vr else None,
                size=size_val,
                date_added=MIGRATION_DATE,
                owner=Owner.BANSAL_BROTHERS.value,
                notes=notes,
                source_sheet="Comics (Issues)",
            )
            session.add(artifact)
            session.flush()
            sr.artifacts_created += 1

            # ArtifactWork links
            for pos, (work_obj, is_partial) in enumerate(all_works, 1):
                session.add(ArtifactWork(
                    artifact_id=artifact.artifact_id,
                    work_id=work_obj.work_id,
                    position=pos,
                    is_partial=is_partial,
                ))

            # Copy
            copy = Copy(
                artifact_id=artifact.artifact_id,
                copy_number=1,
                location=map_location(row.get("Status"), size_val),
            )
            session.add(copy)

            # Ratings
            uts_entry = create_rating_entry(session, UserProfile.UTSAV.value, work1, row.get("Uts Rating"))
            utk_entry = create_rating_entry(session, UserProfile.UTKARSH.value, work1, row.get("Utk Rating"))
            if uts_entry:
                sr.activity_entries += 1
            if utk_entry:
                sr.activity_entries += 1

            create_provenance(session, "artifacts", artifact.artifact_id)
            for work_obj, _ in all_works:
                create_provenance(session, "works", work_obj.work_id)

        except Exception as e:
            sr.errors.append(f"Row {idx}: {e}")
            report.overall_status = "PASS_WITH_WARNINGS"

    # --- Batch update VolumeRun completion status ---
    for vr_id, values in volume_run_complete_values.items():
        vr = session.get(VolumeRun, vr_id)
        if not vr:
            continue

        # Count occurrences
        counts = defaultdict(int)
        for v in values:
            counts[v.upper()] += 1

        # Determine majority
        majority = max(counts, key=counts.get)

        if majority == "S":
            vr.narrative_format = NarrativeFormat.SERIALIZED.value
            vr.completion_status = CompletionStatus.NOT_PURSUING.value
        elif majority == "Y":
            vr.completion_status = CompletionStatus.COMPLETE.value
        elif majority == "N":
            vr.completion_status = CompletionStatus.INCOMPLETE.value

        # Flag if there were mixed values
        if len(counts) > 1:
            create_flag(session, "volume_runs", vr_id,
                        FlagType.CONFLICTING_DATA.value,
                        f"Mixed Complete values for {vr.name} ({vr.publisher}): {dict(counts)}",
                        suggested_fix=f"Majority value '{majority}' was used")

    report.sheet_results["Comics (Issues)"] = sr.__dict__
    session.flush()


# ===========================================================================
# Post-migration processing
# ===========================================================================

def generate_reading_status(session):
    """Generate denormalized ReadingStatus rows from ActivityLedger."""
    # Query distinct (user_profile, work_id) pairs with their most recent rating
    from sqlalchemy import func
    results = (
        session.query(
            ActivityLedger.user_profile,
            ActivityLedger.work_id,
            func.max(ActivityLedger.timestamp).label("last_event"),
        )
        .filter(ActivityLedger.event_type == EventType.RATED.value)
        .group_by(ActivityLedger.user_profile, ActivityLedger.work_id)
        .all()
    )

    for user_profile, work_id, last_event in results:
        # Get the most recent rating value
        latest = (
            session.query(ActivityLedger.event_value)
            .filter(
                ActivityLedger.user_profile == user_profile,
                ActivityLedger.work_id == work_id,
                ActivityLedger.event_type == EventType.RATED.value,
            )
            .order_by(ActivityLedger.timestamp.desc())
            .first()
        )
        rating = safe_float(latest[0]) if latest else None

        rs = ReadingStatus(
            user_profile=user_profile,
            work_id=work_id,
            status=ReadingStatusEnum.FINISHED.value,
            current_rating=rating,
            last_event_at=last_event,
        )
        session.add(rs)

    session.flush()


def flag_near_duplicate_creators(session):
    """Flag creators with similar names (same last name, different first name) for review."""
    from collections import defaultdict
    by_last = defaultdict(list)
    for creator in session.query(Creator).all():
        if creator.last_name:
            by_last[creator.last_name.lower()].append(creator)

    for last_name, creators in by_last.items():
        if len(creators) <= 1:
            continue
        # Flag each pair as potential duplicates
        seen_pairs = set()
        for i, c1 in enumerate(creators):
            for c2 in creators[i + 1:]:
                pair_key = tuple(sorted([c1.creator_id, c2.creator_id]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                create_flag(
                    session, "creators", c1.creator_id,
                    FlagType.NAME_INCONSISTENCY.value,
                    f"Potential duplicate: '{c1.display_name}' and '{c2.display_name}' share last name '{last_name}'",
                    suggested_fix=f"Review if these are the same person. Other ID: {c2.creator_id}",
                )


# ===========================================================================
# Sample data export
# ===========================================================================

def export_sample_data(session):
    """Export a curated subset of the migrated data as JSON for UI prototyping."""
    from sqlalchemy import or_

    sample = {
        "metadata": {
            "generated_at": MIGRATION_TIMESTAMP.isoformat(),
            "description": "Curated sample data from Utskomia Library migration for UI prototyping",
        },
        "artifacts": [],
        "works": [],
        "creators": [],
        "collections": [],
        "story_arcs": [],
        "activity_ledger": [],
        "data_quality_flags": [],
    }

    def artifact_to_dict(a: Artifact) -> dict:
        return {
            "artifact_id": a.artifact_id,
            "title": a.title,
            "format": a.format,
            "publisher": a.publisher,
            "edition_year": a.edition_year,
            "isbn_or_upc": a.isbn_or_upc,
            "is_reprint": a.is_reprint,
            "original_publisher": a.original_publisher,
            "date_added": str(a.date_added) if a.date_added else None,
            "owner": a.owner,
            "issue_number": a.issue_number,
            "size": a.size,
            "main_genre": a.main_genre,
            "sous_genre": a.sous_genre,
            "goodreads_url": a.goodreads_url,
            "notes": a.notes,
            "source_sheet": a.source_sheet,
            "works": [
                {
                    "work_id": aw.work.work_id,
                    "title": aw.work.title,
                    "position": aw.position,
                    "is_partial": aw.is_partial,
                }
                for aw in sorted(a.artifact_works, key=lambda x: x.position)
            ],
            "copies": [
                {
                    "copy_id": c.copy_id,
                    "location": c.location,
                    "condition": c.condition,
                    "borrower_name": c.borrower_name,
                }
                for c in a.copies
            ],
        }

    def work_to_dict(w: Work) -> dict:
        return {
            "work_id": w.work_id,
            "title": w.title,
            "work_type": w.work_type,
            "original_publication_year": w.original_publication_year,
            "issue_number": w.issue_number,
            "subject_tags": w.subject_tags,
            "is_narrative_nonfiction": w.is_narrative_nonfiction,
            "is_coffee_table_book": w.is_coffee_table_book,
            "goodreads_url": w.goodreads_url,
            "comicvine_url": w.comicvine_url,
            "volume_run": {
                "name": w.volume_run.name,
                "publisher": w.volume_run.publisher,
            } if w.volume_run else None,
            "collections": [
                {"name": wc.collection.name, "sequence_number": wc.sequence_number}
                for wc in w.work_collections
            ],
            "arcs": [
                {"name": wam.arc.name, "arc_position": wam.arc_position, "total_parts": wam.arc.total_parts}
                for wam in w.arc_memberships
            ],
            "creators": [
                {"display_name": cr.creator.display_name, "role": cr.role}
                for cr in session.query(CreatorRole)
                .filter(CreatorRole.target_type == "work", CreatorRole.target_id == w.work_id)
                .all()
            ],
            "reading_status": [
                {"user_profile": rs.user_profile, "status": rs.status, "rating": rs.current_rating}
                for rs in w.reading_statuses
            ],
        }

    # Select sample artifacts by source sheet
    # Novels: ~6
    novels = session.query(Artifact).filter(Artifact.source_sheet == "Novels").limit(8).all()
    # Non-fiction: 2-3
    nonfiction = session.query(Artifact).filter(Artifact.source_sheet == "Non-fiction").limit(3).all()
    # Hindi: 1
    hindi = session.query(Artifact).filter(Artifact.source_sheet == "Hindi Books").limit(1).all()
    # Magazines: 2
    magazines = session.query(Artifact).filter(Artifact.source_sheet == "Magazines").limit(2).all()
    # GNs: 5
    gns = session.query(Artifact).filter(Artifact.source_sheet == "Comics (GNs)").limit(5).all()
    # Issues: 10-15
    issues = session.query(Artifact).filter(Artifact.source_sheet == "Comics (Issues)").limit(15).all()

    all_sample_artifacts = novels + nonfiction + hindi + magazines + gns + issues

    # Collect all work IDs referenced
    work_ids = set()
    for a in all_sample_artifacts:
        sample["artifacts"].append(artifact_to_dict(a))
        for aw in a.artifact_works:
            work_ids.add(aw.work_id)

    # Export works
    for wid in work_ids:
        w = session.get(Work, wid)
        if w:
            sample["works"].append(work_to_dict(w))

    # Collect creator IDs
    creator_ids = set()
    for wid in work_ids:
        for cr in session.query(CreatorRole).filter(CreatorRole.target_id == wid).all():
            creator_ids.add(cr.creator_id)
    for a in all_sample_artifacts:
        for cr in session.query(CreatorRole).filter(CreatorRole.target_id == a.artifact_id).all():
            creator_ids.add(cr.creator_id)

    for cid in list(creator_ids)[:10]:
        c = session.get(Creator, cid)
        if c:
            sample["creators"].append({
                "creator_id": c.creator_id,
                "display_name": c.display_name,
                "sort_name": c.sort_name,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "aliases": c.aliases,
            })

    # Collections: a few
    for coll in session.query(Collection).limit(5).all():
        sample["collections"].append({
            "collection_id": coll.collection_id,
            "name": coll.name,
            "collection_type": coll.collection_type,
            "parent_collection_id": coll.parent_collection_id,
        })

    # Story arcs: a few
    for arc in session.query(StoryArc).limit(5).all():
        sample["story_arcs"].append({
            "arc_id": arc.arc_id,
            "name": arc.name,
            "total_parts": arc.total_parts,
            "parent_arc_id": arc.parent_arc_id,
        })

    # Activity entries (sample)
    for entry in session.query(ActivityLedger).limit(10).all():
        sample["activity_ledger"].append({
            "log_id": entry.log_id,
            "user_profile": entry.user_profile,
            "work_id": entry.work_id,
            "event_type": entry.event_type,
            "event_value": entry.event_value,
        })

    # Data quality flags (sample)
    for flag in session.query(DataQualityFlag).limit(5).all():
        sample["data_quality_flags"].append({
            "flag_id": flag.flag_id,
            "entity_type": flag.entity_type,
            "entity_id": flag.entity_id,
            "flag_type": flag.flag_type,
            "description": flag.description,
            "status": flag.status,
        })

    with open("sample_data.json", "w") as f:
        json.dump(sample, f, indent=2, default=str)

    print(f"  Exported sample_data.json: {len(sample['artifacts'])} artifacts, "
          f"{len(sample['works'])} works, {len(sample['creators'])} creators")


# ===========================================================================
# Migration report export
# ===========================================================================

def write_migration_report(session):
    """Write final migration report to JSON."""
    # Entity totals
    report.migration_timestamp = MIGRATION_TIMESTAMP.isoformat()
    report.entity_totals = {
        "creators": session.query(Creator).count(),
        "creator_roles": session.query(CreatorRole).count(),
        "collections": session.query(Collection).count(),
        "volume_runs": session.query(VolumeRun).count(),
        "works": session.query(Work).count(),
        "work_collections": session.query(WorkCollection).count(),
        "story_arcs": session.query(StoryArc).count(),
        "work_arc_membership": session.query(WorkArcMembership).count(),
        "artifacts": session.query(Artifact).count(),
        "artifact_works": session.query(ArtifactWork).count(),
        "copies": session.query(Copy).count(),
        "activity_ledger": session.query(ActivityLedger).count(),
        "reading_status": session.query(ReadingStatus).count(),
        "field_provenance": session.query(FieldProvenance).count(),
        "data_quality_flags": session.query(DataQualityFlag).count(),
    }

    with open("migration_report.json", "w") as f:
        json.dump({
            "migration_timestamp": report.migration_timestamp,
            "source_file": report.source_file,
            "overall_status": report.overall_status,
            "sheet_results": report.sheet_results,
            "entity_totals": report.entity_totals,
            "collects_parsing": report.collects_parsing,
            "creator_stats": report.creator_stats,
            "errors": report.errors,
            "warnings": report.warnings,
        }, f, indent=2, default=str)

    print(f"  Wrote migration_report.json")


# ===========================================================================
# Main entry point
# ===========================================================================

def main():
    print("Utskomia Library — Migration Script")
    print("=" * 50)

    # Step 1: Clean slate
    print("\n1. Dropping and recreating tables...")
    drop_all_tables()
    create_all_tables()

    # Step 2: Load xlsx
    print("2. Loading xlsx...")
    xlsx = pd.ExcelFile(XLSX_PATH)
    sheets = {
        "Novels": pd.read_excel(xlsx, "Novels, etc.."),
        "Hindi Books": pd.read_excel(xlsx, "Hindi Books"),
        "Non-fiction": pd.read_excel(xlsx, "Non-fiction"),
        "Magazines": pd.read_excel(xlsx, "Magazines"),
        "Comics (GNs)": pd.read_excel(xlsx, "Comics (GNs)"),
        "Comics (Issues)": pd.read_excel(xlsx, "Comics (Issues)"),
    }
    for name, df in sheets.items():
        print(f"   {name}: {len(df)} rows, columns: {list(df.columns)[:8]}...")

    # Step 3: Migrate each sheet
    session = SessionLocal()
    try:
        print("\n3. Migrating sheets...")

        print("   -> Novels...")
        migrate_novels(session, sheets["Novels"])

        print("   -> Hindi Books...")
        migrate_hindi_books(session, sheets["Hindi Books"])

        print("   -> Non-fiction...")
        migrate_nonfiction(session, sheets["Non-fiction"])

        print("   -> Magazines...")
        migrate_magazines(session, sheets["Magazines"])

        print("   -> Comics (GNs)...")
        migrate_comics_gns(session, sheets["Comics (GNs)"])

        print("   -> Comics (Issues)...")
        migrate_comics_issues(session, sheets["Comics (Issues)"])

        # Step 4: Post-processing
        print("\n4. Post-processing...")
        print("   -> Generating reading status cache...")
        generate_reading_status(session)

        print("   -> Flagging near-duplicate creators...")
        flag_near_duplicate_creators(session)

        # Step 5: Commit
        print("\n5. Committing to database...")
        session.commit()

        # Step 6: Export
        print("\n6. Exporting...")
        export_sample_data(session)
        write_migration_report(session)

        print("\n" + "=" * 50)
        print("Migration complete!")
        print(f"  Status: {report.overall_status}")
        print(f"  Total artifacts: {report.entity_totals.get('artifacts', '?')}")
        print(f"  Total works: {report.entity_totals.get('works', '?')}")
        print(f"  Total creators: {report.entity_totals.get('creators', '?')}")
        print(f"  Data quality flags: {report.entity_totals.get('data_quality_flags', '?')}")

        if report.errors:
            print(f"\n  ERRORS ({len(report.errors)}):")
            for e in report.errors[:10]:
                print(f"    - {e}")

    except Exception as e:
        session.rollback()
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        report.overall_status = "FAIL"
        report.errors.append(str(e))
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
