"""SQLite storage for visits.

One file, one table. The database path comes from the WORKLOG_DB environment
variable so the same code runs locally (./data/worklog.db) and in a container
(/data/worklog.db on a mounted volume).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = "data/worklog.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS visits (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    site           TEXT NOT NULL,
    asset_tag      TEXT NOT NULL,
    technician     TEXT NOT NULL,
    note           TEXT NOT NULL,
    photo_filename TEXT,
    visited_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_visits_site ON visits (site);
"""


def resolve_db_path(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Pick the database file: explicit argument, then env var, then default."""
    return Path(explicit or os.environ.get("WORKLOG_DB", DEFAULT_DB_PATH))


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a connection with rows addressable by column name."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    """Create the parent folder and the schema if they do not exist yet.

    Safe to call on every start-up: every statement is IF NOT EXISTS.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
