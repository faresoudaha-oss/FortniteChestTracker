"""Viseur personnalisable affiché au centre de l'écran.

Simple image dessinée dans une fenêtre transparente qui laisse passer les clics (aucune interaction avec le jeu :
pas de lecture de la mémoire, pas d'injection). Fonctionne en plein écran fenêtré uniquement.
"""
import os

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

STYLES = ["Croix", "Croix avec point", "Point", "Cercle", "Cercle et point", "Image personnalisée"]
MARGIN = 4


def render_crosshair(get) -> QPixmap:
    """`get(clé)` renvoie un réglage (Settings.get). Retourne un pixmap transparent carré."""
    size = int(get("crosshair_size"))
    t = max(1, int(get("crosshair_thickness")))
    gap = max(0, int(get("crosshair_gap")))
    style = get("crosshair_style")
    color = QColor(get("crosshair_color"))
    if not color.isValid():
        color = QColor("#ff3b3b")
    pm = QPixmap(size + 2 * MARGIN, size + 2 * MARGIN)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setOpacity(float(get("crosshair_opacity")))
    if style == "Image personnalisée":
        img = QPixmap(get("crosshair_image") or "")
        if not img.isNull():
            img = img.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.drawPixmap((pm.width() - img.width()) // 2, (pm.height() - img.height()) // 2, img)
            p.end()
            return pm
        style = "Croix"                      # image absente ou illisible : retour au viseur simple
    c, half = pm.width() / 2, size / 2
    pen = QPen(color, t, Qt.SolidLine, Qt.FlatCap)
    p.setPen(pen)
    if style in ("Croix", "Croix avec point"):
        g = min(gap, half - 1)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p.drawLine(QPointF(c + dx * g, c + dy * g), QPointF(c + dx * half, c + dy * half))
    if style in ("Cercle", "Cercle et point"):
        p.setBrush(Qt.NoBrush)
        r = half - t / 2
        p.drawEllipse(QPointF(c, c), r, r)
    if style in ("Croix avec point", "Point", "Cercle et point"):
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        r = max(t, size / 10) if style == "Point" else max(t * 0.75, 1.5)
        p.drawEllipse(QPointF(c, c), r, r)
    p.end()
    return pm


class CrosshairOverlay(QWidget):
    def __init__(self, settings):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                         | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus)
        self.settings = settings
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.pm = QPixmap()
        self.refresh()

    def refresh(self):
        self.pm = render_crosshair(self.settings.get)
        self.setFixedSize(self.pm.size())
        g = QApplication.primaryScreen().geometry()
        self.move(g.center().x() - self.width() // 2 + int(self.settings.get("crosshair_dx")),
                  g.center().y() - self.height() // 2 + int(self.settings.get("crosshair_dy")))
        self.update()

    def paintEvent(self, _):
        QPainter(self).drawPixmap(0, 0, self.pm)


class CrosshairPreview(QWidget):
    """Aperçu sur fond sombre dans la page de réglages."""

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setFixedSize(230, 230)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#20202b"))
        pm = render_crosshair(self.settings.get)
        p.drawPixmap((self.width() - pm.width()) // 2, (self.height() - pm.height()) // 2, pm)
