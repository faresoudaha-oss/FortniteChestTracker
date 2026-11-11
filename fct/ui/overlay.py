"""Overlay : fenêtre sans bordure, translucide, toujours au premier plan, déplaçable et redimensionnable.

Fonctionne au-dessus de Fortnite en mode « plein écran fenêtré ». Le plein écran exclusif n'est pas supporté
(Windows ne permet pas d'afficher une fenêtre ordinaire par-dessus sans injection, ce que ce projet s'interdit).
"""
from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication, QLabel, QSizeGrip, QVBoxLayout, QWidget

from .theme import ACCENT


class Overlay(QWidget):
    moved = Signal(int, int)
    resized = Signal(int, int)

    def __init__(self):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._drag = None
        self._scale = 1.0
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 12, 8)
        self.title = QLabel("🏆 FORTNITE TRACKER")
        self.opened = QLabel("Coffres ouverts : 0")
        self.destroyed = QLabel("Coffres détruits : 0")
        self.last = QLabel("Dernière partie : —")
        self.status = QLabel("Statut : en attente")
        for w in (self.title, self.opened, self.destroyed, self.last, self.status):
            lay.addWidget(w)
        lay.addStretch()
        grip = QSizeGrip(self)
        lay.addWidget(grip, 0, Qt.AlignRight | Qt.AlignBottom)
        self.set_scale(1.0)
        self.setMinimumSize(180, 110)

    def set_scale(self, s: float):
        self._scale = s
        pt = max(7, round(10 * s))
        css = "color:#e8e8f0; background:transparent; font-size:%dpt;"
        for w in (self.opened, self.destroyed, self.last, self.status):
            w.setStyleSheet(css % pt)
        self.title.setStyleSheet(f"color:{ACCENT}; background:transparent; font-weight:700; font-size:{pt}pt;")
        self.last.setStyleSheet(css % pt + "color:#8b8ba0;")

    def update_stats(self, totals: dict, status: str):
        self.opened.setText(f"Coffres ouverts : {totals['opened']}")
        self.destroyed.setText(f"Coffres détruits : {totals['destroyed']}")
        last = totals.get("last")
        if last:
            txt = "indisponible" if last["certainty"] == "indisponible" else f"{last['opened']} coffre(s)"
            self.last.setText(f"Dernière partie : {txt}")
        else:
            self.last.setText("Dernière partie : —")
        self.status.setText(f"Statut : {status}")

    def move_to_corner(self, corner: str, margin=24):
        g = QApplication.primaryScreen().availableGeometry()
        x = g.left() + margin if "gauche" in corner else g.right() - self.width() - margin
        y = g.top() + margin if "haut" in corner else g.bottom() - self.height() - margin
        self.move(x, y)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 14, 14)
        p.fillPath(path, QColor(14, 14, 20, 205))
        p.setPen(QColor(124, 92, 255, 120))
        p.drawPath(path)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, _):
        if self._drag is not None:
            self._drag = None
            self.moved.emit(self.x(), self.y())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.resized.emit(self.width(), self.height())
