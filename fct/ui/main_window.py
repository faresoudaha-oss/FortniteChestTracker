from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from .pages import AnalysisPage, DashboardPage, HistoryPage, SettingsPage


class MainWindow(QMainWindow):
    def __init__(self, ctl, overlay):
        super().__init__()
        self.setWindowTitle("Fortnite Chest Tracker")
        self.resize(1040, 680)
        self.setMinimumSize(820, 560)
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(210)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(14, 20, 14, 14)
        logo = QLabel("🏆  Chest Tracker")
        logo.setStyleSheet("font-size:17px; font-weight:700;")
        sl.addWidget(logo)
        sl.addSpacing(18)
        self.stack = QStackedWidget()
        group = QButtonGroup(self)
        pages = [("📊  Tableau de bord", DashboardPage(ctl)), ("🕘  Historique", HistoryPage(ctl)),
                 ("🔍  Analyse", AnalysisPage(ctl)), ("⚙  Paramètres", SettingsPage(ctl, overlay))]
        for i, (name, page) in enumerate(pages):
            b = QPushButton(name)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, i=i: self.stack.setCurrentIndex(i))
            group.addButton(b)
            sl.addWidget(b)
            self.stack.addWidget(page)
            if i == 0:
                b.setChecked(True)
        sl.addStretch()
        note = QLabel("Analyse locale uniquement.\nAucun accès au jeu.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        sl.addWidget(note)
        h.addWidget(side)
        h.addWidget(self.stack, 1)
        self._quit = False

    def closeEvent(self, e):
        if self._quit:
            e.accept()
        else:      # reste actif dans la zone de notification pour surveiller les parties
            e.ignore()
            self.hide()

    def real_quit(self):
        self._quit = True
        self.close()
