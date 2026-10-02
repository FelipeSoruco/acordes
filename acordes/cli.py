"""Uso:
    acordes cancion.mp3 --nivel 1
    acordes progresion.txt --nivel 2 -o version.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .chart import parse_text_chart
from .render import render_result
from .simplify import simplify

TEXT_EXT = {".txt", ".cho", ".crd"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="acordes", description="Versión en guitarra de una canción, simplificable.")
    p.add_argument("entrada", help="audio (mp3/wav/flac/...) o archivo de texto con acordes (.txt)")
    p.add_argument("-n", "--nivel", type=int, choices=(1, 2, 3), default=2,
                   help="1 muy fácil, 2 fácil (por defecto), 3 completo")
    p.add_argument("--sin-cejilla", action="store_true", help="no proponer cejilla")
    p.add_argument("--compas", type=int, default=4, help="beats por compás (por defecto 4)")
    p.add_argument("--sin-diagramas", action="store_true")
    p.add_argument("-o", "--salida", help="guardar en archivo en vez de imprimir")
    args = p.parse_args(argv)

    path = Path(args.entrada)
    if not path.exists():
        p.error(f"No existe: {path}")
    if path.suffix.lower() in TEXT_EXT:
        chart = parse_text_chart(path.read_text(encoding="utf-8"), args.compas)
    else:
        from .detect import detect_chart
        chart = detect_chart(str(path), args.compas)
        chart.title = path.stem
    res = simplify(chart, args.nivel, allow_capo=not args.sin_cejilla)
    text = render_result(res, args.nivel, diagrams=not args.sin_diagramas)
    if args.salida:
        Path(args.salida).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
