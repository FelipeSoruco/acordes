"""Modelo de acordes: raíz + calidad, parseo y nombres."""
from __future__ import annotations

import re
from dataclasses import dataclass

NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
_NOTE_INDEX = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# calidad -> intervalos (semitonos sobre la raíz)
QUALITIES: dict[str, tuple[int, ...]] = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "7": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11),
    "min7": (0, 3, 7, 10),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
}
_SUFFIX = {"maj": "", "min": "m", "7": "7", "maj7": "maj7", "min7": "m7",
           "sus2": "sus2", "sus4": "sus4", "dim": "dim", "aug": "aug"}

# sufijo escrito -> calidad (los acordes extendidos se reducen a la más cercana)
_PARSE = {
    "": "maj", "maj": "maj", "M": "maj", "5": "maj", "6": "maj", "add9": "maj",
    "add2": "maj", "69": "maj", "m": "min", "min": "min", "-": "min",
    "m6": "min", "madd9": "min", "7": "7", "9": "7", "11": "7", "13": "7",
    "7sus4": "7", "maj7": "maj7", "M7": "maj7", "maj9": "maj7", "m7": "min7",
    "min7": "min7", "-7": "min7", "m9": "min7", "m11": "min7", "sus": "sus4",
    "sus4": "sus4", "sus2": "sus2", "dim": "dim", "dim7": "dim", "o": "dim",
    "m7b5": "dim", "aug": "aug", "+": "aug",
}
_CHORD_RE = re.compile(r"^([A-G])([#b]?)([^/]*)(?:/([A-G][#b]?))?$")


@dataclass(frozen=True)
class Chord:
    root: int  # 0-11
    quality: str = "maj"

    @property
    def name(self) -> str:
        return NOTE_NAMES[self.root] + _SUFFIX[self.quality]

    def transpose(self, semitones: int) -> "Chord":
        return Chord((self.root + semitones) % 12, self.quality)

    def __str__(self) -> str:
        return self.name


def parse_chord(text: str) -> Chord:
    """'Am7', 'F#m', 'Bb', 'G/B', 'Dsus4'... Lanza ValueError si no se entiende."""
    m = _CHORD_RE.match(text.strip())
    if not m:
        raise ValueError(f"Acorde no reconocido: {text!r}")
    letter, acc, suffix, _bass = m.groups()
    quality = _PARSE.get(suffix)
    if quality is None:
        raise ValueError(f"Calidad de acorde no reconocida: {text!r}")
    root = _NOTE_INDEX[letter] + {"#": 1, "b": -1, "": 0}[acc]
    return Chord(root % 12, quality)
