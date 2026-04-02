"""Tests for activity ledger and reading_status cache auto-update."""


def test_log_activity_updates_reading_status(client, seed_works, db):
    """Critical test: posting activity auto-updates reading_status cache."""
    from models import ReadingStatus

    work_id = "work-1"

    # Start reading
    resp = client.post("/api/activity", json={
        "user_profile": "Utsav",
        "work_id": work_id,
        "event_type": "Started_Reading",
        "timestamp": "2026-03-01T10:00:00",
    })
    assert resp.status_code == 201

    # Check reading_status was created
    rs = db.query(ReadingStatus).filter(
        ReadingStatus.user_profile == "Utsav",
        ReadingStatus.work_id == work_id,
    ).first()
    assert rs is not None
    assert rs.status == "Reading"

    # Finish reading
    resp2 = client.post("/api/activity", json={
        "user_profile": "Utsav",
        "work_id": work_id,
        "event_type": "Finished_Reading",
        "timestamp": "2026-03-05T10:00:00",
    })
    assert resp2.status_code == 201

    db.expire_all()
    rs = db.query(ReadingStatus).filter(
        ReadingStatus.user_profile == "Utsav",
        ReadingStatus.work_id == work_id,
    ).first()
    assert rs.status == "Finished"

    # Rate it
    resp3 = client.post("/api/activity", json={
        "user_profile": "Utsav",
        "work_id": work_id,
        "event_type": "Rated",
        "event_value": "4.5",
        "timestamp": "2026-03-05T11:00:00",
    })
    assert resp3.status_code == 201

    db.expire_all()
    rs = db.query(ReadingStatus).filter(
        ReadingStatus.user_profile == "Utsav",
        ReadingStatus.work_id == work_id,
    ).first()
    assert rs.status == "Finished"  # status unchanged by rating
    assert rs.current_rating == 4.5


def test_abandon_sets_dnf(client, seed_works, db):
    from models import ReadingStatus

    client.post("/api/activity", json={
        "user_profile": "Utkarsh",
        "work_id": "work-2",
        "event_type": "Started_Reading",
        "timestamp": "2026-03-01T10:00:00",
    })
    client.post("/api/activity", json={
        "user_profile": "Utkarsh",
        "work_id": "work-2",
        "event_type": "Abandoned/DNF",
        "timestamp": "2026-03-10T10:00:00",
    })

    db.expire_all()
    rs = db.query(ReadingStatus).filter(
        ReadingStatus.user_profile == "Utkarsh",
        ReadingStatus.work_id == "work-2",
    ).first()
    assert rs.status == "DNF"


def test_list_activity(client, seed_works):
    # Post some activity
    client.post("/api/activity", json={
        "user_profile": "Utsav",
        "work_id": "work-1",
        "event_type": "Started_Reading",
        "timestamp": "2026-03-01T10:00:00",
    })
    resp = client.get("/api/activity", params={
        "work_id": "work-1",
        "profile": "Utsav",
    })
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_activity_nonexistent_work(client):
    resp = client.post("/api/activity", json={
        "user_profile": "Utsav",
        "work_id": "nonexistent",
        "event_type": "Started_Reading",
        "timestamp": "2026-03-01T10:00:00",
    })
    assert resp.status_code == 404
