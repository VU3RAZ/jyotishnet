# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Saved charts, their notes and life events: a local SQLite file behind the API (M3.1).

The file lives at $JYOTISHNET_DB, or $XDG_DATA_HOME/jyotishnet/jyotishnet.db
(~/.local/share/jyotishnet/jyotishnet.db). Nothing leaves the machine; birth data are
personal data, so the file is created readable by its owner only.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS charts (
    id       INTEGER PRIMARY KEY,
    name     TEXT NOT NULL,
    birth    TEXT NOT NULL,              -- JSON: local_datetime, latitude, longitude, utc_offset_hours, ...
    place    TEXT NOT NULL DEFAULT '',
    events   TEXT NOT NULL DEFAULT '[]', -- JSON list of {type, date, note?}
    created  TEXT NOT NULL,
    updated  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notes (
    id       INTEGER PRIMARY KEY,
    chart_id INTEGER NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
    text     TEXT NOT NULL,
    created  TEXT NOT NULL,
    updated  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_chart ON notes(chart_id);
CREATE TABLE IF NOT EXISTS feedback (      -- reading factors accepted or rejected (M3.4)
    id       INTEGER PRIMARY KEY,
    chart_id INTEGER REFERENCES charts(id) ON DELETE SET NULL,
    birth    TEXT,
    topic    TEXT NOT NULL,
    factor   TEXT NOT NULL,
    verdict  TEXT NOT NULL CHECK (verdict IN ('accept', 'reject')),
    created  TEXT NOT NULL
);
"""


def default_path() -> Path:
    if os.environ.get("JYOTISHNET_DB"):
        return Path(os.environ["JYOTISHNET_DB"])
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "jyotishnet" / "jyotishnet.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class Store:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else default_path()
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self.path.touch(mode=0o600)
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript(SCHEMA)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ charts
    @staticmethod
    def _chart(row: sqlite3.Row, notes: list[dict] | None = None, note_count: int | None = None) -> dict:
        out = {"id": row["id"], "name": row["name"], "birth": json.loads(row["birth"]),
               "place": row["place"], "events": json.loads(row["events"]),
               "created": row["created"], "updated": row["updated"]}
        if notes is not None:
            out["notes"] = notes
        if note_count is not None:
            out["note_count"] = note_count
        return out

    def list_charts(self, query: str = "") -> list[dict]:
        with self._lock:
            rows = self._db.execute(
                "SELECT c.*, (SELECT COUNT(*) FROM notes n WHERE n.chart_id = c.id) AS nn "
                "FROM charts c WHERE c.name LIKE ? OR c.place LIKE ? ORDER BY c.updated DESC, c.id DESC",
                (f"%{query}%", f"%{query}%")).fetchall()
        return [self._chart(r, note_count=r["nn"]) for r in rows]

    def create_chart(self, name: str, birth: dict, place: str = "", events: list | None = None) -> dict:
        t = _now()
        with self._lock, self._db:
            cur = self._db.execute(
                "INSERT INTO charts (name, birth, place, events, created, updated) VALUES (?,?,?,?,?,?)",
                (name, json.dumps(birth), place, json.dumps(events or []), t, t))
        return self.get_chart(cur.lastrowid)

    def get_chart(self, chart_id: int) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM charts WHERE id = ?", (chart_id,)).fetchone()
            if row is None:
                return None
            notes = [dict(n) for n in self._db.execute(
                "SELECT id, text, created, updated FROM notes WHERE chart_id = ? ORDER BY created, id",
                (chart_id,))]
        return self._chart(row, notes)

    def update_chart(self, chart_id: int, **fields) -> dict | None:
        cols = {k: (json.dumps(v) if k in ("birth", "events") else v)
                for k, v in fields.items() if v is not None and k in ("name", "birth", "place", "events")}
        if self.get_chart(chart_id) is None:
            return None
        if cols:
            sets = ", ".join(f"{k} = ?" for k in cols)
            with self._lock, self._db:
                self._db.execute(f"UPDATE charts SET {sets}, updated = ? WHERE id = ?",
                                 (*cols.values(), _now(), chart_id))
        return self.get_chart(chart_id)

    def delete_chart(self, chart_id: int) -> bool:
        with self._lock, self._db:
            return self._db.execute("DELETE FROM charts WHERE id = ?", (chart_id,)).rowcount > 0

    # ------------------------------------------------------------------- notes
    def add_note(self, chart_id: int, text: str) -> dict | None:
        if self.get_chart(chart_id) is None:
            return None
        t = _now()
        with self._lock, self._db:
            cur = self._db.execute("INSERT INTO notes (chart_id, text, created, updated) VALUES (?,?,?,?)",
                                   (chart_id, text, t, t))
            self._db.execute("UPDATE charts SET updated = ? WHERE id = ?", (t, chart_id))
        return {"id": cur.lastrowid, "text": text, "created": t, "updated": t}

    def update_note(self, note_id: int, text: str) -> dict | None:
        t = _now()
        with self._lock, self._db:
            if self._db.execute("UPDATE notes SET text = ?, updated = ? WHERE id = ?",
                                (text, t, note_id)).rowcount == 0:
                return None
            row = self._db.execute("SELECT id, text, created, updated FROM notes WHERE id = ?",
                                   (note_id,)).fetchone()
        return dict(row)

    def delete_note(self, note_id: int) -> bool:
        with self._lock, self._db:
            return self._db.execute("DELETE FROM notes WHERE id = ?", (note_id,)).rowcount > 0

    # ---------------------------------------------------------------- feedback
    def add_feedback(self, topic: str, factor: str, verdict: str, chart_id: int | None = None,
                     birth: dict | None = None) -> dict:
        t = _now()
        if chart_id is not None and self.get_chart(chart_id) is None:
            chart_id = None
        with self._lock, self._db:
            cur = self._db.execute(
                "INSERT INTO feedback (chart_id, birth, topic, factor, verdict, created) VALUES (?,?,?,?,?,?)",
                (chart_id, json.dumps(birth) if birth else None, topic, factor, verdict, t))
        return {"id": cur.lastrowid, "topic": topic, "factor": factor, "verdict": verdict, "created": t}

    def feedback(self) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self._db.execute("SELECT * FROM feedback ORDER BY id")]

