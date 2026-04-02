"""Tests for collection CRUD and tree views."""


def test_create_collection(client):
    resp = client.post("/api/collections", json={
        "name": "Marvel Universe",
        "collection_type": "Universe/Franchise",
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Marvel Universe"


def test_list_collections(client, seed_collection):
    resp = client.get("/api/collections")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_collection_detail_with_works(client, seed_collection, seed_works):
    resp = client.get("/api/collections/coll-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "DC Universe"
    assert len(data["works"]) == 2


def test_collection_tree(client, seed_collection, db):
    """Tree view nests children correctly."""
    from models import Collection
    child = Collection(
        collection_id="coll-child",
        name="Batman Family",
        collection_type="Series",
        parent_collection_id="coll-1",
    )
    db.add(child)
    db.commit()

    resp = client.get("/api/collections", params={"tree": True})
    assert resp.status_code == 200
    tree = resp.json()
    dc = next(c for c in tree if c["name"] == "DC Universe")
    assert len(dc["children"]) == 1
    assert dc["children"][0]["name"] == "Batman Family"


def test_update_collection(client, seed_collection):
    resp = client.put("/api/collections/coll-1", json={
        "description": "All DC Comics properties",
    })
    assert resp.status_code == 200
