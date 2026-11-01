"""API tests for the per-site summary."""

from tests.conftest import VALID_VISIT


def test_summary_rolls_up_visits_at_one_site(client):
    client.post("/visits", json={**VALID_VISIT, "visited_at": "2026-03-01T09:00:00Z"})
    client.post("/visits", json={**VALID_VISIT, "visited_at": "2026-03-03T09:00:00Z"})
    client.post(
        "/visits",
        json={
            **VALID_VISIT,
            "asset_tag": "RTU-02",
            "technician": "A. Chen",
            "visited_at": "2026-03-02T09:00:00Z",
        },
    )
    # A visit at another site must not leak into this summary.
    client.post("/visits", json={**VALID_VISIT, "site": "South Depot"})

    response = client.get("/sites/North Plant/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["site"] == "North Plant"
    assert body["visit_count"] == 3
    assert body["first_visit"].startswith("2026-03-01")
    assert body["last_visit"].startswith("2026-03-03")
    assert body["technicians"] == ["A. Chen", "J. Rivera"]
    # Assets ordered by most recent visit; counts are per asset.
    assert [(a["asset_tag"], a["visit_count"]) for a in body["assets"]] == [
        ("AHU-07", 2),
        ("RTU-02", 1),
    ]


def test_summary_for_unknown_site_is_404_not_empty(client):
    response = client.get("/sites/Nowhere/summary")
    assert response.status_code == 404
    assert "Nowhere" in response.json()["detail"]
