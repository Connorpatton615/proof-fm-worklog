"""HTTP routes for the field work log.

Run locally with:  uvicorn app.main:app --reload
Interactive docs:  http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, Query
from sqlite3 import Connection

from app import db
from app.schemas import VisitIn, VisitOut

VISIT_COLUMNS = (
    "id, site, asset_tag, technician, note, photo_filename, visited_at"
)


def create_app(db_path: str | os.PathLike[str] | None = None) -> FastAPI:
    """Build the application against one database file.

    Tests call this with a temporary path. Production uses the default, which
    reads the WORKLOG_DB environment variable.
    """
    path: Path = db.resolve_db_path(db_path)
    db.init_db(path)

    app = FastAPI(
        title="Field Work Log",
        version="0.1.0",
        description="Technicians log site visits; managers read them back.",
    )

    def get_conn():
        conn = db.connect(path)
        try:
            yield conn
        finally:
            conn.close()

    @app.get("/health", tags=["ops"])
    def health(conn: Connection = Depends(get_conn)) -> dict:
        """Confirm the service is up and the database answers."""
        count = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        return {"status": "ok", "visits": count}

    @app.post("/visits", response_model=VisitOut, status_code=201, tags=["visits"])
    def create_visit(visit: VisitIn, conn: Connection = Depends(get_conn)) -> VisitOut:
        """Record one visit to one asset at one site."""
        visited_at = visit.resolved_visited_at()
        with conn:
            cur = conn.execute(
                "INSERT INTO visits (site, asset_tag, technician, note, "
                "photo_filename, visited_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    visit.site,
                    visit.asset_tag,
                    visit.technician,
                    visit.note,
                    visit.photo_filename,
                    visited_at.isoformat(),
                ),
            )
        return VisitOut(
            id=cur.lastrowid,
            visited_at=visited_at,
            **visit.model_dump(exclude={"visited_at"}),
        )

    @app.get("/visits", response_model=list[VisitOut], tags=["visits"])
    def list_visits(
        site: str | None = Query(default=None, description="Only visits at this site."),
        limit: int = Query(default=100, ge=1, le=1000),
        conn: Connection = Depends(get_conn),
    ) -> list[VisitOut]:
        """List visits, newest first, optionally filtered to one site."""
        sql = f"SELECT {VISIT_COLUMNS} FROM visits"
        params: list[object] = []
        if site is not None:
            sql += " WHERE site = ?"
            params.append(site)
        sql += " ORDER BY visited_at DESC, id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [VisitOut(**dict(row)) for row in rows]

    return app


app = create_app()
