"""
Integration tests for the 7 critical scenarios requested.

All tests run against an in-memory SQLite DB (conftest.py setup_db fixture)
with seed data modeled after real Utskomia Library patterns. No disk writes
to utskomia.db.
"""

from models import (
    Creator, CreatorRole, VolumeRun, Work, Artifact, ArtifactWork,
    Copy, StoryArc, WorkArcMembership, _uuid,
)


# ---------------------------------------------------------------------------
# 1. Retrieve a dual-story issue → verify both Works with correct positions
#    (modeled after Action Comics #9 which contains Superman #213 + #214)
# ---------------------------------------------------------------------------

def test_dual_story_issue_retrieval(client, db):
    """Action Comics #9 contains two Superman stories at positions 1 and 2."""
    vr = VolumeRun(
        volume_run_id="vr-action", name="Action Comics",
        publisher="DC Comics", start_year=1938,
    )
    db.add(vr)
    db.flush()

    w1 = Work(
        work_id="w-superman-213", title="Superman #213",
        work_type="Comic Story", volume_run_id="vr-action",
        issue_number="213",
    )
    w2 = Work(
        work_id="w-superman-214", title="Superman #214",
        work_type="Comic Story", volume_run_id="vr-action",
        issue_number="214",
    )
    art = Artifact(
        artifact_id="art-action-9", title="Action Comics #9",
        format="Comic Issue", publisher="DC Comics",
        volume_run_id="vr-action", issue_number="9",
    )
    db.add_all([w1, w2, art])
    db.flush()

    aw1 = ArtifactWork(
        id=_uuid(), artifact_id="art-action-9",
        work_id="w-superman-213", position=1,
    )
    aw2 = ArtifactWork(
        id=_uuid(), artifact_id="art-action-9",
        work_id="w-superman-214", position=2,
    )
    db.add_all([aw1, aw2])
    db.commit()

    resp = client.get("/api/artifacts/art-action-9")
    assert resp.status_code == 200
    data = resp.json()

    assert data["title"] == "Action Comics #9"
    works = data["artifact_works"]
    assert len(works) == 2, f"Expected 2 works, got {len(works)}"

    assert works[0]["position"] == 1
    assert works[0]["work"]["title"] == "Superman #213"
    assert works[1]["position"] == 2
    assert works[1]["work"]["title"] == "Superman #214"


# ---------------------------------------------------------------------------
# 2. Retrieve Knightfall arc → verify cross-volume reading order
#    (real data: Detective Comics + Batman + Showcase '93 interleaved)
# ---------------------------------------------------------------------------

def test_knightfall_cross_volume_reading_order(client, db):
    """Knightfall arc interleaves Batman, Detective Comics, and Showcase '93."""
    vr_batman = VolumeRun(
        volume_run_id="vr-bat", name="Batman",
        publisher="DC Comics", start_year=1940,
    )
    vr_detective = VolumeRun(
        volume_run_id="vr-det", name="Detective Comics",
        publisher="DC Comics", start_year=1937,
    )
    vr_showcase = VolumeRun(
        volume_run_id="vr-show", name="Showcase '93",
        publisher="DC Comics", start_year=1993,
    )
    db.add_all([vr_batman, vr_detective, vr_showcase])
    db.flush()

    # Modeled after real Knightfall reading order from the DB
    arc_works = [
        ("Detective Comics #659", "vr-det", "659", 2),
        ("Detective Comics #660", "vr-det", "660", 4),
        ("Detective Comics #661", "vr-det", "661", 6),
        ("Batman #496", "vr-bat", "496", 9),
        ("Showcase '93 #7", "vr-show", "7", 13),
        ("Batman #499", "vr-bat", "499", 17),
        ("Batman #500", "vr-bat", "500", 19),
    ]

    works = []
    for title, vr_id, issue, _ in arc_works:
        w = Work(
            work_id=_uuid(), title=title, work_type="Comic Story",
            volume_run_id=vr_id, issue_number=issue,
        )
        works.append(w)
    db.add_all(works)
    db.flush()

    arc = StoryArc(
        arc_id="arc-kf", name="Knightfall",
        total_parts=19, completion_status="Incomplete",
    )
    db.add(arc)
    db.flush()

    for work, (_, _, _, pos) in zip(works, arc_works):
        m = WorkArcMembership(
            id=_uuid(), work_id=work.work_id,
            arc_id="arc-kf", arc_position=pos,
        )
        db.add(m)
    db.commit()

    resp = client.get("/api/arcs/arc-kf")
    assert resp.status_code == 200
    data = resp.json()

    assert data["name"] == "Knightfall"
    assert data["total_parts"] == 19

    arc_entries = data["works"]
    assert len(arc_entries) == 7

    # Verify cross-volume interleaving: positions should be ascending
    positions = [e["arc_position"] for e in arc_entries]
    assert positions == sorted(positions), "Works must be in arc_position order"

    # Verify first entry is Detective Comics (position 2)
    assert arc_entries[0]["work"]["title"] == "Detective Comics #659"
    assert arc_entries[0]["volume_run"]["name"] == "Detective Comics"
    assert arc_entries[0]["arc_position"] == 2

    # Verify Batman appears mid-sequence
    batman_496 = next(e for e in arc_entries if e["work"]["title"] == "Batman #496")
    assert batman_496["volume_run"]["name"] == "Batman"
    assert batman_496["arc_position"] == 9

    # Verify Showcase '93 also appears (three different volume runs)
    showcase = next(e for e in arc_entries if "Showcase" in e["work"]["title"])
    assert showcase["volume_run"]["name"] == "Showcase '93"

    volume_runs_seen = set(e["volume_run"]["name"] for e in arc_entries)
    assert len(volume_runs_seen) == 3, "Should span 3 different volume runs"


