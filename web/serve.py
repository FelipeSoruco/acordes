"""Servidor local: sirve la página y descarga el audio de un enlace de YouTube.

    pip install yt-dlp          (y ffmpeg instalado)
    python web/serve.py         ->  http://127.0.0.1:8765

La página analiza el audio en el navegador; el servidor solo lo descarga.
Escucha únicamente en 127.0.0.1.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).parent
MAX_SECONDS = 600
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}


def valid_youtube_url(url: str) -> bool:
    u = urlparse(url)
    return u.scheme in ("http", "https") and (u.hostname or "").lower() in YOUTUBE_HOSTS


def download_audio(url: str) -> bytes:
    """Baja el audio con yt-dlp y lo devuelve como WAV mono de 22,05 kHz."""
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-warnings", "-x",
            "--audio-format", "wav", "--postprocessor-args", "ffmpeg:-ac 1 -ar 22050",
            "--match-filter", f"duration<={MAX_SECONDS}", "-o", f"{tmp}/audio.%(ext)s", url,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except FileNotFoundError:
            raise RuntimeError("Falta yt-dlp: pip install yt-dlp")
        except subprocess.TimeoutExpired:
            raise RuntimeError("La descarga tardó demasiado.")
        wav = Path(tmp) / "audio.wav"
        if proc.returncode != 0 or not wav.exists():
            tail = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["sin detalles"]
            if "does not pass filter" in (proc.stdout + proc.stderr):
                raise RuntimeError(f"El video dura más de {MAX_SECONDS // 60} minutos.")
            raise RuntimeError(f"No se pudo descargar el audio: {tail[0].split(' (caused by')[0][:220]}")
        return wav.read_bytes()


class Handler(BaseHTTPRequestHandler):
    downloader = staticmethod(download_audio)

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            self._send(200, (HERE / "acordes.html").read_bytes(), "text/html; charset=utf-8")
        elif u.path == "/api/health":
            self._send(200, b"ok", "text/plain")
        elif u.path == "/api/audio":
            url = (parse_qs(u.query).get("url") or [""])[0]
            if not valid_youtube_url(url):
                return self._send(400, "Pega un enlace de YouTube (youtube.com o youtu.be).".encode(), "text/plain; charset=utf-8")
            try:
                self._send(200, self.downloader(url), "audio/wav")
            except RuntimeError as e:
                self._send(502, str(e).encode(), "text/plain; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, fmt, *args) -> None:
        sys.stderr.write("[acordes] " + fmt % args + "\n")


def main(port: int = 8765) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Acordes en http://127.0.0.1:{port}  (Ctrl+C para salir)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
