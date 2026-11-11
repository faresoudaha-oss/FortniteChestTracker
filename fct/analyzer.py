"""Moteur d'analyse : en-tête du replay + backend de détection de coffres interchangeable.

Contrat du backend externe (docs/PARSER.md) : `<parser_cmd> <fichier.replay>` écrit sur stdout un JSON
{"mode": str, "player": str, "events": [{"t_ms": int, "kind": "standard|rare|enterre|special|sprite",
"action": "opened|destroyed", "actor": "player|teammate|enemy|unknown", "certain": bool}]}
Sans backend, aucun coffre n'est compté et le statut est « indisponible » : rien n'est inventé.
"""
import json
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .db import MatchRecord
from .replay_header import ReplayError, parse_header

KINDS = ("standard", "rare", "enterre", "special", "sprite")


@dataclass
class ChestEvent:
    t_ms: int
    kind: str
    action: str   # opened | destroyed
    actor: str    # player | teammate | enemy | unknown
    certain: bool


def run_external(cmd: str, path: Path, timeout=300) -> dict:
    args = shlex.split(cmd, posix=False) + [str(path)]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        out = subprocess.run(args, capture_output=True, timeout=timeout, creationflags=flags)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ReplayError(f"Parseur externe indisponible : {e}") from e
    if out.returncode != 0:
        raise ReplayError("Le parseur a échoué : " + out.stderr.decode("utf-8", "replace")[:200])
    try:
        return json.loads(out.stdout.decode("utf-8"))
    except ValueError as e:
        raise ReplayError("Sortie du parseur illisible") from e


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
        raise ReplayError("Rediffusion incomplète (partie en cours ou écriture inachevée)")
    played = info.timestamp.strftime("%Y-%m-%d %H:%M:%S") if info.timestamp else None
    duration = info.length_ms // 1000
    if parser_cmd:
        data = run_external(parser_cmd, path)
        events, opened, destroyed, uncertain = count_events(data.get("events", []))
        return MatchRecord(str(path), played, duration, data.get("mode") or "Inconnu", opened, destroyed,
                           "incertaine" if uncertain else "certaine", "", events)
    return MatchRecord(str(path), played, duration, "Inconnu", 0, 0, "indisponible",
                       "Aucun module de détection des coffres n'est configuré ; seules les métadonnées sont lues.", [])
