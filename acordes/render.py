"""Salida en texto: tabla de compases y diagramas de acordes."""
from __future__ import annotations

from .chart import Chart
from .shapes import best_shape, diagram
from .simplify import Result

LEVEL_NAMES = {1: "muy fácil (mayores/menores)", 2: "fácil (con séptimas)", 3: "completo"}


def _bar_text(bar) -> str:
    # un acorde por beat: se muestra cuando cambia, '.' si se mantiene
    out, prev = [], object()
    for c in bar:
        if c == prev:
            out.append(".")
        else:
            out.append("N.C." if c is None else c.name)
        prev = c
    return " ".join(out)


def render_chart(chart: Chart, bars_per_line: int = 4) -> str:
    bars = chart.bars()
    rows = []
    for i in range(0, len(bars), bars_per_line):
        group = [_bar_text(b) for b in bars[i:i + bars_per_line]]
        rows.append("| " + " | ".join(f"{t:<12}" for t in group) + " |")
    return "\n".join(rows)


def render_diagrams(chart: Chart, per_row: int = 6) -> str:
    seen = []
    for c in chart.beats:
        if c is not None and c not in seen:
            seen.append(c)
    blocks = [diagram(best_shape(c)) for c in seen]
    out = []
    for i in range(0, len(blocks), per_row):
        row = blocks[i:i + per_row]
        for line_no in range(max(len(b) for b in row)):
            out.append("   ".join((b[line_no] if line_no < len(b) else "").ljust(11) for b in row).rstrip())
        out.append("")
    return "\n".join(out).rstrip()


def render_result(res: Result, level: int, diagrams: bool = True) -> str:
    chart = res.chart
    head = [f"# {chart.title}" if chart.title else "# Versión para guitarra"]
    info = [f"Nivel: {level} - {LEVEL_NAMES[level]}",
            f"Cejilla: {'sin cejilla' if res.capo == 0 else f'traste {res.capo}'}",
            f"Dificultad media: {res.difficulty:.1f} (1 = abiertos, 3+ = cejillas)"]
    if chart.tempo:
        info.append(f"Tempo aprox.: {chart.tempo:.0f} bpm · {chart.beats_per_bar} beats por compás")
    parts = head + info + ["", "(las formas se tocan con la cejilla; el sonido es el de la canción original)", "",
                           render_chart(chart)]
    if diagrams:
        parts += ["", "Acordes:", "", render_diagrams(chart)]
    return "\n".join(parts) + "\n"
