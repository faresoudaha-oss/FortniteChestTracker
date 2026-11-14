ACCENT = "#7c5cff"
BG = "#0f0f14"
CARD = "#1a1a23"
TEXT = "#e8e8f0"
MUTED = "#8b8ba0"

QSS = f"""
QMenu {{ background: #1a1a23; border: 1px solid #2f2f3f; border-radius: 8px; padding: 6px; }}
QMenu::item {{ padding: 7px 26px 7px 14px; border-radius: 6px; }}
QMenu::item:selected {{ background: {ACCENT}; }}
QMenu::item:disabled {{ color: {MUTED}; }}
QMenu::separator {{ height: 1px; background: #2f2f3f; margin: 5px 8px; }}
* {{ font-family: 'Segoe UI', 'Inter', sans-serif; color: {TEXT}; font-size: 13px; }}
QMainWindow, QWidget#root {{ background: {BG}; }}
QFrame#sidebar {{ background: #14141b; border-right: 1px solid #23232e; }}
QPushButton#nav {{ background: transparent; text-align: left; padding: 11px 16px; border: none; border-radius: 10px; color: {MUTED}; font-size: 14px; }}
QPushButton#nav:hover {{ background: #1f1f2b; color: {TEXT}; }}
QPushButton#nav:checked {{ background: {ACCENT}; color: white; font-weight: 600; }}
QFrame#card {{ background: {CARD}; border-radius: 14px; border: 1px solid #262633; }}
QLabel#cardvalue {{ font-size: 28px; font-weight: 700; }}
QLabel#cardtitle, QLabel#muted {{ color: {MUTED}; }}
QLabel#h1 {{ font-size: 22px; font-weight: 700; }}
QPushButton {{ background: {ACCENT}; color: white; border: none; border-radius: 9px; padding: 9px 16px; font-weight: 600; }}
QPushButton:hover {{ background: #9079ff; }}
QPushButton:disabled {{ background: #2a2a38; color: {MUTED}; }}
QPushButton#danger {{ background: #c0392b; }}
QPushButton#danger:hover {{ background: #e04a3a; }}
QTableWidget {{ background: {CARD}; border: 1px solid #262633; border-radius: 12px; gridline-color: #262633; selection-background-color: #2d2650; }}
QHeaderView::section {{ background: #20202b; border: none; padding: 8px; color: {MUTED}; font-weight: 600; }}
QLineEdit, QComboBox, QSpinBox {{ background: #20202b; border: 1px solid #2f2f3f; border-radius: 8px; padding: 7px; }}
QCheckBox {{ spacing: 10px; }}
QProgressBar {{ background: #20202b; border-radius: 6px; height: 12px; text-align: center; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 6px; }}
QSlider::groove:horizontal {{ background: #2a2a38; height: 6px; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {ACCENT}; width: 16px; margin: -5px 0; border-radius: 8px; }}
"""
