"""Tests for story arc endpoints and cross-volume navigation."""


def test_create_arc(client):
    resp = client.post("/api/arcs", json={
        "name": "No Man's Land",
        "total_parts": 80,
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "No Man's Land"


def test_list_arcs(client, seed_arc):
    resp = client.get("/api/arcs")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_arcs_tree(client, seed_arc, db):
    """Tree view should nest child arcs under parents."""
    from models import StoryArc
    child = StoryArc(
        arc_id="arc-child",
        name="Knightfall Part 1",
        parent_arc_id="arc-knightfall",
        total_parts=2,
    )
    db.add(child)
    db.commit()

    resp = client.get("/api/arcs", params={"tree": True})
    assert resp.status_code == 200
    tree = resp.json()
    # Find Knightfall in roots
    kf = next(a for a in tree if a["name"] == "Knightfall")
    assert len(kf["children"]) == 1
    assert kf["children"][0]["name"] == "Knightfall Part 1"


def test_arc_cross_volume_navigation(client, seed_arc, seed_works):
    """Critical test: arc detail shows works from multiple volume runs in order."""
    resp = client.get("/api/arcs/arc-knightfall")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Knightfall"
    assert data["total_parts"] == 4

    works = data["works"]
    assert len(works) == 4

    # Verify reading order interleaves Batman and Detective Comics
    assert works[0]["work"]["title"] == "Batman #492"
    assert works[0]["volume_run"]["name"] == "Batman"
    assert works[0]["arc_position"] == 1

    assert works[1]["work"]["title"] == "Detective Comics #659"
    assert works[1]["volume_run"]["name"] == "Detective Comics"
    assert works[1]["arc_position"] == 2

    assert works[2]["work"]["title"] == "Batman #493"
    assert works[2]["volume_run"]["name"] == "Batman"
    assert works[2]["arc_position"] == 3

    assert works[3]["work"]["title"] == "Detective Comics #660"
    assert works[3]["volume_run"]["name"] == "Detective Comics"
    assert works[3]["arc_position"] == 4


def test_update_arc(client, seed_arc):
    resp = client.put("/api/arcs/arc-knightfall", json={
        "completion_status": "Complete",
    })
    assert resp.status_code == 200
    assert resp.json()["completion_status"] == "Complete"
