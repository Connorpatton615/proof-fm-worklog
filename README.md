# Field Work Log

A small web service for recording technician site visits and reading them
back. A technician logs what they did to which piece of equipment at which
site. A manager lists the visits for a site to see what has happened there.

This repository is deliberately small. It exists to show, end to end, how I
build and ship an internal tool: the code, the tests, the deployment files,
the runbook, and the pull-request habits that go with them.

[![tests](https://github.com/Connorpatton615/proof-fm-worklog/actions/workflows/tests.yml/badge.svg)](https://github.com/Connorpatton615/proof-fm-worklog/actions/workflows/tests.yml)

## For managers: what it does

- A technician records a **visit**: the site, the asset tag on the equipment,
  a note about what was done, and optionally the filename of a photo they
  took. The time is stamped automatically.
- Anyone with access can **list visits**, newest first, for one site or for
  all sites.
- A manager pulls a **per-site summary**: how many visits, first and last
  date, which technicians have been there, and which assets get the most
  attention.
- The data lives in a single file on the server. Backing it up is copying
  one file. Restoring it is copying it back. See the [runbook](docs/runbook.md).

What it does **not** do, on purpose:

- No user accounts or passwords. It is meant to sit behind whatever access
  control the network already has (a VPN or a reverse proxy). Adding sign-in
  would be the first real change if this went to production.
- No photo storage. It records the photo's filename so the visit and the
  photo can be matched up later; the photo itself stays wherever the phone
  or shared drive put it.
- No editing or deleting of visits. A log is a log. A wrong entry gets a
  follow-up entry.

## For engineers: how to run it

Requires Python 3.12. Two commands from a fresh checkout:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is then at <http://127.0.0.1:8000> and the interactive documentation
(every endpoint, with a try-it button) at <http://127.0.0.1:8000/docs>.
The database file is created on first start at `data/worklog.db`.

Log a visit:

```bash
curl -X POST http://127.0.0.1:8000/visits \
  -H 'content-type: application/json' \
  -d '{"site": "North Plant", "asset_tag": "AHU-07", "technician": "J. Rivera",
       "note": "Replaced belt, checked filters.", "photo_filename": "ahu-07-belt.jpg"}'
```

List the visits at one site:

```bash
curl 'http://127.0.0.1:8000/visits?site=North%20Plant'
```

Summarise a site:

```bash
curl 'http://127.0.0.1:8000/sites/North%20Plant/summary'
```

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Service is up and the database answers. Used by the deployment health check. |
| `POST` | `/visits` | Record a visit. Returns the stored record with its `id`. |
| `GET` | `/visits` | List visits, newest first. Optional `?site=` filter, `?limit=` (default 100). |
| `GET` | `/sites/{site}/summary` | Roll-up for one site: visit count, date range, technicians, per-asset counts. 404 if the site has no visits. |

Input rules are in [`app/schemas.py`](app/schemas.py). Bad input gets an
HTTP 422 with a message naming the field; nothing is written.

### Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Every test runs against a fresh temporary database, so the suite never
touches real data and needs no setup. The same command runs in GitHub
Actions on every pull request ([workflow](.github/workflows/tests.yml)).

### How it is deployed

The [`Dockerfile`](Dockerfile) builds a single-process image. The
[`fly.toml`](fly.toml) runs that image on [Fly.io](https://fly.io) as one
machine with a persistent volume mounted at `/data`, where the SQLite file
lives. One machine, not many, because SQLite is a single-writer database and
this tool does not need more. The health check hits `/health` every 30
seconds. Day-to-day operations (start, stop, back up, restore, what to check
when it misbehaves) are in [`docs/runbook.md`](docs/runbook.md).

### Layout

```
app/
  main.py      routes
  schemas.py   request/response shapes and validation rules
  db.py        SQLite schema and connection
tests/         pytest suite, one fixture, one file per concern
docs/          runbook
.github/       CI workflow
Dockerfile, fly.toml, requirements*.txt
```

About 200 lines of application code. Stack: Python 3.12, FastAPI, SQLite
from the standard library. No ORM, no framework beyond FastAPI, nothing to
learn before reading it.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the pull-request rules this
repository follows. They are the same rules I use on private work.

## Licence

[MIT](LICENSE).
