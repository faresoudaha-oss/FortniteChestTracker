"""Stockage SQLite local des statistiques."""
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .config import data_dir

SCHEMA = """
CREATE TABLE IF NOT EXISTS replays(
  path TEXT PRIMARY KEY, name TEXT, size INTEGER, mtime REAL,
  status TEXT NOT NULL, error TEXT, analyzed_at TEXT);
CREATE TABLE IF NOT EXISTS matches(
  id INTEGER PRIMARY KEY AUTOINCREMENT, replay_path TEXT UNIQUE NOT NULL,
  played_at TEXT, duration_s INTEGER, mode TEXT, opened INTEGER NOT NULL, destroyed INTEGER NOT NULL,
  certainty TEXT NOT NULL, note TEXT);
CREATE TABLE IF NOT EXISTS chest_events(
  id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  t_ms INTEGER, kind TEXT, action TEXT, actor TEXT, certain INTEGER);
"""


@dataclass
class MatchRecord:
    replay_path: str
    played_at: str | None
    duration_s: int
    mode: str
    opened: int
    destroyed: int
    certainty: str     # certaine | incertaine | indisponible
    note: str = ""
    events: list | None = None


class Database:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else data_dir() / "stats.db"
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def status_of(self, path):
        with self._conn() as c:
            r = c.execute("SELECT status FROM replays WHERE path=?", (str(path),)).fetchone()
            return r[0] if r else None

    def mark_error(self, path, name, size, mtime, error):
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO replays VALUES(?,?,?,?,?,?,datetime('now','localtime'))",
                      (str(path), name, size, mtime, "erreur", error))

    def save_match(self, name, size, mtime, m: MatchRecord):
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO replays VALUES(?,?,?,?,?,?,datetime('now','localtime'))",
                      (m.replay_path, name, size, mtime, "analysée", None))
            c.execute("DELETE FROM matches WHERE replay_path=?", (m.replay_path,))
            cur = c.execute("INSERT INTO matches(replay_path,played_at,duration_s,mode,opened,destroyed,certainty,note)"
                            " VALUES(?,?,?,?,?,?,?,?)",
                            (m.replay_path, m.played_at, m.duration_s, m.mode, m.opened, m.destroyed, m.certainty, m.note))
            for e in (m.events or []):
                c.execute("INSERT INTO chest_events(match_id,t_ms,kind,action,actor,certain) VALUES(?,?,?,?,?,?)",
                          (cur.lastrowid, e.t_ms, e.kind, e.action, e.actor, int(e.certain)))

    def totals(self) -> dict:
        with self._conn() as c:
            r = c.execute("SELECT COUNT(*) n, COALESCE(SUM(opened),0) o, COALESCE(SUM(destroyed),0) d FROM matches").fetchone()
            last = c.execute("SELECT * FROM matches ORDER BY COALESCE(played_at,'') DESC, id DESC LIMIT 1").fetchone()
        n = r["n"]
        return {"matches": n, "opened": r["o"], "destroyed": r["d"],
                "avg": (r["o"] / n) if n else 0.0, "last": dict(last) if last else None}

    def matches(self) -> list:
        with self._conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM matches ORDER BY COALESCE(played_at,'') DESC, id DESC")]

    def events(self, match_id) -> list:
        with self._conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM chest_events WHERE match_id=? ORDER BY t_ms", (match_id,))]

    def replays(self) -> list:
        with self._conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM replays ORDER BY mtime DESC")]

    def reset(self):
        with self._conn() as c:
            c.execute("DELETE FROM chest_events")
            c.execute("DELETE FROM matches")
            c.execute("DELETE FROM replays")
