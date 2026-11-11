"""Chef d'orchestre : surveillance, analyse en arrière-plan, statistiques."""
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal

from .analyzer import analyze_file
from .config import Settings
from .db import Database
from .paths import default_replay_dir
from .replay_header import ReplayError
from .scanner import FolderScanner


class _Job(QRunnable):
    def __init__(self, ctl, path):
        super().__init__()
        self.ctl, self.path = ctl, Path(path)

    def run(self):
        c = self.ctl
        try:
            st = self.path.stat()
            name, size, mtime = self.path.name, st.st_size, st.st_mtime
        except OSError as e:
            c.job_done.emit(str(self.path), False, f"Lecture impossible : {e}", 0, "")
            return
        try:
            m = analyze_file(self.path, c.settings.get("parser_cmd"))
            c.db.save_match(name, size, mtime, m)
            c.job_done.emit(str(self.path), True, m.note, m.opened, m.certainty)
        except ReplayError as e:
            c.db.mark_error(self.path, name, size, mtime, str(e))
            c.job_done.emit(str(self.path), False, str(e), 0, "")
        except Exception as e:  # ne jamais planter l'application sur un fichier
            c.db.mark_error(self.path, name, size, mtime, f"Erreur inattendue : {e}")
            c.job_done.emit(str(self.path), False, f"Erreur inattendue : {e}", 0, "")


class Controller(QObject):
    stats_changed = Signal()
    job_done = Signal(str, bool, str, int, str)     # chemin, ok, message, coffres, certitude
    notify = Signal(str, str)
    replays_changed = Signal()

    def __init__(self, settings: Settings | None = None, db: Database | None = None):
        super().__init__()
        self.settings = settings or Settings()
        self.db = db or Database()
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(1)           # analyse discrète : un fichier à la fois
        self.pending = 0
        self.scanner = FolderScanner(self.replay_dir())
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self._tick)
        self.job_done.connect(self._on_done)

    def replay_dir(self):
        d = self.settings.get("replay_dir")
        return Path(d) if d else default_replay_dir()

    def start(self):
        self.timer.start()
        self._tick()

    def set_replay_dir(self, folder):
        self.settings.set("replay_dir", str(folder))
        self.scanner = FolderScanner(folder)
        self._tick()

    def _tick(self):
        self._sync_scanner()
        self.replays_changed.emit()
        if not self.settings.get("auto_analyze"):
            return
        for p in self.scanner.poll():
            if self.db.status_of(p) is None:      # nouvelle partie (ou jamais vue au démarrage)
                self._submit(p)

    def _sync_scanner(self):
        if self.scanner.folder != self.replay_dir():
            self.scanner = FolderScanner(self.replay_dir())

    def _submit(self, path):
        self.pending += 1
        self.pool.start(_Job(self, path))

    def analyze_manual(self, force=False):
        """Analyse manuelle : toutes les rediffusions non analysées (ou toutes si force)."""
        n = 0
        for p in self.scanner.list_replays():
            if force or self.db.status_of(p) in (None, "erreur"):
                self.scanner.mark_done(p)
                self._submit(p)
                n += 1
        return n

    def _on_done(self, path, ok, msg, opened, certainty):
        self.pending = max(0, self.pending - 1)
        self.stats_changed.emit()
        self.replays_changed.emit()
        if ok:
            txt = f"{opened} coffre(s) détecté(s)" if certainty != "indisponible" else "Détection des coffres indisponible"
            if certainty == "incertaine":
                txt += " (incertain)"
            self.notify.emit("Partie analysée", txt)

    def reset(self):
        self.db.reset()
        self.scanner = FolderScanner(self.replay_dir())
        self.stats_changed.emit()
        self.replays_changed.emit()
