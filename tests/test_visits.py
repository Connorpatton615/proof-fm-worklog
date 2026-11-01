"""API tests for logging and listing visits."""

from tests.conftest import VALID_VISIT


def test_health_reports_ok_and_zero_visits(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "visits": 0}


def test_create_visit_returns_record_with_id_and_timestamp(client):
    response = client.post("/visits", json=VALID_VISIT)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["site"] == "North Plant"
    assert body["photo_filename"] == "ahu-07-belt.jpg"
    # visited_at was not supplied, so the server stamped it (UTC, ISO 8601).
    assert body["visited_at"].endswith("Z") or "+00:00" in body["visited_at"]


def test_photo_filename_is_optional(client):
    visit = {k: v for k, v in VALID_VISIT.items() if k != "photo_filename"}
    response = client.post("/visits", json=visit)
    assert response.status_code == 201
    assert response.json()["photo_filename"] is None


def test_list_visits_filters_by_site_newest_first(client):
    client.post("/visits", json={**VALID_VISIT, "visited_at": "2026-03-01T09:00:00Z"})
    client.post("/visits", json={**VALID_VISIT, "visited_at": "2026-03-02T09:00:00Z"})
    client.post("/visits", json={**VALID_VISIT, "site": "South Depot"})

    everything = client.get("/visits").json()
    assert len(everything) == 3

    north = client.get("/visits", params={"site": "North Plant"}).json()
    assert [v["visited_at"][:10] for v in north] == ["2026-03-02", "2026-03-01"]

    assert client.get("/visits", params={"site": "Nowhere"}).json() == []


def test_blank_note_is_rejected(client):
    response = client.post("/visits", json={**VALID_VISIT, "note": "   "})
    assert response.status_code == 422
    assert client.get("/health").json()["visits"] == 0


def test_photo_filename_cannot_contain_a_path(client):
    """Edge case: a filename is a name, never a path.

    If this were accepted, whatever later serves photos from a folder could be
    tricked into reading outside it.
    """
    for bad in ["../../etc/passwd", "photos/ahu.jpg", "C:\\temp\\ahu.jpg", "..", ".hidden"]:
        response = client.post("/visits", json={**VALID_VISIT, "photo_filename": bad})
        assert response.status_code == 422, bad
    assert client.get("/health").json()["visits"] == 0
