from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QSlider, QVBoxLayout, QWidget)

from .crosshair import STYLES, CrosshairPreview


class CrosshairPage(QWidget):
    def __init__(self, ctl, xover):
        super().__init__()
        self.ctl, self.xover, s = ctl, xover, ctl.settings
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(12)
        t = QLabel("Crosshair")
        t.setObjectName("h1")
        lay.addWidget(t)
        warn = QLabel("Fonction non officielle : Epic Games n'a pas validé les viseurs affichés par une application externe. "
                      "Utilisation à vos risques ; préférez le viseur du jeu quand il existe. Visible en plein écran fenêtré uniquement.")
        warn.setWordWrap(True)
        warn.setStyleSheet("color:#f0b429;")
        lay.addWidget(warn)
        body = QHBoxLayout()
        form = QGridLayout()
        form.setVerticalSpacing(10)
        self.enable = QCheckBox("Afficher le crosshair à l'écran")
        self.enable.setChecked(bool(s.get("crosshair_enabled")))
        self.enable.toggled.connect(self.on_enable)
        form.addWidget(self.enable, 0, 0, 1, 3)
        self.style = QComboBox()
        self.style.addItems(STYLES)
        self.style.setCurrentText(s.get("crosshair_style"))
        self.style.activated.connect(lambda _: self.put("crosshair_style", self.style.currentText()))
        form.addWidget(QLabel("Forme :"), 1, 0)
        form.addWidget(self.style, 1, 1, 1, 2)
        self.sliders = {}
        rows = [("Taille (px) :", "crosshair_size", 8, 256), ("Épaisseur :", "crosshair_thickness", 1, 12),
                ("Espace central :", "crosshair_gap", 0, 40), ("Opacité (%) :", "crosshair_opacity", 10, 100),
                ("Décalage horizontal :", "crosshair_dx", -100, 100), ("Décalage vertical :", "crosshair_dy", -100, 100)]
        for i, (label, key, lo, hi) in enumerate(rows, start=2):
            sl = QSlider(Qt.Horizontal)
            sl.setRange(lo, hi)
            val = s.get(key)
            sl.setValue(int(val * 100) if key == "crosshair_opacity" else int(val))
            val_lbl = QLabel(str(sl.value()))
            sl.valueChanged.connect(lambda v, k=key, lb=val_lbl: (lb.setText(str(v)), self.put(k, v / 100 if k == "crosshair_opacity" else v)))
            form.addWidget(QLabel(label), i, 0)
            form.addWidget(sl, i, 1)
            form.addWidget(val_lbl, i, 2)
            self.sliders[key] = sl
        self.colorb = QPushButton("Couleur…")
        self.colorb.clicked.connect(self.pick_color)
        self.img = QPushButton("Choisir mon image…")
        self.img.clicked.connect(self.pick_image)
        rm = QPushButton("Retirer l'image")
        rm.clicked.connect(self.remove_image)
        self.imglbl = QLabel(s.get("crosshair_image") or "Aucune image choisie (PNG, JPG ou SVG avec fond transparent conseillé)")
        self.imglbl.setObjectName("muted")
        self.imglbl.setWordWrap(True)
        form.addWidget(self.colorb, 8, 0)
        row = QHBoxLayout()
        row.addWidget(self.img)
        row.addWidget(rm)
        form.addLayout(row, 9, 0, 1, 3)
        form.addWidget(self.imglbl, 10, 0, 1, 3)
        body.addLayout(form, 1)
        self.preview = CrosshairPreview(s)
        body.addWidget(self.preview, 0, Qt.AlignTop)
        lay.addLayout(body)
        lay.addStretch()

    def put(self, key, value):
        self.ctl.settings.set(key, value)
        self.xover.refresh()
        self.preview.update()

    def on_enable(self, v):
        self.ctl.settings.set("crosshair_enabled", v)
        self.xover.setVisible(v)
        self.xover.refresh()

    def pick_color(self):
        c = QColorDialog.getColor(QColor(self.ctl.settings.get("crosshair_color")), self, "Couleur du crosshair")
        if c.isValid():
            self.put("crosshair_color", c.name())

    def pick_image(self):
        f, _ = QFileDialog.getOpenFileName(self, "Image du crosshair", "", "Images (*.png *.jpg *.jpeg *.bmp *.svg *.webp)")
        if f:
            self.imglbl.setText(f)
            self.style.setCurrentText("Image personnalisée")
            self.ctl.settings.set("crosshair_style", "Image personnalisée")
            self.put("crosshair_image", f)

    def remove_image(self):
        self.imglbl.setText("Aucune image choisie")
        if self.ctl.settings.get("crosshair_style") == "Image personnalisée":
            self.style.setCurrentText("Croix")
            self.ctl.settings.set("crosshair_style", "Croix")
        self.put("crosshair_image", "")
