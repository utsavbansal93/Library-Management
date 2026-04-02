"""
Shared test fixtures: in-memory SQLite DB, TestClient, seed data.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from models import Base, _uuid
from models import (
    Creator, CreatorRole, VolumeRun, Work, Artifact, ArtifactWork,
    Copy, Collection, WorkCollection, StoryArc, WorkArcMembership,
    ActivityLedger, ReadingStatus, DataQualityFlag,
)
from database import get_db
from main import app


# --- In-memory database setup ---
# Use StaticPool + check_same_thread=False so all connections share
# the same in-memory database.

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)

# Force SQLAlchemy to reuse the same connection for the in-memory DB
# so that tables created in one session are visible in another.
from sqlalchemy.pool import StaticPool

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSession = sessionmaker(bind=TEST_ENGINE)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(TEST_ENGINE)
    yield
    Base.metadata.drop_all(TEST_ENGINE)


@pytest.fixture
def db():
    """Yield a test DB session."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Yield a FastAPI TestClient."""
    return TestClient(app)


# --- Seed data fixtures ---

@pytest.fixture
def seed_creators(db):
    """Two creators for merge testing."""
    c1 = Creator(
        creator_id="creator-1",
        first_name="Greg",
        last_name="Rucka",
        display_name="Greg Rucka",
        sort_name="Rucka, Greg",
    )
    c2 = Creator(
        creator_id="creator-2",
        first_name="Gregg",
        last_name="Rucka",
        display_name="Gregg Rucka",
        sort_name="Rucka, Gregg",
        aliases=["G. Rucka"],
    )
    db.add_all([c1, c2])
    db.commit()
    return c1, c2


@pytest.fixture
def seed_volume_runs(db):
    """Two volume runs for cross-volume arc testing."""
    vr1 = VolumeRun(
        volume_run_id="vr-batman",
        name="Batman",
        publisher="DC Comics",
        start_year=1940,
    )
    vr2 = VolumeRun(
        volume_run_id="vr-detective",
        name="Detective Comics",
        publisher="DC Comics",
        start_year=1937,
    )
    db.add_all([vr1, vr2])
    db.commit()
    return vr1, vr2


@pytest.fixture
def seed_works(db, seed_volume_runs):
    """Works across two volume runs for arc testing."""
    vr1, vr2 = seed_volume_runs
    works = []
    for i, (title, vr_id, issue) in enumerate([
        ("Batman #492", "vr-batman", "492"),
        ("Detective Comics #659", "vr-detective", "659"),
        ("Batman #493", "vr-batman", "493"),
        ("Detective Comics #660", "vr-detective", "660"),
    ]):
        w = Work(
            work_id="work-%d" % (i + 1),
            title=title,
            work_type="Comic Story",
            volume_run_id=vr_id,
            issue_number=issue,
        )
        works.append(w)
    db.add_all(works)
    db.commit()
    return works


@pytest.fixture
def seed_arc(db, seed_works):
    """A Knightfall-style arc spanning two volume runs."""
    arc = StoryArc(
        arc_id="arc-knightfall",
        name="Knightfall",
        total_parts=4,
        completion_status="Incomplete",
    )
    db.add(arc)
    db.flush()

    for i, work in enumerate(seed_works):
        m = WorkArcMembership(
            id=_uuid(),
            work_id=work.work_id,
            arc_id="arc-knightfall",
            arc_position=i + 1,
        )
        db.add(m)
    db.commit()
    return arc


@pytest.fixture
def seed_dual_story_artifact(db):
    """An artifact containing two works (dual-story issue)."""
    w1 = Work(
        work_id="work-dual-1",
        title="Story A",
        work_type="Comic Story",
    )
    w2 = Work(
        work_id="work-dual-2",
        title="Story B",
        work_type="Comic Story",
    )
    art = Artifact(
        artifact_id="artifact-dual",
        title="Batman #22 (dual-story)",
        format="Comic Issue",
        publisher="DC Comics",
    )
    db.add_all([w1, w2, art])
    db.flush()

    aw1 = ArtifactWork(
        id=_uuid(), artifact_id="artifact-dual",
        work_id="work-dual-1", position=1,
    )
    aw2 = ArtifactWork(
        id=_uuid(), artifact_id="artifact-dual",
        work_id="work-dual-2", position=2,
    )
    db.add_all([aw1, aw2])
    db.commit()
    return art, w1, w2


@pytest.fixture
def seed_copy(db, seed_dual_story_artifact):
    """A lendable copy attached to the dual-story artifact."""
    art, _, _ = seed_dual_story_artifact
    copy = Copy(
        copy_id="copy-1",
        artifact_id=art.artifact_id,
        copy_number=1,
        location="Large Shelf",
        condition="Good",
    )
    db.add(copy)
    db.commit()
    return copy


@pytest.fixture
def seed_collection(db, seed_works):
    """A collection with works."""
    coll = Collection(
        collection_id="coll-1",
        name="DC Universe",
        collection_type="Universe/Franchise",
    )
    db.add(coll)
    db.flush()

    for i, w in enumerate(seed_works[:2]):
        wc = WorkCollection(
            id=_uuid(),
            work_id=w.work_id,
            collection_id="coll-1",
            sequence_number=float(i + 1),
        )
        db.add(wc)
    db.commit()
    return coll


@pytest.fixture
def seed_creator_roles(db, seed_creators, seed_works):
    """Assign creator roles for merge testing."""
    c1, c2 = seed_creators
    roles = [
        CreatorRole(
            id=_uuid(), creator_id=c1.creator_id,
            target_type="work", target_id=seed_works[0].work_id,
            role="Writer",
        ),
        CreatorRole(
            id=_uuid(), creator_id=c2.creator_id,
            target_type="work", target_id=seed_works[1].work_id,
            role="Writer",
        ),
    ]
    db.add_all(roles)
    db.commit()
    return roles


@pytest.fixture
def seed_flags(db):
    """Data quality flags for testing."""
    flags = [
        DataQualityFlag(
            flag_id="flag-1",
            entity_type="artifact",
            entity_id="some-artifact",
            flag_type="missing_isbn",
            description="No ISBN found",
            status="open",
        ),
        DataQualityFlag(
            flag_id="flag-2",
            entity_type="creator",
            entity_id="some-creator",
            flag_type="name_inconsistency",
            description="Name mismatch",
            status="open",
        ),
    ]
    db.add_all(flags)
    db.commit()
    return flags
