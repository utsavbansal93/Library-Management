"""Tests for global search endpoint."""


def test_search_finds_works(client, seed_works):
    resp = client.get("/api/search", params={"q": "Batman"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["works"]) >= 2


def test_search_finds_creators(client, seed_creators):
    resp = client.get("/api/search", params={"q": "Rucka"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["creators"]) == 2


def test_search_finds_arcs(client, seed_arc):
    resp = client.get("/api/search", params={"q": "Knightfall"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["arcs"]) == 1


def test_search_finds_collections(client, seed_collection):
    resp = client.get("/api/search", params={"q": "DC"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["collections"]) == 1


def test_search_requires_query(client):
    resp = client.get("/api/search")
    assert resp.status_code == 422  # validation error


def test_search_no_results(client):
    resp = client.get("/api/search", params={"q": "zzzznonexistentzzzz"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(len(v) == 0 for v in data.values())
