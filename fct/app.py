import os
import sys
import tempfile

from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .config import APP_NAME, Settings
from .controller import Controller
from .db import Database
from .ui.main_window import MainWindow
from .ui.overlay import Overlay
from .ui.theme import QSS


def resource(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, rel)


def _icon():
    p = resource("assets/icon.ico")
    if os.path.exists(p):
        return QIcon(p)
    pm = QPixmap(64, 64)
    pm.fill(QColor("#7c5cff"))
    return QIcon(pm)


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    selftest = "--selftest" in argv
    if selftest:
        os.environ["FCT_DATA_DIR"] = tempfile.mkdtemp()
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(QSS)
    icon = _icon()
    app.setWindowIcon(icon)

    settings = Settings()
    ctl = Controller(settings, Database())
    overlay = Overlay()
    win = MainWindow(ctl, overlay)

    def refresh_overlay():
        busy = ctl.pending > 0
        overlay.update_stats(ctl.db.totals(), "analyse en cours…" if busy else "à jour")

    ctl.stats_changed.connect(refresh_overlay)
    ctl.replays_changed.connect(refresh_overlay)
    overlay.resize(*settings.get("overlay_size"))
    overlay.set_scale(settings.get("overlay_scale"))
    if settings.get("overlay_corner") == "personnalisée":
        overlay.move(*settings.get("overlay_pos"))
    else:
        overlay.move_to_corner(settings.get("overlay_corner"))
    overlay.moved.connect(lambda x, y: (settings.set("overlay_pos", [x, y]), settings.set("overlay_corner", "personnalisée")))
    overlay.resized.connect(lambda w, h: settings.set("overlay_size", [w, h]))
    refresh_overlay()

    tray = QSystemTrayIcon(icon, app)
    menu = QMenu()
    for label, fn in (("Ouvrir", lambda: (win.show(), win.raise_(), win.activateWindow())),
                      ("Afficher / masquer l'overlay", lambda: overlay.setVisible(not overlay.isVisible())),
                      ("Quitter", lambda: (overlay.hide(), tray.hide(), win.real_quit(), app.quit()))):
        a = QAction(label, menu)
        a.triggered.connect(fn)
        menu.addAction(a)
    tray.setContextMenu(menu)
    tray.setToolTip("Fortnite Chest Tracker")
    tray.activated.connect(lambda r: win.show() if r == QSystemTrayIcon.Trigger else None)
    tray.show()
    ctl.notify.connect(lambda t, m: tray.showMessage(t, m, QSystemTrayIcon.Information, 5000))

    if "--minimized" not in argv and not selftest:
        win.show()
    if settings.get("overlay_enabled"):
        overlay.show()
    ctl.start()

    if selftest:
        win.show()
        app.processEvents()
        assert ctl.db.totals()["matches"] == 0 and overlay.isVisible()
        from .analyzer import bundled_exporter
        if os.environ.get("FCT_REQUIRE_EXPORTER") == "1":
            assert bundled_exporter(), "ReplayExporter.exe absent de l'application"
        print("Module de détection :", bundled_exporter() or "absent")
        print("SELFTEST OK")
        return 0
    return app.exec()
