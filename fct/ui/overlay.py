"""Overlay : fenêtre sans bordure, translucide, toujours au premier plan, déplaçable et redimensionnable.

Gros total de coffres ouverts, petits détails dessous, clic droit pour le menu des réglages.
Fonctionne au-dessus de Fortnite en mode « plein écran fenêtré ». Le plein écran exclusif n'est pas supporté
(Windows ne permet pas d'afficher une fenêtre ordinaire par-dessus sans injection, ce que ce projet s'interdit).
"""
from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QSizeGrip, QVBoxLayout, QWidget

COLORS = {"Vert": "#3ddc84", "Bleu": "#4da3ff", "Jaune": "#ffd23f", "Blanc": "#ffffff"}
MUTED = "#a3a3b8"
STATUS_COLORS = {"ok": "#3ddc84", "busy": "#ffb020", "idle": "#8b8ba0"}


class Overlay(QWidget):
    moved = Signal(int, int)
    resized = Signal(int, int)
    menu_requested = Signal(QPoint)

    def __init__(self):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._drag = None
        self._scale, self._opacity, self._color = 1.0, 0.9, COLORS["Vert"]
        self._status_kind = "idle"

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 10, 8)
        lay.setSpacing(2)
        top = QHBoxLayout()
        top.setSpacing(10)
        self.total = QLabel("0")                      # le gros chiffre
        side = QVBoxLayout()
        side.setSpacing(1)
        self.caption = QLabel("coffres ouverts")
        self.last = QLabel("—")                      # « +7 dernière partie »
        side.addStretch()
        side.addWidget(self.caption)
        side.addWidget(self.last)
        top.addWidget(self.total)
        top.addLayout(side)
        top.addStretch()
        lay.addLayout(top)
        self.details = QLabel("")
        self.status = QLabel("")
        lay.addWidget(self.details)
        lay.addWidget(self.status)
        lay.addStretch()
        lay.addWidget(QSizeGrip(self), 0, Qt.AlignRight | Qt.AlignBottom)
        self._style()
        self._fit(reset=True)

    # ---- apparence -------------------------------------------------------
    def _style(self):
        s = self._scale
        big, small = max(16, round(30 * s)), max(7, round(8.5 * s))
        self.total.setStyleSheet(f"color:{self._color}; background:transparent; font-size:{big}pt; font-weight:800;")
        for w in (self.caption, self.details):
            w.setStyleSheet(f"color:{MUTED}; background:transparent; font-size:{small}pt;")
        self.last.setStyleSheet(f"color:#e8e8f0; background:transparent; font-size:{small}pt; font-weight:600;")
        dot = STATUS_COLORS[self._status_kind]
        self.status.setStyleSheet(f"color:{dot}; background:transparent; font-size:{small}pt;")
        self.update()

    def _fit(self, reset=False):
        """La fenêtre ne devient jamais trop petite pour son contenu."""
        hint = self.sizeHint()
        self.resize(hint if reset else self.size().expandedTo(hint))

    def set_scale(self, s: float, fit=False):
        self._scale = s
        self._style()
        self._fit(reset=fit)

    def set_opacity_level(self, v: float):
        self._opacity = max(0.3, min(1.0, v))
        self.update()

    def set_color(self, name: str):
        self._color = COLORS.get(name, COLORS["Vert"])
        self._style()

    def set_details_visible(self, v: bool):
        self.details.setVisible(v)
        self._fit(reset=True)

    # ---- données ---------------------------------------------------------
    def update_stats(self, totals: dict, status: str):
        self.total.setText(str(totals["opened"]))
        last = totals.get("last")
        if last and last["certainty"] != "indisponible":
            self.last.setText(f"+{last['opened']} dernière partie")
        else:
            self.last.setText("—")
        self.details.setText(f"{totals['destroyed']} détruits  ·  {totals['matches']} parties  ·  moy. {totals['avg']:.1f}".replace(".", ","))
        self._status_kind = "busy" if "cours" in status else ("ok" if "jour" in status else "idle")
        self.status.setText(f"● {status}")
        self._style()
        self._fit()

    def move_to_corner(self, corner: str, margin=24):
        g = QApplication.primaryScreen().availableGeometry()
        x = g.left() + margin if "gauche" in corner else g.right() - self.width() - margin
        y = g.top() + margin if "haut" in corner else g.bottom() - self.height() - margin
        self.move(x, y)

    # ---- dessin et souris ------------------------------------------------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 14, 14)
        p.fillPath(path, QColor(14, 14, 20, int(255 * self._opacity)))
        c = QColor(self._color)
        c.setAlpha(110)
        p.setPen(c)
        p.drawPath(path)

    def contextMenuEvent(self, e):
        self.menu_requested.emit(e.globalPos())

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
