"""Genera acordes.html (página autocontenida) a partir de app.template.html + engine.js."""
from pathlib import Path

here = Path(__file__).parent
engine = (here / "engine.js").read_text().split("if (typeof module")[0]
(here / "acordes.html").write_text((here / "app.template.html").read_text().replace("/*ENGINE*/", engine))
