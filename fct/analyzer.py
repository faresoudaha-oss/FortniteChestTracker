"""Moteur d'analyse : en-tête du replay + backend de détection de coffres interchangeable.

Backend par défaut : `ReplayExporter.exe` (dossier bin/ de l'application), petit programme .NET construit à partir du
décodeur open source de LED-N/Fortnite-ChestCounter (MIT, voir third_party/). Il ne lit que le fichier .replay.

Contrat du backend externe (docs/PARSER.md) : `<parser_cmd> <fichier.replay>` écrit sur stdout un JSON
{"mode": str, "player": str, "events": [{"t_ms": int, "kind": "standard|rare|enterre|special|sprite",
"action": "opened|destroyed", "actor": "player|teammate|enemy|unknown", "certain": bool}]}
Sans backend, aucun coffre n'est compté et le statut est « indisponible » : rien n'est inventé.
"""
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .db import MatchRecord
from .replay_header import ReplayError, ReplayIncomplete, parse_header

KINDS = ("standard", "rare", "enterre", "special", "sprite")


@dataclass
class ChestEvent:
    t_ms: int
    kind: str
    action: str   # opened | destroyed
    actor: str    # player | teammate | enemy | unknown
    certain: bool


MODES = {"solo": "Solo", "duo": "Duo", "trios": "Trios", "squad": "Escouade", "ranked": "Classé",
         "reload": "Reload", "blitz": "Blitz", "vamp": "Vampires"}


def friendly_mode(playlist: str) -> str:
    """Playlist_DefaultSolo -> Solo ; les noms inconnus sont affichés tels quels."""
    if not playlist or playlist == "Inconnu":
        return "Inconnu"
    low = playlist.lower()
    zero = "Zéro construction " if ("nobuild" in low or "zerobuild" in low) else ""
    for key, name in MODES.items():
        if key in low:
            return zero + name
    return playlist.replace("Playlist_", "")


def bundled_exporter() -> str | None:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base, "bin", "ReplayExporter.exe")
    return p if os.path.isfile(p) else None


def resolve_parser(cmd: str = "") -> list | None:
    """Commande personnalisée des paramètres, sinon l'exporteur fourni avec l'application."""
    if cmd and cmd.strip():
        return shlex.split(cmd, posix=False)
    exe = bundled_exporter()
    return [exe] if exe else None


def run_external(args: list, path: Path, timeout=300) -> dict:
    args = list(args) + [str(path)]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        out = subprocess.run(args, capture_output=True, timeout=timeout, creationflags=flags)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ReplayError(f"Module de détection indisponible : {e}") from e
    if out.returncode != 0:
        raise ReplayError("Lecture impossible : " + out.stderr.decode("utf-8", "replace").strip()[:200])
    try:
        return json.loads(out.stdout.decode("utf-8"))
    except ValueError as e:
        raise ReplayError("Sortie du module de détection illisible") from e


def count_events(raw_events) -> tuple[list, int, int, bool]:
    """Ne compte que les actions attribuées au joueur ; signale l'incertitude."""
    events, opened, destroyed, uncertain = [], 0, 0, False
    for e in raw_events:
        if e.get("kind") not in KINDS or e.get("action") not in ("opened", "destroyed"):
            continue
        ev = ChestEvent(int(e.get("t_ms", 0)), e["kind"], e["action"], e.get("actor", "unknown"), bool(e.get("certain", False)))
        events.append(ev)
        if ev.actor == "player":
            if not ev.certain:
                uncertain = True
            if ev.action == "opened":
                opened += 1
            else:
                destroyed += 1
        elif ev.actor == "unknown":
            uncertain = True
    return events, opened, destroyed, uncertain


def analyze_file(path, parser_cmd: str = "") -> MatchRecord:
    path = Path(path)
    info = parse_header(path)           # lève ReplayError si corrompu / incomplet
    if not info.complete:
        raise ReplayIncomplete("Rediffusion incomplète (partie en cours ou écriture inachevée)")
    played = info.timestamp.strftime("%Y-%m-%d %H:%M:%S") if info.timestamp else None
    duration = info.length_ms // 1000
    args = resolve_parser(parser_cmd)
    if args:
        data = run_external(args, path)
        events, opened, destroyed, uncertain = count_events(data.get("events", []))
        mode, note = friendly_mode(data.get("mode") or ""), ""
        if data.get("battle_royale") is False:
            mode, note = "Hors Battle Royale", "Partie ignorée : seules les parties Battle Royale sont comptées."
        return MatchRecord(str(path), played, duration, mode, opened, destroyed,
                           "incertaine" if uncertain else "certaine", note, events)
    return MatchRecord(str(path), played, duration, "Inconnu", 0, 0, "indisponible",
                       "Module de détection des coffres introuvable ; seules les métadonnées sont lues.", [])
