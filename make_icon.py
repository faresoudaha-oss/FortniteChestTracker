"""Génère assets/icon.ico (multi-tailles) avec Qt, sans dépendance supplémentaire."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath

app = QGuiApplication([])
img = QImage(256, 256, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
g = QLinearGradient(0, 0, 256, 256)
g.setColorAt(0, QColor("#7c5cff"))
g.setColorAt(1, QColor("#3b2a99"))
path = QPainterPath()
path.addRoundedRect(QRectF(8, 8, 240, 240), 56, 56)
p.fillPath(path, g)
p.setPen(QColor("white"))
p.setFont(QFont("Sans", 110, QFont.Bold))
p.drawText(QRectF(0, 0, 256, 256), Qt.AlignCenter, "C")
p.end()
out = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
print("ok" if img.save(out, "ICO") else "echec", out)
