"""
Utskomia Library — SQLAlchemy 2.0 ORM Models

16 tables implementing the FRBR-inspired two-level data model
(Work + Artifact) as specified in Utskomia_PRD.md Section 5.
"""

import enum
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, Date,
    JSON, ForeignKey, UniqueConstraint, Index, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = "utskomia.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=ENGINE)


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enum definitions (stored as TEXT in SQLite, validated in Python)
# ---------------------------------------------------------------------------

class WorkType(str, enum.Enum):
    NOVEL = "Novel"
    NONFICTION = "Non-fiction"
    HINDI_LITERATURE = "Hindi Literature"
    COMIC_STORY = "Comic Story"
    MAGAZINE_ISSUE = "Magazine Issue"
    SHORT_STORY = "Short Story"


class ArtifactFormat(str, enum.Enum):
    HARDCOVER = "Hardcover"
    PAPERBACK = "Paperback"
    COMIC_ISSUE = "Comic Issue"
    GRAPHIC_NOVEL = "Graphic Novel"
    MAGAZINE = "Magazine"
    KINDLE = "Kindle"
    AUDIBLE = "Audible"


class CollectionType(str, enum.Enum):
    UNIVERSE_FRANCHISE = "Universe/Franchise"
    SERIES = "Series"
    SUB_SERIES = "Sub-series"


class NarrativeFormat(str, enum.Enum):
    ARC_BASED = "Arc-based"
    SERIALIZED = "Serialized"
    ANTHOLOGY = "Anthology"
    STANDALONE = "Standalone"


class CompletionStatus(str, enum.Enum):
    COMPLETE = "Complete"
    INCOMPLETE = "Incomplete"
    NOT_PURSUING = "Not Pursuing"


class CreatorRoleEnum(str, enum.Enum):
    AUTHOR = "Author"
    WRITER = "Writer"
    ARTIST = "Artist"
    INKER = "Inker"
    COLORIST = "Colorist"
    LETTERER = "Letterer"
    EDITOR = "Editor"
    TRANSLATOR = "Translator"
    NARRATOR_PERFORMER = "Narrator/Performer"


class TargetType(str, enum.Enum):
    WORK = "work"
    ARTIFACT = "artifact"


class Owner(str, enum.Enum):
    BANSAL_BROTHERS = "The Bansal Brothers"
    SOMDUTTA = "Somdutta"


class Location(str, enum.Enum):
    LARGE_SHELF = "Large Shelf"
    SMALL_SHELF = "Small Shelf"
    BOX = "Box"
    LENT = "Lent"
    MISSING = "Missing"
    DIGITAL = "Digital"


class UserProfile(str, enum.Enum):
    UTSAV = "Utsav"
    UTKARSH = "Utkarsh"
    SOM = "Som"


class EventType(str, enum.Enum):
    STARTED_READING = "Started_Reading"
    FINISHED_READING = "Finished_Reading"
    RATED = "Rated"
    REVIEWED = "Reviewed"
    ABANDONED_DNF = "Abandoned/DNF"


class ReadingStatusEnum(str, enum.Enum):
    UNREAD = "Unread"
    READING = "Reading"
    FINISHED = "Finished"
    DNF = "DNF"


class ProvenanceSource(str, enum.Enum):
    MANUAL = "manual"
    MIGRATED = "migrated"
    SCRAPED_COMICVINE = "scraped:comicvine"
    SCRAPED_OPENLIBRARY = "scraped:openlibrary"
    SCRAPED_GOODREADS = "scraped:goodreads"
    SCRAPED_GOOGLEBOOKS = "scraped:googlebooks"


class FlagType(str, enum.Enum):
    MISSING_ISBN = "missing_isbn"
    NAME_INCONSISTENCY = "name_inconsistency"
    UNPARSED_COLLECTS = "unparsed_collects"
    POTENTIAL_DUPLICATE = "potential_duplicate"
    MISSING_METADATA = "missing_metadata"
    CONFLICTING_DATA = "conflicting_data"


class FlagStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ArtifactSize(str, enum.Enum):
    LARGE = "Large"
    SMALL = "Small"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Table models
# ---------------------------------------------------------------------------

class Creator(Base):
    __tablename__ = "creators"

    creator_id = Column(String(36), primary_key=True, default=_uuid)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    display_name = Column(Text, nullable=False)
    sort_name = Column(Text, nullable=False)
    aliases = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = relationship("CreatorRole", back_populates="creator", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_creators_display_name", "display_name"),
        Index("ix_creators_sort_name", "sort_name"),
    )


