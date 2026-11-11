"""Détection de Fortnite et du dossier des rediffusions (lecture seule du système de fichiers)."""
import json
import os
from pathlib import Path


def default_replay_dir() -> Path | None:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None
    p = Path(local) / "FortniteGame" / "Saved" / "Demos"
    return p if p.is_dir() else None


def find_fortnite_install() -> Path | None:
    """Lit le manifeste du lanceur Epic (simple fichier JSON local)."""
    pd = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
    dat = Path(pd) / "Epic" / "UnrealEngineLauncher" / "LauncherInstalled.dat"
    try:
        data = json.loads(dat.read_text(encoding="utf-8"))
        for item in data.get("InstallationList", []):
            if item.get("AppName") == "Fortnite":
                return Path(item["InstallLocation"])
    except (OSError, ValueError, KeyError):
        pass
    return None
