from datetime import timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFileDialog, QGridLayout, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton, QSlider, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from ..autostart import set_autostart
from ..paths import find_fortnite_install
from .widgets import ProgressChart, StatCard

CERT = {"certaine": "✔ Certaine", "incertaine": "⚠ Incertaine", "indisponible": "— Indisponible"}
ACTIONS = {"opened": "Ouvert", "destroyed": "Détruit"}
ACTORS = {"player": "Vous", "teammate": "Coéquipier", "enemy": "Adversaire", "unknown": "Inconnu"}
KINDS = {"standard": "Classique", "rare": "Rare", "enterre": "Enterré", "special": "Spécial", "sprite": "Sprite"}


def fmt_dur(s):
    return str(timedelta(seconds=int(s or 0)))


def _item(text, right=False):
    it = QTableWidgetItem(str(text))
    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
    if right:
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return it


def _table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setShowGrid(False)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    return t


def _title(text):
    l = QLabel(text)
    l.setObjectName("h1")
    return l


class DashboardPage(QWidget):
    def __init__(self, ctl):
        super().__init__()
        self.ctl = ctl
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.addWidget(_title("Tableau de bord"))
        grid = QGridLayout()
        self.c_open, self.c_dest = StatCard("Coffres ouverts"), StatCard("Coffres détruits")
        self.c_n, self.c_avg = StatCard("Parties analysées"), StatCard("Moyenne par partie")
        for i, c in enumerate((self.c_open, self.c_dest, self.c_n, self.c_avg)):
            grid.addWidget(c, 0, i)
        lay.addLayout(grid)
        self.last = QLabel()
        self.last.setObjectName("muted")
        self.warn = QLabel()
        self.warn.setWordWrap(True)
        self.warn.setStyleSheet("color:#f0b429;")
        self.chart = ProgressChart()
        lay.addWidget(self.last)
        lay.addWidget(self.warn)
        lay.addWidget(self.chart, 1)
        ctl.stats_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        t = self.ctl.db.totals()
        self.c_open.set_value(t["opened"])
        self.c_dest.set_value(t["destroyed"])
        self.c_n.set_value(t["matches"])
        self.c_avg.set_value(f"{t['avg']:.1f}")
        l = t["last"]
        self.last.setText(f"Dernière partie analysée : {l['played_at'] or 'date inconnue'} — {l['opened']} coffre(s) ouvert(s)" if l
                          else "Aucune partie analysée pour le moment.")
        ms = self.ctl.db.matches()
        self.warn.setText("La détection des coffres n'est pas disponible pour au moins une partie : aucun chiffre n'a été inventé."
                          if any(m["certainty"] == "indisponible" for m in ms) else "")
        self.chart.set_values([m["opened"] for m in reversed(ms)])


