"""Tests for artifact CRUD and dual-story retrieval."""


def test_create_artifact(client):
    resp = client.post("/api/artifacts", json={
        "title": "Batman: Year One",
        "format": "Graphic Novel",
        "publisher": "DC Comics",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Batman: Year One"
    assert data["artifact_id"]


def test_list_artifacts(client, seed_dual_story_artifact):
    resp = client.get("/api/artifacts")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_filter_by_format(client, seed_dual_story_artifact):
    resp = client.get("/api/artifacts", params={"format": "Comic Issue"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_search_artifacts(client, seed_dual_story_artifact):
    resp = client.get("/api/artifacts", params={"q": "dual-story"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_dual_story_artifact_retrieval(client, seed_dual_story_artifact):
    """Critical test: artifact with 2 works returns both with correct positions."""
    resp = client.get("/api/artifacts/artifact-dual")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Batman #22 (dual-story)"

    works = data["artifact_works"]
    assert len(works) == 2
    # Verify ordering by position
    assert works[0]["position"] == 1
    assert works[0]["work"]["title"] == "Story A"
    assert works[1]["position"] == 2
    assert works[1]["work"]["title"] == "Story B"


def test_update_artifact(client, seed_dual_story_artifact):
    resp = client.put("/api/artifacts/artifact-dual", json={
        "notes": "Contains two stories",
    })
    assert resp.status_code == 200


def test_delete_artifact_soft(client, seed_dual_story_artifact):
    resp = client.delete("/api/artifacts/artifact-dual")
    assert resp.status_code == 204

    resp2 = client.get("/api/artifacts/artifact-dual")
    assert resp2.status_code == 404


def test_create_copy_for_artifact(client, seed_dual_story_artifact):
    resp = client.post("/api/artifacts/artifact-dual/copies", json={
        "copy_number": 1,
        "location": "Large Shelf",
        "condition": "Mint",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["artifact_id"] == "artifact-dual"
    assert data["location"] == "Large Shelf"
