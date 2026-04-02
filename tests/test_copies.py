"""Tests for copy update and lending workflow."""


def test_update_copy(client, seed_copy):
    resp = client.put("/api/copies/copy-1", json={
        "condition": "Fair",
    })
    assert resp.status_code == 200
    assert resp.json()["condition"] == "Fair"


def test_lending_flow(client, seed_copy):
    """Critical test: full lend → return cycle."""
    # Lend the copy
    resp = client.put("/api/copies/copy-1/lend", json={
        "borrower_name": "Utkarsh",
        "lent_date": "2026-03-15",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["location"] == "Lent"
    assert data["borrower_name"] == "Utkarsh"
    assert data["lent_date"] == "2026-03-15"

    # Cannot lend again while already lent
    resp2 = client.put("/api/copies/copy-1/lend", json={
        "borrower_name": "Som",
    })
    assert resp2.status_code == 409

    # Return the copy
    resp3 = client.put("/api/copies/copy-1/return", json={
        "location": "Small Shelf",
    })
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["location"] == "Small Shelf"
    assert data3["borrower_name"] is None
    assert data3["lent_date"] is None


def test_return_not_lent(client, seed_copy):
    """Cannot return a copy that isn't lent out."""
    resp = client.put("/api/copies/copy-1/return", json={})
    assert resp.status_code == 409


def test_lend_default_date(client, seed_copy):
    """Lend without explicit date defaults to today."""
    resp = client.put("/api/copies/copy-1/lend", json={
        "borrower_name": "Friend",
    })
    assert resp.status_code == 200
    assert resp.json()["lent_date"] is not None


def test_return_default_location(client, seed_copy):
    """Return without explicit location defaults to Large Shelf."""
    # First lend it
    client.put("/api/copies/copy-1/lend", json={"borrower_name": "Someone"})
    # Return without specifying location
    resp = client.put("/api/copies/copy-1/return", json={})
    assert resp.status_code == 200
    assert resp.json()["location"] == "Large Shelf"
