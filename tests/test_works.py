"""Tests for work CRUD endpoints."""


def test_create_work(client):
    resp = client.post("/api/works", json={
        "title": "Watchmen",
        "work_type": "Comic Story",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Watchmen"
    assert data["work_id"]


def test_list_works(client, seed_works):
    resp = client.get("/api/works")
    assert resp.status_code == 200
    assert len(resp.json()) == 4


def test_filter_works_by_type(client, seed_works):
    resp = client.get("/api/works", params={"work_type": "Comic Story"})
    assert resp.status_code == 200
    assert len(resp.json()) == 4


def test_search_works(client, seed_works):
    resp = client.get("/api/works", params={"q": "Batman"})
    assert resp.status_code == 200
    assert all("Batman" in w["title"] for w in resp.json())


def test_get_work_detail(client, seed_works):
    resp = client.get("/api/works/work-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Batman #492"
    assert data["volume_run"] is not None
    assert data["volume_run"]["name"] == "Batman"


def test_update_work(client, seed_works):
    resp = client.put("/api/works/work-1", json={
        "notes": "First part of Knightfall",
    })
    assert resp.status_code == 200


def test_delete_work_soft(client, seed_works):
    resp = client.delete("/api/works/work-1")
    assert resp.status_code == 204

    # Should not appear in list
    resp2 = client.get("/api/works")
    ids = [w["work_id"] for w in resp2.json()]
    assert "work-1" not in ids

    # Should return 404 on detail
    resp3 = client.get("/api/works/work-1")
    assert resp3.status_code == 404


def test_filter_works_by_arc(client, seed_works, seed_arc):
    resp = client.get("/api/works", params={"arc": "arc-knightfall"})
    assert resp.status_code == 200
    assert len(resp.json()) == 4
