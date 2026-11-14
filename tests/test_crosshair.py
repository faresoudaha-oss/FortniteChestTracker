import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from fct.config import Settings
from fct.ui.crosshair import STYLES, CrosshairOverlay, render_crosshair

app = QApplication.instance() or QApplication([])


def _opaque_pixels(pm):
    img = pm.toImage()
    return sum(1 for x in range(img.width()) for y in range(img.height()) if img.pixelColor(x, y).alpha() > 0)


def test_every_style_draws_something_and_size_applies(tmp_path):
    s = Settings(tmp_path / "s.json")
    for st in STYLES[:-1]:
        s.set("crosshair_style", st)
        s.set("crosshair_size", 40)
        pm = render_crosshair(s.get)
        assert pm.width() == 48 and _opaque_pixels(pm) > 10, st
    s.set("crosshair_size", 100)
    assert render_crosshair(s.get).width() == 108


def test_custom_image_and_fallback(tmp_path):
    img = QImage(20, 10, QImage.Format_ARGB32)
    img.fill(QColor("#00ff00"))
    f = tmp_path / "mon.png"
    assert img.save(str(f))
    s = Settings(tmp_path / "s.json")
    s.set("crosshair_style", "Image personnalisée")
    s.set("crosshair_size", 60)
    s.set("crosshair_image", str(f))
    pm = render_crosshair(s.get).toImage()
    assert pm.pixelColor(pm.width() // 2, pm.height() // 2).green() > 200          # l'image est bien dessinée
    s.set("crosshair_image", str(tmp_path / "absent.png"))
    assert _opaque_pixels(render_crosshair(s.get)) > 10                              # retour au viseur simple


def test_overlay_is_click_through_and_centered(tmp_path):
    s = Settings(tmp_path / "s.json")
    x = CrosshairOverlay(s)
    assert x.windowFlags() & Qt.WindowTransparentForInput and x.windowFlags() & Qt.WindowStaysOnTopHint
    s.set("crosshair_dx", 10)
    x.refresh()
    g = app.primaryScreen().geometry()
    assert abs((x.x() + x.width() // 2) - (g.center().x() + 10)) <= 1
