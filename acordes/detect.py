"""Detección de acordes desde audio: chroma sincronizado a beats + Viterbi."""
from __future__ import annotations

import numpy as np

from .chart import Chart
from .chords import QUALITIES, Chord

# Pequeña penalización a priori: los acordes "raros" deben ganar con claridad.
_PRIOR = {"maj": 0.0, "min": 0.0, "7": 0.06, "min7": 0.06, "maj7": 0.08,
          "sus2": 0.10, "sus4": 0.10, "dim": 0.10, "aug": 0.12}


def _templates() -> tuple[list[Chord], np.ndarray, np.ndarray]:
    chords, rows, prior = [], [], []
    for q, intervals in QUALITIES.items():
        for root in range(12):
            v = np.zeros(12)
            for i in intervals:
                v[(root + i) % 12] = 1.0
            v[root] += 0.5  # la raíz pesa más
            rows.append(v / np.linalg.norm(v))
            chords.append(Chord(root, q))
            prior.append(_PRIOR[q])
    return chords, np.array(rows), np.array(prior)


def viterbi_chords(chroma: np.ndarray, switch_penalty: float = 1.2, beta: float = 12.0) -> list[Chord | None]:
    """chroma: (12, T) por beat. Devuelve un acorde por columna (None = silencio)."""
    chords, templ, prior = _templates()
    norms = np.linalg.norm(chroma, axis=0)
    unit = chroma / np.maximum(norms, 1e-9)
    obs = beta * (templ @ unit - prior[:, None]).T  # (T, K)
    T, K = obs.shape
    if T == 0:
        return []
    delta = np.zeros((T, K))
    back = np.zeros((T, K), dtype=int)
    delta[0] = obs[0]
    for t in range(1, T):
        best = int(np.argmax(delta[t - 1]))
        switch = delta[t - 1, best] - switch_penalty
        stay = delta[t - 1]
        use_stay = stay >= switch
        delta[t] = np.where(use_stay, stay, switch) + obs[t]
        back[t] = np.where(use_stay, np.arange(K), best)
    path = [int(np.argmax(delta[-1]))]
    for t in range(T - 1, 0, -1):
        path.append(int(back[t, path[-1]]))
    path.reverse()
    silent_floor = 0.05 * (norms.max() if norms.size else 0)
    return [None if norms[t] < silent_floor else chords[k] for t, k in enumerate(path)]


def detect_chart(path: str, beats_per_bar: int = 4, sr: int = 22050) -> Chart:
    import librosa  # import perezoso: es pesado

    y, sr = librosa.load(path, sr=sr, mono=True)
    y_harm = librosa.effects.harmonic(y, margin=3.0)
    hop = 512
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop)
    tempo = float(np.atleast_1d(tempo)[0])
    chroma = librosa.feature.chroma_cqt(y=y_harm, sr=sr, hop_length=hop, n_chroma=12)
    chroma = librosa.util.normalize(chroma, norm=2, axis=0, threshold=1e-6)
    # Sin pad: de beat a beat. Reemplaza silencio real por cero antes de sincronizar.
    rms = librosa.feature.rms(y=y, hop_length=hop)[0][: chroma.shape[1]]
    chroma = chroma[:, : len(rms)] * (rms / (rms.max() + 1e-9))[None, :] ** 0.5
    synced = librosa.util.sync(chroma, beat_frames, aggregate=np.median, pad=False)
    beats = viterbi_chords(synced)
    return Chart(beats, beats_per_bar, tempo=tempo)
