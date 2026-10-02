import numpy as np
import soundfile as sf

from acordes.chart import parse_text_chart
from acordes.chords import Chord, parse_chord
from acordes.detect import detect_chart
from acordes.shapes import best_shape, candidate_shapes
from acordes.simplify import simplify


def test_parse():
    assert parse_chord("Am7") == Chord(9, "min7")
    assert parse_chord("F#m") == Chord(6, "min")
    assert parse_chord("Bb") == Chord(10, "maj")
    assert parse_chord("G/B") == Chord(7, "maj")
    assert parse_chord("C9") == Chord(0, "7")


def test_shapes_sound_right():
    open_strings = [4, 9, 14, 19, 23, 28]
    for root in range(12):
        for q in ("maj", "min", "7", "min7", "maj7"):
            c = Chord(root, q)
            for s in candidate_shapes(c):
                notes = {(o + f) % 12 for o, f in zip(open_strings, s.frets) if f is not None}
                assert notes <= {(root + i) % 12 for i in (0, 3, 4, 7, 10, 11)}, (c, s)
                assert root in notes


def test_simplify_prefers_capo():
    chart = parse_text_chart("| F#m | D | A | E |")
    r = simplify(chart, level=2)
    assert r.capo == 2  # Em C G D con capo 2... suena igual
    assert [x.name for x, _ in r.chart.runs()] == ["Em", "C", "G", "D"]


def test_levels_reduce_quality():
    chart = parse_text_chart("| Cmaj7 | Am7 | Dm7 G7 | Csus4 C |")
    r1 = simplify(chart, 1, allow_capo=False)
    assert {c.quality for c in r1.chart.beats} <= {"maj", "min"}
    r3 = simplify(chart, 3, allow_capo=False)
    assert r3.chart.beats == chart.beats


def test_difficulty_decreases_with_level():
    chart = parse_text_chart("| Bbmaj7 | Gm7 | Ebmaj7 | F7sus4 |")
    d = [simplify(chart, lv).difficulty for lv in (3, 2, 1)]
    assert d[0] >= d[1] >= d[2]


def test_detect_audio(tmp_path):
    sr = 22050
    prog = [("C", [0, 4, 7]), ("A", [9, 0, 4]), ("F", [5, 9, 0]), ("G", [7, 11, 2])]
    bpm, beat = 120, 0.5
    out = []
    for _, pcs in prog:
        n = int(sr * beat * 4)
        t = np.arange(n) / sr
        s = np.zeros(n)
        for pc in pcs:
            f = 130.81 * 2 ** (pc / 12)
            for h in (1, 2, 3):
                s += np.sin(2 * np.pi * f * h * t) / h
        s *= 0.2 / max(1, np.abs(s).max())
        for b in range(4):  # clic para el seguimiento de pulso
            i = int(b * beat * sr)
            s[i:i + 300] += 0.8 * np.hanning(300)
        out.append(s)
    path = tmp_path / "t.wav"
    sf.write(path, np.concatenate(out * 2), sr)
    chart = detect_chart(str(path))
    found = [x.name for x, _ in chart.runs() if x]
    assert "C" in found and "F" in found and "G" in found, found
