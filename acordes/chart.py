"""Rejilla de beats con un acorde por beat, y lectura de cartas de acordes en texto."""
from __future__ import annotations

from dataclasses import dataclass, field

from .chords import Chord, parse_chord


@dataclass
class Chart:
    beats: list[Chord | None]
    beats_per_bar: int = 4
    tempo: float | None = None
    title: str = ""
    notes: list[str] = field(default_factory=list)

    def bars(self) -> list[list[Chord | None]]:
        n = self.beats_per_bar
        return [self.beats[i:i + n] for i in range(0, len(self.beats), n)]

    def runs(self) -> list[tuple[Chord | None, int]]:
        """Acordes consecutivos agrupados: [(acorde, nº de beats)]."""
        out: list[tuple[Chord | None, int]] = []
        for c in self.beats:
            if out and out[-1][0] == c:
                out[-1] = (c, out[-1][1] + 1)
            else:
                out.append((c, 1))
        return out


def parse_text_chart(text: str, beats_per_bar: int = 4) -> Chart:
    """Compases separados por '|' (o por líneas); acordes separados por espacios.

    Los acordes de un compás se reparten por igual: '| Am | F C | G |'.
    Las líneas que empiezan con '#' son comentarios (la primera es el título).
    """
    title = ""
    bars: list[list[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            title = title or line.lstrip("# ").strip()
            continue
        for bar in line.split("|"):
            tokens = bar.split()
            if tokens:
                bars.append(tokens)
    beats: list[Chord | None] = []
    for tokens in bars:
        chords = [None if t in {"N", "N.C.", "-"} else parse_chord(t) for t in tokens]
        for i in range(beats_per_bar):
            beats.append(chords[i * len(chords) // beats_per_bar])
    return Chart(beats, beats_per_bar, title=title)
