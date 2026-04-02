"""Tests for data quality flag endpoints."""


def test_list_open_flags(client, seed_flags):
    resp = client.get("/api/flags")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_filter_flags_by_type(client, seed_flags):
    resp = client.get("/api/flags", params={"type": "missing_isbn"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["flag_type"] == "missing_isbn"


def test_resolve_flag(client, seed_flags):
    resp = client.put("/api/flags/flag-1", json={
        "action": "resolve",
        "applied_fix": "Added ISBN 978-1234567890",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None

    # Should no longer appear in default (open) list
    resp2 = client.get("/api/flags")
    ids = [f["flag_id"] for f in resp2.json()]
    assert "flag-1" not in ids


def test_dismiss_flag(client, seed_flags):
    resp = client.put("/api/flags/flag-2", json={"action": "dismiss"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "dismissed"


def test_invalid_flag_action(client, seed_flags):
    resp = client.put("/api/flags/flag-1", json={"action": "invalid"})
    assert resp.status_code == 400
