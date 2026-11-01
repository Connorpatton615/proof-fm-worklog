"""Shared test fixtures: a fresh app and database per test."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    """An API client backed by an empty SQLite file in a temp folder."""
    app = create_app(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


VALID_VISIT = {
    "site": "North Plant",
    "asset_tag": "AHU-07",
    "technician": "J. Rivera",
    "note": "Replaced belt, checked filters, no further action.",
    "photo_filename": "ahu-07-belt.jpg",
}