class DetailDialog(QDialog):
    def __init__(self, ctl, m, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détails de la partie")
        self.resize(640, 420)
        lay = QVBoxLayout(self)
        lay.addWidget(_title(m["played_at"] or "Partie"))
        lay.addWidget(QLabel(f"Mode : {m['mode']} — Durée : {fmt_dur(m['duration_s'])} — Fiabilité : {CERT.get(m['certainty'], m['certainty'])}"))
        if m.get("note"):
            n = QLabel(m["note"])
            n.setWordWrap(True)
            n.setObjectName("muted")
            lay.addWidget(n)
        t = _table(["Temps", "Type", "Action", "Auteur", "Fiable"])
        for e in ctl.db.events(m["id"]):
            r = t.rowCount()
            t.insertRow(r)
            for c, v in enumerate((fmt_dur(e["t_ms"] // 1000), KINDS.get(e["kind"], e["kind"]), ACTIONS.get(e["action"], e["action"]),
                                   ACTORS.get(e["actor"], e["actor"]), "Oui" if e["certain"] else "Non")):
                t.setItem(r, c, _item(v))
        lay.addWidget(t)


class HistoryPage(QWidget):
    def __init__(self, ctl):
        super().__init__()
        self.ctl, self.rows = ctl, []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.addWidget(_title("Historique"))
        self.t = _table(["Date et heure", "Ouverts", "Détruits", "Durée", "Mode", "Fiabilité"])
        self.t.cellDoubleClicked.connect(self.open_detail)
        lay.addWidget(self.t, 1)
        lay.addWidget(QLabel("Double-clic sur une partie pour voir le détail."))
        ctl.stats_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.rows = self.ctl.db.matches()
        self.t.setRowCount(0)
        for m in self.rows:
            r = self.t.rowCount()
            self.t.insertRow(r)
            vals = (m["played_at"] or "?", m["opened"] if m["certainty"] != "indisponible" else "—",
                    m["destroyed"] if m["certainty"] != "indisponible" else "—", fmt_dur(m["duration_s"]), m["mode"],
                    CERT.get(m["certainty"], m["certainty"]))
            for c, v in enumerate(vals):
                self.t.setItem(r, c, _item(v))

    def open_detail(self, row, _):
        if 0 <= row < len(self.rows):
            DetailDialog(self.ctl, self.rows[row], self).exec()


class AnalysisPage(QWidget):
    def __init__(self, ctl):
        super().__init__()
        self.ctl = ctl
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.addWidget(_title("Analyse"))
        top = QHBoxLayout()
        self.info = QLabel()
        self.info.setObjectName("muted")
        b1, b2 = QPushButton("Analyser les nouvelles rediffusions"), QPushButton("Tout réanalyser")
        b1.clicked.connect(lambda: self.run(False))
        b2.clicked.connect(lambda: self.run(True))
        top.addWidget(self.info, 1)
        top.addWidget(b1)
        top.addWidget(b2)
        lay.addLayout(top)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        lay.addWidget(self.bar)
        self.t = _table(["Fichier", "Statut", "Détail"])
        lay.addWidget(self.t, 1)
        self.total = 0
        ctl.replays_changed.connect(self.refresh)
        self.refresh()

    def run(self, force):
        self.total = self.ctl.analyze_manual(force)
        self.refresh()

    def refresh(self):
        d = self.ctl.replay_dir()
        self.info.setText(f"Dossier : {d}" if d and d.is_dir() else "Dossier des rediffusions introuvable : choisissez-le dans les paramètres.")
        db = {r["name"]: r for r in self.ctl.db.replays()}
        files = self.ctl.scanner.list_replays()
        self.t.setRowCount(0)
        for p in files:
            r = db.get(p.name)
            status = r["status"] if r else "en attente"
            if r is None and self.ctl.pending:
                status = "en file d'analyse"
            r_i = self.t.rowCount()
            self.t.insertRow(r_i)
            for c, v in enumerate((p.name, status, (r or {}).get("error") or "")):
                self.t.setItem(r_i, c, _item(v))
        pend = self.ctl.pending
        self.bar.setMaximum(max(self.total, 1))
        self.bar.setValue(self.total - pend if self.total and pend <= self.total else (self.total or 0))
        if pend == 0:
            self.total = 0
            self.bar.setValue(0)


class SettingsPage(QWidget):
    def __init__(self, ctl, overlay):
        super().__init__()
        self.ctl, self.overlay, s = ctl, overlay, ctl.settings
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(12)
        lay.addWidget(_title("Paramètres"))
        row = QHBoxLayout()
        self.dir = QLineEdit(str(ctl.replay_dir() or ""))
        self.dir.setReadOnly(True)
        b = QPushButton("Parcourir…")
        b.clicked.connect(self.pick_dir)
        row.addWidget(QLabel("Rediffusions :"))
        row.addWidget(self.dir, 1)
        row.addWidget(b)
        lay.addLayout(row)
        inst = find_fortnite_install()
        lay.addWidget(QLabel(f"Fortnite détecté : {inst}" if inst else "Installation de Fortnite non détectée automatiquement (sans importance si le dossier des rediffusions est correct)."))
        self.auto = self._check("Analyse automatique après chaque partie", s.get("auto_analyze"), lambda v: s.set("auto_analyze", v))
        self.ov = self._check("Afficher l'overlay", s.get("overlay_enabled"), self.toggle_overlay)
        self.start = self._check("Lancer avec Windows", s.get("autostart"), self.toggle_autostart)
        for c in (self.auto, self.ov, self.start):
            lay.addWidget(c)
        r2 = QHBoxLayout()
        self.size = QSlider(Qt.Horizontal)
        self.size.setRange(70, 200)
        self.size.setValue(int(s.get("overlay_scale") * 100))
        self.size.valueChanged.connect(self.on_size)
        self.corner = QComboBox()
        self.corner.addItems(["haut-gauche", "haut-droite", "bas-gauche", "bas-droite", "personnalisée"])
        self.corner.setCurrentText(s.get("overlay_corner"))
        self.corner.activated.connect(self.on_corner)
        r2.addWidget(QLabel("Taille de l'overlay :"))
        r2.addWidget(self.size, 1)
        r2.addWidget(QLabel("Position :"))
        r2.addWidget(self.corner)
        lay.addLayout(r2)
        tip = QLabel("Astuce : glissez l'overlay avec la souris, redimensionnez-le par le coin inférieur droit. "
                             "Il s'affiche en plein écran fenêtré (pas en plein écran exclusif).")
        tip.setWordWrap(True)
        tip.setObjectName("muted")
        lay.addWidget(tip)
        self.parser = QLineEdit(s.get("parser_cmd"))
        self.parser.setPlaceholderText("Commande du module de détection des coffres (optionnel, voir docs/PARSER.md)")
        self.parser.editingFinished.connect(lambda: s.set("parser_cmd", self.parser.text().strip()))
        lay.addWidget(QLabel("Module de détection des coffres :"))
        lay.addWidget(self.parser)
        reset = QPushButton("Réinitialiser les statistiques")
        reset.setObjectName("danger")
        reset.clicked.connect(self.reset)
        lay.addWidget(reset, 0, Qt.AlignLeft)
        lay.addStretch()

    def _check(self, text, val, cb):
        c = QCheckBox(text)
        c.setChecked(bool(val))
        c.toggled.connect(cb)
        return c

    def pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Dossier des rediffusions Fortnite", self.dir.text())
        if d:
            self.dir.setText(d)
            self.ctl.set_replay_dir(d)

    def toggle_overlay(self, v):
        self.ctl.settings.set("overlay_enabled", v)
        self.overlay.setVisible(v)

    def toggle_autostart(self, v):
        if set_autostart(v):
            self.ctl.settings.set("autostart", v)
        else:
            self.start.blockSignals(True)
            self.start.setChecked(False)
            self.start.blockSignals(False)
            QMessageBox.information(self, "Lancement avec Windows", "Impossible de modifier le démarrage automatique sur ce système.")

    def on_size(self, v):
        self.ctl.settings.set("overlay_scale", v / 100)
        self.overlay.set_scale(v / 100)

    def on_corner(self, _):
        c = self.corner.currentText()
        self.ctl.settings.set("overlay_corner", c)
        if c != "personnalisée":
            self.overlay.move_to_corner(c)

    def reset(self):
        if QMessageBox.question(self, "Réinitialiser", "Effacer toutes les statistiques et l'historique ? Les rediffusions seront à nouveau analysables.") == QMessageBox.Yes:
            self.ctl.reset()
