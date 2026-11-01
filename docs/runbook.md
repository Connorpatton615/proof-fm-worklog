# Runbook: Field Work Log

Everything an on-call person needs to operate this service. Written so it can
be followed at 7am without having read the code.

The service is one process and one file:

| Thing | Local | Fly.io |
|---|---|---|
| Process | `uvicorn app.main:app` | one Fly machine, app `proof-fm-worklog` |
| Database | `./data/worklog.db` | `/data/worklog.db` on volume `worklog_data` |
| Health check | `GET /health` | same, hit by Fly every 30 seconds |

The `WORKLOG_DB` environment variable points at the database file. If it is
unset the local default `data/worklog.db` is used.

## Start

Local:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Fly.io (first deploy creates the machine; later deploys replace it):

```bash
fly deploy
```

Confirm it is up:

```bash
curl -s https://proof-fm-worklog.fly.dev/health
# {"status":"ok","visits":1234}
```

## Stop

Local: `Ctrl-C` in the terminal running uvicorn. SQLite closes cleanly; there
is nothing else to shut down.

Fly.io:

```bash
fly machine list                 # note the machine id
fly machine stop <machine-id>
```

Start it again with `fly machine start <machine-id>`. Stopping does not touch
the volume, so the data is still there when it comes back.

## Back up

The database is one SQLite file. Do **not** copy it with `cp` while the
service is running: a write landing mid-copy gives you a corrupt backup.
Use SQLite's own online backup, which is safe while the service is live.

Local:

```bash
mkdir -p backups
sqlite3 data/worklog.db ".backup backups/worklog-$(date +%Y%m%d-%H%M).db"
```

Fly.io (run the backup inside the machine, then pull the file down):

```bash
fly ssh console -C "sqlite3 /data/worklog.db '.backup /data/worklog-backup.db'"
fly ssh sftp get /data/worklog-backup.db ./backups/worklog-$(date +%Y%m%d-%H%M).db
fly ssh console -C "rm /data/worklog-backup.db"
```

Verify a backup before trusting it:

```bash
sqlite3 backups/worklog-20260301-0700.db "PRAGMA integrity_check; SELECT COUNT(*) FROM visits;"
# ok
# 1234
```

The container image installs the `sqlite3` command-line tool for exactly
these steps; the service itself uses Python's built-in SQLite and does not
need it.

## Restore

Restoring replaces the live database with a backup. Visits logged after the
backup was taken are lost, so say so before you do it.

1. Stop the service (see above). Never swap the file under a running process.
2. Put the backup in place:

   Local:
   ```bash
   cp backups/worklog-20260301-0700.db data/worklog.db
   ```

   Fly.io:
   ```bash
   fly ssh sftp shell
   put backups/worklog-20260301-0700.db /data/worklog.db
   ```
3. Start the service.
4. Check `/health` returns `ok` and the `visits` count matches the backup.

## When it misbehaves

Start with these three, in order. Most problems show up in the first one.

1. **`GET /health`.** If it answers `{"status":"ok", ...}` the process and
   database are fine and the problem is in front of the service (network,
   proxy, DNS) or in the request being sent.
2. **Logs.** Local: the terminal running uvicorn. Fly: `fly logs`. Every
   request is logged with its status code. A Python traceback here is a bug;
   copy it into an issue.
3. **Disk.** Fly: `fly ssh console -C "df -h /data"`. SQLite needs free space
   to write. A full volume shows up as HTTP 500 on `POST /visits` while
   `GET` still works.

Specific symptoms:

| Symptom | Likely cause | What to do |
|---|---|---|
| `POST /visits` returns 422 | Input failed validation. The response body names the field. | Fix the request. Common ones: blank note, photo filename containing `/`. Not a server problem. |
| `/health` returns 500, logs say `database is locked` | Another process has the file open for writing (a stray backup, a second instance). | Find and stop it. There should be exactly one process and `max_machines_running = 1` in `fly.toml`. |
| `/health` returns 500, logs say `unable to open database file` | The `data/` folder (local) or volume (Fly) is missing or not writable. | Local: check the working directory. Fly: `fly volumes list`; the volume must be attached to the machine. |
| Service starts but all data is gone | Started against a different `WORKLOG_DB` path, or a new volume. | Check the env var and `fly volumes list`. Data is almost certainly still on the old path or volume. |
| Fly machine keeps restarting | Health check failing during start-up. | `fly logs` for the traceback. Usually a dependency or import error after a change; roll back with `fly releases` and `fly deploy --image <previous>`. |

## Rolling back a bad deploy

```bash
fly releases                       # find the last good version
fly deploy --image <image-from-that-release>
```

The database schema only ever adds (`CREATE TABLE IF NOT EXISTS`), so an
older build runs fine against a newer database file.
