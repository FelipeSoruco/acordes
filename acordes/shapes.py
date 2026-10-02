"""Digitaciones de guitarra y su dificultad. Cuerdas de grave a aguda: E A D G B e."""
from __future__ import annotations

from dataclasses import dataclass

from .chords import Chord, parse_chord

Frets = tuple  # 6 valores: int o None (cuerda muda)


@dataclass(frozen=True)
class Shape:
    chord: Chord
    frets: Frets
    barre: bool
    difficulty: float

    @property
    def base_fret(self) -> int:
        played = [f for f in self.frets if f]
        return min(played) if played else 0


def _f(s: str) -> Frets:
    """'x32010' -> (None, 3, 2, 0, 1, 0); usa ',' si hay trastes de dos cifras."""
    parts = s.split(",") if "," in s else list(s)
    return tuple(None if p == "x" else int(p) for p in parts)


_OPEN = {
    "C": "x32010", "Cmaj7": "x32000", "C7": "x32310",
    "D": "xx0232", "Dm": "xx0231", "D7": "xx0212", "Dmaj7": "xx0222",
    "Dm7": "xx0211", "Dsus4": "xx0233", "Dsus2": "xx0230",
    "E": "022100", "Em": "022000", "E7": "020100", "Em7": "022030",
    "Emaj7": "021100", "Esus4": "022200",
    "G": "320003", "G7": "320001", "Gmaj7": "320002",
    "A": "x02220", "Am": "x02210", "A7": "x02020", "Am7": "x02010",
    "Amaj7": "x02120", "Asus2": "x02200", "Asus4": "x02230",
    "B7": "x21202",
}
# Variantes sin cejilla de acordes que normalmente la requieren.
_EASY_F = {"F": "xx3211", "Fmaj7": "xx3210"}

# Formas móviles: desplazamientos respecto al traste de la raíz (None = muda).
_E_SHAPE = {"maj": (0, 2, 2, 1, 0, 0), "min": (0, 2, 2, 0, 0, 0), "7": (0, 2, 0, 1, 0, 0),
            "min7": (0, 2, 0, 0, 0, 0), "maj7": (0, 2, 1, 1, 0, 0), "sus4": (0, 2, 2, 2, 0, 0),
            "sus2": (0, 2, 4, 4, 0, 0), "dim": (0, 1, 2, 0, None, None),
            "aug": (0, 3, 2, 1, 1, 0)}
_A_SHAPE = {"maj": (None, 0, 2, 2, 2, 0), "min": (None, 0, 2, 2, 1, 0), "7": (None, 0, 2, 0, 2, 0),
            "min7": (None, 0, 2, 0, 1, 0), "maj7": (None, 0, 2, 1, 2, 0), "sus4": (None, 0, 2, 2, 3, 0),
            "sus2": (None, 0, 2, 2, 0, 0), "dim": (None, 0, 1, 2, 1, None),
            "aug": (None, 0, 3, 2, 2, 1)}

_OPEN_SHAPES = {parse_chord(n): _f(s) for n, s in _OPEN.items()}
_EASY_SHAPES = {parse_chord(n): _f(s) for n, s in _EASY_F.items()}


def _open_difficulty(chord: Chord, frets: Frets) -> float:
    d = 1.0
    if chord.quality in ("7", "min7", "maj7", "sus2", "sus4"):
        d += 0.3
    if chord.name in ("G", "C", "G7", "Cmaj7", "Dmaj7"):
        d += 0.4  # estiramientos / dedos separados
    return d


def candidate_shapes(chord: Chord) -> list[Shape]:
    out: list[Shape] = []
    if chord in _OPEN_SHAPES:
        out.append(Shape(chord, _OPEN_SHAPES[chord], False, _open_difficulty(chord, _OPEN_SHAPES[chord])))
    if chord in _EASY_SHAPES:
        out.append(Shape(chord, _EASY_SHAPES[chord], False, 2.0))
    for table, string_root in ((_E_SHAPE, 4), (_A_SHAPE, 9)):
        if chord.quality not in table:
            continue
        fret = (chord.root - string_root) % 12
        if fret == 0 and chord in _OPEN_SHAPES:
            continue
        fret = fret or 12
        frets = tuple(None if o is None else o + fret for o in table[chord.quality])
        out.append(Shape(chord, frets, True, 3.0 + 0.1 * fret))
    return out


def best_shape(chord: Chord) -> Shape:
    return min(candidate_shapes(chord), key=lambda s: s.difficulty)


def diagram(shape: Shape) -> list[str]:
    """Diagrama ASCII de 5 trastes."""
    base = shape.base_fret
    top = base if base > 3 else 1
    lines = [f"{shape.chord.name}" + (f"  ({top}fr)" if top > 1 else "")]
    head = "".join("x" if f is None else ("o" if f == 0 else " ") for f in shape.frets)
    lines.append(" ".join(head))
    lines.append("=" * 11 if top == 1 else "-" * 11)
    for fret in range(top, top + 5):
        row = ["●" if f == fret else "│" for f in shape.frets]
        lines.append(" ".join(row))
    return lines
