from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .theme import ACCENT, MUTED


class StatCard(QFrame):
    def __init__(self, title, value="0"):
        super().__init__()
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        self.t = QLabel(title)
        self.t.setObjectName("cardtitle")
        self.v = QLabel(value)
        self.v.setObjectName("cardvalue")
        lay.addWidget(self.t)
        lay.addWidget(self.v)

    def set_value(self, v):
        self.v.setText(str(v))


class ProgressChart(QWidget):
    """Courbe du total cumulé de coffres ouverts, partie après partie."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(190)
        self.values: list[int] = []

    def set_values(self, per_match: list[int]):
        total, acc = 0, []
        for v in per_match:
            total += v
            acc.append(total)
        self.values = acc
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(12, 12, -12, -22)
        if len(self.values) < 2:
            p.setPen(QColor(MUTED))
            p.drawText(self.rect(), Qt.AlignCenter, "Le graphique apparaîtra après quelques parties analysées")
            return
        mx = max(self.values) or 1
        pts = [QPointF(r.left() + r.width() * i / (len(self.values) - 1), r.bottom() - r.height() * v / mx)
               for i, v in enumerate(self.values)]
        line = QPainterPath(pts[0])
        for q in pts[1:]:
            line.lineTo(q)
        area = QPainterPath(line)
        area.lineTo(r.right(), r.bottom())
        area.lineTo(r.left(), r.bottom())
        g = QLinearGradient(0, r.top(), 0, r.bottom())
        g.setColorAt(0, QColor(124, 92, 255, 110))
        g.setColorAt(1, QColor(124, 92, 255, 0))
        p.fillPath(area, g)
        p.setPen(QPen(QColor(ACCENT), 2.5))
        p.drawPath(line)
        p.setPen(QColor(MUTED))
        p.drawText(QRectF(r.left(), r.bottom() + 2, r.width(), 18), Qt.AlignLeft, f"{len(self.values)} parties — total {mx}")
