"""Lecture de l'en-tête et de la structure en chunks d'un fichier .replay (format Unreal Engine).

Écrit d'après la documentation publique du format ; NON validé sur de vrais replays Fortnite
à ce stade. Toute incohérence lève ReplayError (fichier corrompu/tronqué/format inconnu).
"""
import struct
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

MAGIC = 0x1CA2E27F
HISTORY_COMPRESSION, HISTORY_RECORDED_TIMESTAMP, HISTORY_ENCRYPTION, HISTORY_CUSTOM_VERSIONS = 2, 3, 6, 7
CHUNK_HEADER, CHUNK_REPLAY_DATA, CHUNK_CHECKPOINT, CHUNK_EVENT = 0, 1, 2, 3


class ReplayError(Exception):
    pass


@dataclass
class ReplayInfo:
    file_version: int = 0
    length_ms: int = 0
    network_version: int = 0
    changelist: int = 0
    friendly_name: str = ""
    is_live: bool = False
    timestamp: datetime | None = None
    compressed: bool = False
    encrypted: bool = False
    chunk_counts: dict = field(default_factory=dict)

    @property
    def complete(self) -> bool:
        return (not self.is_live) and self.chunk_counts.get(CHUNK_HEADER, 0) >= 1 \
            and self.chunk_counts.get(CHUNK_REPLAY_DATA, 0) >= 1


class _R:
    def __init__(self, f):
        self.f = f

    def read(self, n):
        b = self.f.read(n)
        if len(b) != n:
            raise ReplayError("Fichier tronqué ou corrompu")
        return b

    def u32(self):
        return struct.unpack("<I", self.read(4))[0]

    def i32(self):
        return struct.unpack("<i", self.read(4))[0]

    def i64(self):
        return struct.unpack("<q", self.read(8))[0]

    def fstring(self):
        n = self.i32()
        if n == 0:
            return ""
        if abs(n) > 4096:
            raise ReplayError("Chaîne invalide dans l'en-tête")
        if n < 0:
            return self.read(-n * 2)[:-2].decode("utf-16-le", "replace")
        return self.read(n)[:-1].decode("latin-1", "replace")


def parse_header(path) -> ReplayInfo:
    info = ReplayInfo()
    try:
        with open(Path(path), "rb") as f:
            r = _R(f)
            if r.u32() != MAGIC:
                raise ReplayError("Ce fichier n'est pas une rediffusion valide")
            info.file_version = r.u32()
            if info.file_version >= HISTORY_CUSTOM_VERSIONS:
                count = r.i32()
                if not 0 <= count <= 256:
                    raise ReplayError("Table de versions invalide")
                r.read(20 * count)
            info.length_ms = r.u32()
            info.network_version = r.u32()
            info.changelist = r.u32()
            info.friendly_name = r.fstring()
            info.is_live = r.u32() != 0
            if info.file_version >= HISTORY_RECORDED_TIMESTAMP:
                ticks = r.i64()
                try:
                    info.timestamp = datetime(1, 1, 1) + timedelta(microseconds=ticks // 10)
                except OverflowError:
                    info.timestamp = None
            if info.file_version >= HISTORY_COMPRESSION:
                info.compressed = r.u32() != 0
            if info.file_version >= HISTORY_ENCRYPTION:
                info.encrypted = r.u32() != 0
                r.read(r.u32())  # clé de chiffrement du fichier (stockée dans l'en-tête)
            start = f.tell()
            f.seek(0, 2)
            end = f.tell()
            f.seek(start)
            while True:
                head = f.read(8)
                if len(head) == 0:
                    break
                if len(head) < 8:
                    raise ReplayError("Chunk tronqué")
                ctype, size = struct.unpack("<Ii", head)
                if size < 0 or f.tell() + size > end:
                    raise ReplayError("Fichier tronqué (écriture inachevée ?)")
                f.seek(size, 1)
                info.chunk_counts[ctype] = info.chunk_counts.get(ctype, 0) + 1
    except OSError as e:
        raise ReplayError(f"Lecture impossible : {e}") from e
    return info