class CreatorRole(Base):
    __tablename__ = "creator_roles"

    id = Column(String(36), primary_key=True, default=_uuid)
    creator_id = Column(String(36), ForeignKey("creators.creator_id"), nullable=False)
    target_type = Column(String(20), nullable=False)   # 'work' or 'artifact'
    target_id = Column(String(36), nullable=False)      # polymorphic FK
    role = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)

    creator = relationship("Creator", back_populates="roles")


class Collection(Base):
    __tablename__ = "collections"

    collection_id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(Text, nullable=False)
    parent_collection_id = Column(String(36), ForeignKey("collections.collection_id"), nullable=True)
    collection_type = Column(String(30), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("Collection", remote_side=[collection_id], backref="children")
    work_collections = relationship("WorkCollection", back_populates="collection")

    __table_args__ = (
        Index("ix_collections_name", "name"),
    )


class VolumeRun(Base):
    __tablename__ = "volume_runs"

    volume_run_id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(Text, nullable=False)
    publisher = Column(Text, nullable=False)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    volume_qualifier = Column(Text, nullable=True)
    volume_number = Column(Integer, nullable=True)
    narrative_format = Column(String(30), nullable=True)
    completion_status = Column(String(30), nullable=True)  # Only "Not Pursuing" for Serialized runs. Y/N lives on story_arcs. Per D-028.
    comicvine_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    works = relationship("Work", back_populates="volume_run")
    artifacts = relationship("Artifact", back_populates="volume_run")

    __table_args__ = (
        Index("ix_volume_runs_name", "name"),
    )


class Work(Base):
    __tablename__ = "works"

    work_id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(Text, nullable=False)
    work_type = Column(String(30), nullable=False)
    original_publication_year = Column(Integer, nullable=True)
    volume_run_id = Column(String(36), ForeignKey("volume_runs.volume_run_id"), nullable=True)
    issue_number = Column(Text, nullable=True)
    subject_tags = Column(JSON, nullable=True)
    is_narrative_nonfiction = Column(Boolean, nullable=True)
    is_coffee_table_book = Column(Boolean, nullable=True)
    goodreads_url = Column(Text, nullable=True)
    comicvine_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    volume_run = relationship("VolumeRun", back_populates="works")
    artifact_works = relationship("ArtifactWork", back_populates="work")
    work_collections = relationship("WorkCollection", back_populates="work")
    arc_memberships = relationship("WorkArcMembership", back_populates="work")
    activity_entries = relationship("ActivityLedger", back_populates="work")
    reading_statuses = relationship("ReadingStatus", back_populates="work")

    __table_args__ = (
        Index("ix_works_title", "title"),
    )


class WorkCollection(Base):
    __tablename__ = "work_collections"

    id = Column(String(36), primary_key=True, default=_uuid)
    work_id = Column(String(36), ForeignKey("works.work_id"), nullable=False)
    collection_id = Column(String(36), ForeignKey("collections.collection_id"), nullable=False)
    sequence_number = Column(Float, nullable=True)

    work = relationship("Work", back_populates="work_collections")
    collection = relationship("Collection", back_populates="work_collections")


class StoryArc(Base):
    __tablename__ = "story_arcs"

    arc_id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(Text, nullable=False)
    parent_arc_id = Column(String(36), ForeignKey("story_arcs.arc_id"), nullable=True)
    total_parts = Column(Integer, nullable=True)
    completion_status = Column(String(30), nullable=True)  # Complete, Incomplete. Per D-028.
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("StoryArc", remote_side=[arc_id], backref="children")
    work_memberships = relationship("WorkArcMembership", back_populates="arc")


class WorkArcMembership(Base):
    __tablename__ = "work_arc_membership"

    id = Column(String(36), primary_key=True, default=_uuid)
    work_id = Column(String(36), ForeignKey("works.work_id"), nullable=False)
    arc_id = Column(String(36), ForeignKey("story_arcs.arc_id"), nullable=False)
    arc_position = Column(Integer, nullable=True)

    work = relationship("Work", back_populates="arc_memberships")
    arc = relationship("StoryArc", back_populates="work_memberships")


class Artifact(Base):
    __tablename__ = "artifacts"

    artifact_id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(Text, nullable=False)
    format = Column(String(30), nullable=False)
    publisher = Column(Text, nullable=True)
    edition_year = Column(Integer, nullable=True)
    isbn_or_upc = Column(Text, nullable=True)
    is_reprint = Column(Boolean, nullable=False, default=False)
    original_publisher = Column(Text, nullable=True)
    date_added = Column(Date, nullable=True)
    owner = Column(String(30), nullable=False, default=Owner.BANSAL_BROTHERS.value)
    is_pirated = Column(Boolean, nullable=False, default=False)
    issue_number = Column(Text, nullable=True)
    volume_run_id = Column(String(36), ForeignKey("volume_runs.volume_run_id"), nullable=True)
    size = Column(String(10), nullable=True)
    main_genre = Column(Text, nullable=True)
    sous_genre = Column(Text, nullable=True)
    goodreads_url = Column(Text, nullable=True)
    cover_image_path = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    source_sheet = Column(String(30), nullable=True)  # track which xlsx sheet this came from
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    volume_run = relationship("VolumeRun", back_populates="artifacts")
    artifact_works = relationship("ArtifactWork", back_populates="artifact")
    copies = relationship("Copy", back_populates="artifact", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_artifacts_title", "title"),
    )


class ArtifactWork(Base):
    __tablename__ = "artifact_works"

    id = Column(String(36), primary_key=True, default=_uuid)
    artifact_id = Column(String(36), ForeignKey("artifacts.artifact_id"), nullable=False)
    work_id = Column(String(36), ForeignKey("works.work_id"), nullable=False)
    position = Column(Integer, nullable=False, default=1)
    is_partial = Column(Boolean, nullable=False, default=False)
    collects_note = Column(Text, nullable=True)

    artifact = relationship("Artifact", back_populates="artifact_works")
    work = relationship("Work", back_populates="artifact_works")


class Copy(Base):
    __tablename__ = "copies"

    copy_id = Column(String(36), primary_key=True, default=_uuid)
    artifact_id = Column(String(36), ForeignKey("artifacts.artifact_id"), nullable=False)
    copy_number = Column(Integer, nullable=False, default=1)
    internal_sku = Column(Text, nullable=True)
    location = Column(String(20), nullable=True)
    condition = Column(Text, nullable=True)
    borrower_name = Column(Text, nullable=True)
    lent_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    artifact = relationship("Artifact", back_populates="copies")


class ActivityLedger(Base):
    __tablename__ = "activity_ledger"

    log_id = Column(String(36), primary_key=True, default=_uuid)
    user_profile = Column(String(20), nullable=False)
    work_id = Column(String(36), ForeignKey("works.work_id"), nullable=False)
    event_type = Column(String(30), nullable=False)
    event_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False)

    work = relationship("Work", back_populates="activity_entries")


