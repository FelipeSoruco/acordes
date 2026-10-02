# acordes

Genera una versión en guitarra de una canción: detecta los acordes y los simplifica
(menos tipos de acorde, menos cambios rápidos y la mejor cejilla) para que sea más fácil de tocar.

```bash
pip install -e .
acordes cancion.mp3 --nivel 1        # audio -> acordes -> versión fácil
acordes progresion.txt --nivel 2     # o parte de acordes escritos a mano
```

Niveles: `1` solo mayores/menores · `2` añade séptimas y sus (por defecto) · `3` completo.
La cejilla se elige automáticamente para minimizar la dificultad (`--sin-cejilla` la desactiva).

Formato de texto: compases separados por `|`; los acordes de un compás se reparten por igual.
Útil para corregir la detección automática (que no es perfecta) y volver a simplificar.

```
# Mi canción
| Bbmaj7 | Gm7 | Ebmaj7 | F7sus4 F |
```

Pipeline: `detect.py` (chroma CQT sincronizado a beats + Viterbi) → `simplify.py` → `shapes.py` / `render.py`.
Limitaciones: asume compás fijo (`--compas`), sin detección de bajo/inversiones ni de tonalidad.
