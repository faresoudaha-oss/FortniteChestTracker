import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from fct.config import Settings
from fct.controller import Controller
from fct.db import Database, MatchRecord
from fct.ui.overlay import Overlay
from fct.ui.overlay_menu import build_menu

app = QApplication.instance() or QApplication([])


def _texts(menu):
    return [a.text() for a in menu.actions() if a.text()]


def test_overlay_texts_and_menu(tmp_path):
    db = Database(tmp_path / "d.db")
    db.save_match("a", 1, 1.0, MatchRecord("/a", "2026-01-01 10:00:00", 600, "Solo", 7, 2, "certaine"))
    db.save_match("b", 1, 1.0, MatchRecord("/b", "2026-01-02 10:00:00", 600, "Duo", 5, 1, "certaine"))
    ctl = Controller(Settings(tmp_path / "s.json"), db)
    ov = Overlay()
    ov.update_stats(db.totals(), "à jour")
    assert ov.total.text() == "12" and "+5 dernière partie" in ov.last.text() and "3 détruits" in ov.details.text()
    called = []
    m = build_menu(ctl, ov, lambda: called.append("win"), lambda: called.append("quit"))
    t = _texts(m)
    assert "Total : 12 coffres (2 parties)" in t and "Ouvrir le tableau de bord" in t and "Quitter" in t
    sub = {a.text(): a.menu() for a in m.actions() if a.menu()}
    assert "Overlay" in sub
    om = {a.text(): a.menu() for a in sub["Overlay"].actions() if a.menu()}
    grand = [a for a in om["Taille"].actions() if a.text() == "Grand"][0]
    grand.trigger()
    assert ctl.settings.get("overlay_scale") == 1.4
    bleu = [a for a in om["Couleur du total"].actions() if a.text() == "Bleu"][0]
    bleu.trigger()
    assert ctl.settings.get("overlay_color") == "Bleu"
    [a for a in m.actions() if a.text() == "Quitter"][0].trigger()
    assert called == ["quit"]
    ov.update_stats({"opened": 0, "destroyed": 0, "matches": 1, "avg": 0, "last": {"certainty": "indisponible", "opened": 0}}, "à jour")
    assert ov.last.text() == "—"
