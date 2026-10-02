"""Simplificación: reduce la calidad de los acordes, funde cambios rápidos y elige cejilla."""
from __future__ import annotations

from dataclasses import dataclass

from .chart import Chart
from .chords import Chord
from .shapes import best_shape

# nivel 1: solo mayores/menores · nivel 2: añade séptimas y sus · nivel 3: tal cual
LEVELS = {
    1: {"maj7": "maj", "7": "maj", "min7": "min", "sus2": "maj", "sus4": "maj", "dim": "min", "aug": "maj"},
    2: {"maj7": "maj", "dim": "min", "aug": "maj"},
    3: {},
}
MIN_BEATS = {1: 2, 2: 1, 3: 1}  # un acorde más corto se absorbe en el anterior
MAX_CAPO = 7


@dataclass
class Result:
    chart: Chart
    capo: int          # traste de cejilla (0 = sin cejilla)
    difficulty: float  # dificultad media ponderada de las digitaciones


def _reduce(c: Chord | None, level: int) -> Chord | None:
    if c is None:
        return None
    return Chord(c.root, LEVELS[level].get(c.quality, c.quality))


def _absorb_short(beats: list[Chord | None], min_beats: int) -> list[Chord | None]:
    if min_beats <= 1 or not beats:
        return beats
    out = list(beats)
    # repetir hasta estabilizar: las rachas cortas toman el acorde anterior (o el siguiente)
    changed = True
    while changed:
        changed = False
        runs, i = [], 0
        while i < len(out):
            j = i
            while j < len(out) and out[j] == out[i]:
                j += 1
            runs.append((i, j))
            i = j
        for k, (a, b) in enumerate(runs):
            if b - a < min_beats and len(runs) > 1:
                src = out[runs[k - 1][0]] if k > 0 else out[runs[k + 1][0]]
                for x in range(a, b):
                    out[x] = src
                changed = True
                break
    return out


def _cost(beats: list[Chord | None], shift: int) -> float:
    total, n = 0.0, 0
    for c in beats:
        if c is None:
            continue
        total += best_shape(c.transpose(-shift)).difficulty
        n += 1
    return total / n if n else 0.0


def simplify(chart: Chart, level: int = 2, allow_capo: bool = True) -> Result:
    if level not in LEVELS:
        raise ValueError(f"Nivel desconocido: {level} (usa 1, 2 o 3)")
    beats = _absorb_short([_reduce(c, level) for c in chart.beats], MIN_BEATS[level])
    capos = range(MAX_CAPO + 1) if allow_capo else range(1)
    # a igualdad de dificultad, preferir menos cejilla (el orden de min() lo garantiza)
    capo = min(capos, key=lambda k: (round(_cost(beats, k), 6), k))
    shaped = [None if c is None else c.transpose(-capo) for c in beats]
    new = Chart(shaped, chart.beats_per_bar, chart.tempo, chart.title, list(chart.notes))
    return Result(new, capo, _cost(beats, capo))
