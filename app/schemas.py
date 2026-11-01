"""Request and response shapes.

Validation lives here so the route handlers stay short. Anything that fails
these rules is rejected with HTTP 422 before it touches the database.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

# A photo filename is just a name. Slashes, backslashes and ".." are refused
# so a caller can never smuggle a path into the log.
PHOTO_FILENAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"


class VisitIn(BaseModel):
    """What a technician sends when logging a visit."""

    model_config = ConfigDict(str_strip_whitespace=True)

    site: str = Field(min_length=1, max_length=80, examples=["North Plant"])
    asset_tag: str = Field(min_length=1, max_length=40, examples=["AHU-07"])
    technician: str = Field(min_length=1, max_length=80, examples=["J. Rivera"])
    note: str = Field(
        min_length=1,
        max_length=2000,
        examples=["Replaced belt, checked filters, no further action."],
    )
    photo_filename: str | None = Field(
        default=None,
        max_length=120,
        pattern=PHOTO_FILENAME_PATTERN,
        examples=["ahu-07-belt.jpg"],
    )
    visited_at: datetime | None = Field(
        default=None,
        description="When the visit happened. Defaults to now (UTC).",
    )

    def resolved_visited_at(self) -> datetime:
        """Return the visit time in UTC, defaulting to the current time."""
        when = self.visited_at or datetime.now(timezone.utc)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        return when.astimezone(timezone.utc)


class VisitOut(VisitIn):
    """A stored visit: the input plus its id and resolved timestamp."""

    id: int
    visited_at: datetime


class AssetSummary(BaseModel):
    """How often one asset at a site has been visited, and when last."""

    asset_tag: str
    visit_count: int
    last_visit: datetime


class SiteSummary(BaseModel):
    """Everything a manager wants to know about a site in one call."""

    site: str
    visit_count: int
    first_visit: datetime
    last_visit: datetime
    technicians: list[str]
    assets: list[AssetSummary]
