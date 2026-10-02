import sys, threading, urllib.error, urllib.parse, urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "web"))
import serve  # noqa: E402


def test_valid_urls():
    assert serve.valid_youtube_url("https://www.youtube.com/watch?v=abc")
    assert serve.valid_youtube_url("https://youtu.be/abc")
    assert not serve.valid_youtube_url("http://localhost:22/x")
    assert not serve.valid_youtube_url("https://youtube.com.evil.com/x")
    assert not serve.valid_youtube_url("file:///etc/passwd")


def test_api(monkeypatch):
    def fake(url):
        if "fail" in url:
            raise RuntimeError("No se pudo descargar el audio: x")
        return b"RIFFfake"
    monkeypatch.setattr(serve.Handler, "downloader", staticmethod(fake))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    q = lambda u: base + "/api/audio?url=" + urllib.parse.quote(u)
    try:
        assert urllib.request.urlopen(base + "/api/health").read() == b"ok"
        assert b"Detectar desde YouTube" in urllib.request.urlopen(base + "/").read()
        assert urllib.request.urlopen(q("https://youtu.be/abc")).read() == b"RIFFfake"
        for u, code in (("https://example.com/x", 400), ("https://youtu.be/fail", 502)):
            try:
                urllib.request.urlopen(q(u)); assert False
            except urllib.error.HTTPError as e:
                assert e.code == code
    finally:
        srv.shutdown()