# ---------------------------------------------------------------------------
# 3. Create artifact with only title + format → all other fields null
# ---------------------------------------------------------------------------

def test_create_minimal_artifact(client):
    """PRD requires only title + format as minimum fields."""
    resp = client.post("/api/artifacts", json={
        "title": "Mystery Issue",
        "format": "Comic Issue",
    })
    assert resp.status_code == 201
    data = resp.json()

    assert data["title"] == "Mystery Issue"
    assert data["format"] == "Comic Issue"
    assert data["artifact_id"]  # UUID was assigned
    assert data["publisher"] is None
    assert data["issue_number"] is None
    assert data["volume_run"] is None

    # Verify it's retrievable
    resp2 = client.get("/api/artifacts/%s" % data["artifact_id"])
    assert resp2.status_code == 200
    detail = resp2.json()
    assert detail["edition_year"] is None
    assert detail["isbn_or_upc"] is None
    assert detail["goodreads_url"] is None
    assert detail["notes"] is None
    assert detail["size"] is None
    assert detail["main_genre"] is None
    assert detail["sous_genre"] is None


# ---------------------------------------------------------------------------
# 4. Lend a copy → verify borrower_name and location updated
#    (modeled after copy 7c3eed57 on Small Shelf)
# ---------------------------------------------------------------------------

def test_lend_copy_updates_fields(client, db):
    """Lending sets location=Lent, records borrower and date."""
    art = Artifact(
        artifact_id="art-lend-test", title="Action Comics #9",
        format="Comic Issue", publisher="DC Comics",
    )
    copy = Copy(
        copy_id="copy-lend-test", artifact_id="art-lend-test",
        copy_number=1, location="Small Shelf", condition="Good",
    )
    db.add_all([art, copy])
    db.commit()

    resp = client.put("/api/copies/copy-lend-test/lend", json={
        "borrower_name": "Utkarsh",
        "lent_date": "2026-04-01",
    })
    assert resp.status_code == 200
    data = resp.json()

    assert data["location"] == "Lent"
    assert data["borrower_name"] == "Utkarsh"
    assert data["lent_date"] == "2026-04-01"
    assert data["copy_id"] == "copy-lend-test"


# ---------------------------------------------------------------------------
# 5. Return a copy → verify lending info cleared
# ---------------------------------------------------------------------------

def test_return_copy_clears_lending(client, db):
    """Returning restores location and clears borrower fields."""
    from datetime import date
    art = Artifact(
        artifact_id="art-return-test", title="Batman #500",
        format="Comic Issue", publisher="DC Comics",
    )
    copy = Copy(
        copy_id="copy-return-test", artifact_id="art-return-test",
        copy_number=1, location="Lent", condition="Good",
        borrower_name="Friend", lent_date=date(2026, 3, 15),
    )
    db.add_all([art, copy])
    db.commit()

    resp = client.put("/api/copies/copy-return-test/return", json={
        "location": "Large Shelf",
    })
    assert resp.status_code == 200
    data = resp.json()

    assert data["location"] == "Large Shelf"
    assert data["borrower_name"] is None
    assert data["lent_date"] is None


# ---------------------------------------------------------------------------
# 6. Merge two duplicate creators → verify roles transfer
#    (modeled after real Greg/Gregg Rucka merge in v0.1.1)
# ---------------------------------------------------------------------------