class ReadingStatus(Base):
    __tablename__ = "reading_status"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_profile = Column(String(20), nullable=False)
    work_id = Column(String(36), ForeignKey("works.work_id"), nullable=False)
    status = Column(String(20), nullable=False, default=ReadingStatusEnum.UNREAD.value)
    current_rating = Column(Float, nullable=True)
    last_event_at = Column(DateTime, nullable=True)

    work = relationship("Work", back_populates="reading_statuses")

    __table_args__ = (
        UniqueConstraint("user_profile", "work_id", name="uq_reading_status_profile_work"),
    )


class FieldProvenance(Base):
    __tablename__ = "field_provenance"

    id = Column(String(36), primary_key=True, default=_uuid)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(String(36), nullable=False)
    field_name = Column(Text, nullable=False)
    source = Column(String(40), nullable=False)
    source_url = Column(Text, nullable=True)
    approved = Column(Boolean, nullable=False, default=False)
    scraped_at = Column(DateTime, nullable=True)


class DataQualityFlag(Base):
    __tablename__ = "data_quality_flags"

    flag_id = Column(String(36), primary_key=True, default=_uuid)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(String(36), nullable=False)
    flag_type = Column(String(30), nullable=False)
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=FlagStatus.OPEN.value)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Table creation helper
# ---------------------------------------------------------------------------

def create_all_tables():
    """Create all tables. Idempotent — skips existing tables."""
    Base.metadata.create_all(ENGINE)


def drop_all_tables():
    """Drop all tables for clean-slate migration reruns."""
    Base.metadata.drop_all(ENGINE)
