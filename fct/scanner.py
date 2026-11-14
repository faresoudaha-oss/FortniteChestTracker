"""Surveillance du dossier des rediffusions par sondage léger (aucune dépendance, très peu de CPU).

Un fichier est « prêt » quand sa taille/date n'ont pas changé pendant `settle` secondes,
c.-à-d. que Fortnite a fini de l'écrire.
"""
import time
from pathlib import Path


class FolderScanner:
    def __init__(self, folder, settle: float = 8.0, clock=time.time):
        self.folder = Path(folder) if folder else None
        self.settle = settle
        self.clock = clock
        self._seen: dict[str, tuple] = {}     # path -> (size, mtime, since)
        self._done: set[str] = set()
        self._blocked: dict[str, tuple] = {}   # replays incomplets : on n'y revient que s'ils changent

    def list_replays(self) -> list[Path]:
        if not self.folder or not self.folder.is_dir():
            return []
        try:
            return sorted(self.folder.glob("*.replay"), key=lambda p: p.stat().st_mtime, reverse=True)
        except OSError:
            return []

    def mark_done(self, path):
        self._done.add(str(path))

    def forget(self, path):
        """Replay pas encore terminé : le surveiller à nouveau, mais seulement s'il change."""
        key = str(path)
        self._done.discard(key)
        self._seen.pop(key, None)
        try:
            st = Path(path).stat()
            self._blocked[key] = (st.st_size, st.st_mtime)
        except OSError:
            pass

    def poll(self) -> list[Path]:
        """Retourne les fichiers stables jamais retournés auparavant."""
        now, ready = self.clock(), []
        for p in self.list_replays():
            key = str(p)
            if key in self._done:
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            sig = (st.st_size, st.st_mtime)
            if self._blocked.get(key) == sig:
                continue
            self._blocked.pop(key, None)
            prev = self._seen.get(key)
            if prev is None or prev[:2] != sig:
                self._seen[key] = (*sig, now)
            elif now - prev[2] >= self.settle and st.st_size > 0:
                self._done.add(key)
                ready.append(p)
        return ready
