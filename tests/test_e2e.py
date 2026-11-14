import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from fct.config import Settings
from fct.controller import Controller
from fct.db import Database
from tests.test_core import make_replay

app = QApplication.instance() or QApplication([])


def wait(ctl, cond, t=5):
    end = time.time() + t
    while time.time() < end and not cond():
        app.processEvents()
        time.sleep(0.02)
    return cond()


def test_full_flow(tmp_path):
    demos = tmp_path / "Demos"
    demos.mkdir()
    fake = tmp_path / "fake.py"
    fake.write_text("import json;print(json.dumps({'mode':'Duo','events':[{'t_ms':9,'kind':'rare','action':'opened','actor':'player','certain':True}]*4}))")
    s = Settings(tmp_path / "s.json")
    s.set("replay_dir", str(demos))
    s.set("parser_cmd", f"{sys.executable} {fake}")
    ctl = Controller(s, Database(tmp_path / "db.sqlite"))
    ctl.scanner.settle = 0
    notes = []
    ctl.notify.connect(lambda t, m: notes.append(m))
    make_replay(demos / "UnsavedReplay-1.replay")
    make_replay(demos / "broken.replay", truncate=7)
    ctl._tick()          # 1er passage : fichiers observés
    ctl._tick()          # 2e : stables -> analyse
    assert wait(ctl, lambda: ctl.pending == 0 and ctl.db.totals()["matches"] == 1)
    assert ctl.db.totals()["opened"] == 4 and notes == ["4 coffre(s) détecté(s)"]
    assert ctl.db.status_of(demos / "broken.replay") == "incomplète"      # tronqué : peut-être encore en écriture
    (demos / "garbage.replay").write_bytes(b"ceci n'est pas une rediffusion Fortnite")
    ctl._tick(); ctl._tick()
    assert wait(ctl, lambda: ctl.pending == 0 and ctl.db.status_of(demos / "garbage.replay") == "erreur")
    ctl._tick(); ctl._tick()
    time.sleep(0.2); app.processEvents()
    assert ctl.db.totals()["matches"] == 1       # pas de double analyse
    ctl.analyze_manual(force=True)                # ré-analyse manuelle : remplace, ne double pas
    assert wait(ctl, lambda: ctl.pending == 0)
    assert ctl.db.totals()["opened"] == 4


def test_replay_in_progress_is_retried_when_finished(tmp_path):
    demos = tmp_path / "Demos"
    demos.mkdir()
    fake = tmp_path / "fake.py"
    fake.write_text("import json;print(json.dumps({'mode':'Solo','events':[{'t_ms':1,'kind':'standard','action':'opened','actor':'player','certain':True}]*2}))")
    s = Settings(tmp_path / "s.json")
    s.set("replay_dir", str(demos))
    s.set("parser_cmd", f"{sys.executable} {fake}")
    ctl = Controller(s, Database(tmp_path / "db.sqlite"))
    ctl.scanner.settle = 0
    notes = []
    ctl.notify.connect(lambda t, m: notes.append(m))
    rp = demos / "UnsavedReplay-live.replay"
    make_replay(rp, live=True)                    # partie en cours : l'en-tête dit « live »
    for _ in range(3):
        ctl._tick()
    assert wait(ctl, lambda: ctl.pending == 0 and ctl.db.status_of(rp) == "incomplète")
    for _ in range(4):                            # inchangé : on ne réessaie pas en boucle
        ctl._tick()
    time.sleep(0.2); app.processEvents()
    assert ctl.db.status_of(rp) == "incomplète" and notes == []
    rp.unlink()
    make_replay(rp, live=False, chunks=((0, b"h" * 10), (1, b"d" * 80)))   # fin de partie : fichier finalisé
    for _ in range(3):
        ctl._tick()
    assert wait(ctl, lambda: ctl.db.totals()["matches"] == 1 and len(notes) == 1)
    assert ctl.db.status_of(rp) == "analysée" and notes == ["2 coffre(s) détecté(s)"]
