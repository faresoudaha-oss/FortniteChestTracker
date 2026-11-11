"""Paramètres persistants (JSON dans %APPDATA%\\FortniteChestTracker)."""
import json
import os
from pathlib import Path

APP_NAME = "FortniteChestTracker"
VERSION = "0.1.0"


def data_dir() -> Path:
    override = os.environ.get("FCT_DATA_DIR")
    base = Path(override) if override else Path(os.environ.get("APPDATA") or Path.home() / ".local" / "share") / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


DEFAULTS = {
    "replay_dir": "",
    "auto_analyze": True,
    "overlay_enabled": True,
    "overlay_scale": 1.0,
    "overlay_corner": "haut-gauche",   # haut-gauche, haut-droite, bas-gauche, bas-droite, personnalisée
    "overlay_pos": [40, 40],
    "overlay_size": [260, 150],
    "autostart": False,
    "parser_cmd": "",                  # exécutable externe de parsing (voir docs/PARSER.md)
    "player_name": "",
}


class Settings:
    def __init__(self, path: Path | None = None):
        self.path = path or data_dir() / "settings.json"
        self.values = dict(DEFAULTS)
        try:
            self.values.update(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass

    def get(self, key):
        return self.values.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        self.values[key] = value
        self.save()

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.values, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