def test_creator_merge_transfers_all_roles(client, db):
    """Merging Greg Rucka + Gregg Rucka: roles transfer, aliases merge."""
    w1 = Work(work_id="w-role-1", title="Batman #600", work_type="Comic Story")
    w2 = Work(work_id="w-role-2", title="Gotham Central #1", work_type="Comic Story")
    w3 = Work(work_id="w-role-3", title="Lazarus #1", work_type="Comic Story")
    db.add_all([w1, w2, w3])
    db.flush()

    # Target (correct spelling)
    c_target = Creator(
        creator_id="c-greg", first_name="Greg", last_name="Rucka",
        display_name="Greg Rucka", sort_name="Rucka, Greg",
    )
    # Source (typo duplicate)
    c_source = Creator(
        creator_id="c-gregg", first_name="Gregg", last_name="Rucka",
        display_name="Gregg Rucka", sort_name="Rucka, Gregg",
        aliases=["G. Rucka"],
    )
    db.add_all([c_target, c_source])
    db.flush()

    # Greg wrote Batman #600
    r1 = CreatorRole(
        id=_uuid(), creator_id="c-greg",
        target_type="work", target_id="w-role-1", role="Writer",
    )
    # Gregg (duplicate) wrote Gotham Central #1 and Lazarus #1
    r2 = CreatorRole(
        id=_uuid(), creator_id="c-gregg",
        target_type="work", target_id="w-role-2", role="Writer",
    )
    r3 = CreatorRole(
        id=_uuid(), creator_id="c-gregg",
        target_type="work", target_id="w-role-3", role="Writer",
    )
    db.add_all([r1, r2, r3])
    db.commit()

    # Merge: source (Gregg) → target (Greg)
    resp = client.post("/api/creators/merge", json={
        "source_creator_id": "c-gregg",
        "target_creator_id": "c-greg",
    })
    assert resp.status_code == 200
    data = resp.json()

    assert data["roles_transferred"] == 2
    merged = data["merged_creator"]
    assert merged["display_name"] == "Greg Rucka"
    assert "Gregg Rucka" in merged["aliases"]
    assert "G. Rucka" in merged["aliases"]

    # Verify source creator is gone
    resp2 = client.get("/api/creators/c-gregg")
    assert resp2.status_code == 404

    # Verify all 3 roles now belong to Greg
    resp3 = client.get("/api/creators/c-greg")
    assert resp3.status_code == 200
    assert len(resp3.json()["roles"]) == 3


# ---------------------------------------------------------------------------
# 7. Write Activity Ledger event → verify reading_status cache updated
# ---------------------------------------------------------------------------

def test_activity_event_updates_reading_status_cache(client, db):
    """Started_Reading → cache=Reading, Finished → cache=Finished, Rated → rating set."""
    from models import ReadingStatus

    w = Work(work_id="w-activity-test", title="Watchmen", work_type="Comic Story")
    db.add(w)
    db.commit()

    # Step 1: Start reading
    resp1 = client.post("/api/activity", json={
        "user_profile": "Utsav",
        "work_id": "w-activity-test",
        "event_type": "Started_Reading",
        "timestamp": "2026-03-01T10:00:00",
    })
    assert resp1.status_code == 201

    db.expire_all()
    rs = db.query(ReadingStatus).filter(
        ReadingStatus.user_profile == "Utsav",
        ReadingStatus.work_id == "w-activity-test",
    ).first()
    assert rs is not None, "reading_status row should have been created"
    assert rs.status == "Reading"

    # Step 2: Finish reading
    resp2 = client.post("/api/activity", json={
        "user_profile": "Utsav",
        "work_id": "w-activity-test",
        "event_type": "Finished_Reading",
        "timestamp": "2026-03-10T18:00:00",
    })
    assert resp2.status_code == 201

    db.expire_all()
    rs = db.query(ReadingStatus).filter(
        ReadingStatus.user_profile == "Utsav",
        ReadingStatus.work_id == "w-activity-test",
    ).first()
    assert rs.status == "Finished"

    # Step 3: Rate it
    resp3 = client.post("/api/activity", json={
        "user_profile": "Utsav",
        "work_id": "w-activity-test",
        "event_type": "Rated",
        "event_value": "5.0",
        "timestamp": "2026-03-10T18:05:00",
    })
    assert resp3.status_code == 201

    db.expire_all()
    rs = db.query(ReadingStatus).filter(
        ReadingStatus.user_profile == "Utsav",
        ReadingStatus.work_id == "w-activity-test",
    ).first()
    assert rs.status == "Finished", "Rating should not change status"
    assert rs.current_rating == 5.0

    # Verify all 3 activity entries were logged
    resp4 = client.get("/api/activity", params={
        "work_id": "w-activity-test",
        "profile": "Utsav",
    })
    assert resp4.status_code == 200
    assert len(resp4.json()) == 3
