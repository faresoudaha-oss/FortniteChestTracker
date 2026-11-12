import json
import struct
import sys
from datetime import datetime

import pytest

from fct.analyzer import analyze_file, count_events
from fct.db import Database
from fct.replay_header import ReplayError, parse_header
from fct.scanner import FolderScanner


def fstr(s):
    b = s.encode("latin-1") + b"\0"
    return struct.pack("<i", len(b)) + b


def make_replay(path, version=7, live=False, truncate=0, chunks=((0, b"h" * 10), (1, b"d" * 50))):
    ticks = int((datetime(2026, 11, 1, 12, 0, 0) - datetime(1, 1, 1)).total_seconds() * 10_000_000)
    b = struct.pack("<II", 0x1CA2E27F, version)
    if version >= 7:
        b += struct.pack("<i", 1) + b"\x01" * 16 + struct.pack("<i", 3)
    b += struct.pack("<III", 1_200_000, 25, 999) + fstr("Partie") + struct.pack("<I", int(live))
    b += struct.pack("<q", ticks) + struct.pack("<I", 1) + struct.pack("<I", 1) + struct.pack("<I", 16) + b"k" * 16
    for t, d in chunks:
        b += struct.pack("<Ii", t, len(d)) + d
    path.write_bytes(b[: len(b) - truncate] if truncate else b)
    return path


@pytest.mark.parametrize("version", [6, 7])
def test_header_ok(tmp_path, version):
    info = parse_header(make_replay(tmp_path / "a.replay", version=version))
    assert info.length_ms == 1_200_000 and info.complete and info.friendly_name == "Partie"
    assert info.timestamp == datetime(2026, 11, 1, 12, 0, 0) and info.encrypted


def test_bad_files(tmp_path):
    (tmp_path / "x.replay").write_bytes(b"not a replay at all")
    with pytest.raises(ReplayError):
        parse_header(tmp_path / "x.replay")
    with pytest.raises(ReplayError):
        parse_header(make_replay(tmp_path / "t.replay", truncate=5))
    with pytest.raises(ReplayError):
        analyze_file(make_replay(tmp_path / "l.replay", live=True))


def test_no_backend_invents_nothing(tmp_path, monkeypatch):
       monkeypatch.setattr("fct.analyzer.bundled_exporter", lambda: None)
    m = analyze_file(make_replay(tmp_path / "a.replay"))
    assert (m.opened, m.destroyed, m.certainty) == (0, 0, "indisponible")


def test_count_only_player():
    raw = [
        {"t_ms": 1, "kind": "standard", "action": "opened", "actor": "player", "certain": True},
        {"t_ms": 2, "kind": "rare", "action": "opened", "actor": "teammate", "certain": True},
        {"t_ms": 3, "kind": "sprite", "action": "opened", "actor": "enemy", "certain": True},
        {"t_ms": 4, "kind": "standard", "action": "destroyed", "actor": "player", "certain": True},
        {"t_ms": 5, "kind": "bidon", "action": "opened", "actor": "player", "certain": True},
    ]
    ev, o, d, unc = count_events(raw)
    assert (o, d, unc, len(ev)) == (1, 1, False, 4)
    assert count_events([{"t_ms": 1, "kind": "enterre", "action": "opened", "actor": "player", "certain": False}])[3]


def test_external_backend_and_db(tmp_path):
    rp = make_replay(tmp_path / "a.replay")
    fake = tmp_path / "fake.py"
    fake.write_text("import json;print(json.dumps({'mode':'Solo','events':[{'t_ms':5,'kind':'standard','action':'opened','actor':'player','certain':True}]*3}))")
    m = analyze_file(rp, f'"{sys.executable}" "{fake}"'.replace("\\", "/") if False else f'{sys.executable} {fake}')
    assert (m.opened, m.mode, m.certainty) == (3, "Solo", "certaine")
    db = Database(tmp_path / "s.db")
    db.save_match("a.replay", 1, 1.0, m)
    db.save_match("a.replay", 1, 1.0, m)   # pas de double comptage
    t = db.totals()
    assert t["matches"] == 1 and t["opened"] == 3 and t["avg"] == 3
    assert len(db.events(db.matches()[0]["id"])) == 3
    db.reset()
    assert db.totals()["matches"] == 0


def test_scanner_waits_for_stable_file(tmp_path):
    now = [0.0]
    sc = FolderScanner(tmp_path, settle=5, clock=lambda: now[0])
    f = tmp_path / "a.replay"
    f.write_bytes(b"1")
    assert sc.poll() == []
    now[0] = 3
    f.write_bytes(b"12")          # le fichier grossit : on réarme l'attente
    assert sc.poll() == []
    now[0] = 6
    assert sc.poll() == []
    now[0] = 9
    assert sc.poll() == [f]
    now[0] = 30
    assert sc.poll() == []        # jamais deux fois
