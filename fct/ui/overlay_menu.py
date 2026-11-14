"""Menu du clic droit sur l'overlay (réglages rapides)."""
import os

from PySide6.QtCore import QUrl
from PySide6.QtGui import QActionGroup, QDesktopServices, QFont
from PySide6.QtWidgets import QMenu

from ..autostart import set_autostart
from ..config import VERSION
from .overlay import COLORS

SIZES = [("Petit", 0.8), ("Normal", 1.0), ("Grand", 1.4), ("Très grand", 1.8)]
OPACITIES = [("100 %", 1.0), ("85 %", 0.85), ("70 %", 0.7), ("55 %", 0.55)]
CORNERS = ["haut-gauche", "haut-droite", "bas-gauche", "bas-droite"]


def _choice(menu, items, current, on_pick, tol=0.01):
    grp = QActionGroup(menu)
    for label, val in items:
        a = menu.addAction(label)
        a.setCheckable(True)
        a.setChecked(abs(val - current) < tol if isinstance(val, float) else val == current)
        grp.addAction(a)
        a.triggered.connect(lambda _=False, v=val: on_pick(v))


def build_menu(ctl, overlay, show_window, quit_app) -> QMenu:
    s, m = ctl.settings, QMenu(overlay)
    t = ctl.db.totals()
    for text in (f"Chest Tracker · v{VERSION}", f"Total : {t['opened']} coffres ({t['matches']} parties)",
                 "Analyse en cours…" if ctl.pending else "À jour"):
        m.addAction(text).setEnabled(False)
    m.addSeparator()
    a = m.addAction("Ouvrir le tableau de bord")
    f = QFont(a.font())
    f.setBold(True)
    a.setFont(f)
    a.triggered.connect(show_window)
    m.addAction("Analyser les nouvelles rediffusions").triggered.connect(lambda: ctl.analyze_manual(False))
    m.addSeparator()

    om = m.addMenu("Overlay")
    om.addAction("Masquer l'overlay").triggered.connect(lambda: (s.set("overlay_enabled", False), overlay.hide()))
    d = om.addAction("Afficher les détails")
    d.setCheckable(True)
    d.setChecked(bool(s.get("overlay_details")))
    d.toggled.connect(lambda v: (s.set("overlay_details", v), overlay.set_details_visible(v)))
    om.addSeparator()
    _choice(om.addMenu("Taille"), SIZES, s.get("overlay_scale"),
            lambda v: (s.set("overlay_scale", v), overlay.set_scale(v, fit=True)))
    _choice(om.addMenu("Transparence du fond"), OPACITIES, s.get("overlay_opacity"),
            lambda v: (s.set("overlay_opacity", v), overlay.set_opacity_level(v)))
    _choice(om.addMenu("Couleur du total"), [(n, n) for n in COLORS], s.get("overlay_color"),
            lambda v: (s.set("overlay_color", v), overlay.set_color(v)))
    _choice(om.addMenu("Position"), [(c.capitalize().replace("-", " "), c) for c in CORNERS], s.get("overlay_corner"),
            lambda v: (s.set("overlay_corner", v), overlay.move_to_corner(v)))

    st = m.addAction("Lancer au démarrage de Windows")
    st.setCheckable(True)
    st.setChecked(bool(s.get("autostart")))
    st.toggled.connect(lambda v: s.set("autostart", v) if set_autostart(v) else None)
    m.addSeparator()

    def open_folder():
        d_ = ctl.replay_dir()
        if d_ and os.path.isdir(d_):
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(d_)))

    m.addAction("Ouvrir le dossier des rediffusions").triggered.connect(open_folder)
    m.addSeparator()
    m.addAction("Quitter").triggered.connect(quit_app)
    return m
