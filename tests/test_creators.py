"""Tests for creator CRUD and merge/deduplication."""


def test_create_creator(client):
    resp = client.post("/api/creators", json={
        "display_name": "Alan Moore",
        "sort_name": "Moore, Alan",
        "first_name": "Alan",
        "last_name": "Moore",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["display_name"] == "Alan Moore"
    assert data["sort_name"] == "Moore, Alan"
    assert data["creator_id"]


def test_list_creators(client, seed_creators):
    resp = client.get("/api/creators")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_search_creators(client, seed_creators):
    resp = client.get("/api/creators", params={"q": "Rucka"})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_creator_detail(client, seed_creators):
    resp = client.get("/api/creators/creator-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Greg Rucka"


def test_get_creator_not_found(client):
    resp = client.get("/api/creators/nonexistent")
    assert resp.status_code == 404


def test_update_creator(client, seed_creators):
    resp = client.put("/api/creators/creator-1", json={
        "display_name": "Gregory Rucka",
    })
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Gregory Rucka"


def test_merge_creators(client, seed_creators, seed_works, seed_creator_roles):
    resp = client.post("/api/creators/merge", json={
        "source_creator_id": "creator-2",
        "target_creator_id": "creator-1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["roles_transferred"] == 1
    merged = data["merged_creator"]
    assert merged["display_name"] == "Greg Rucka"
    # Source display_name should be in aliases
    assert "Gregg Rucka" in merged["aliases"]
    # Source's original alias should also be merged
    assert "G. Rucka" in merged["aliases"]

    # Source should be gone
    resp2 = client.get("/api/creators/creator-2")
    assert resp2.status_code == 404


def test_merge_nonexistent_creator(client, seed_creators):
    resp = client.post("/api/creators/merge", json={
        "source_creator_id": "nonexistent",
        "target_creator_id": "creator-1",
    })
    assert resp.status_code == 404
