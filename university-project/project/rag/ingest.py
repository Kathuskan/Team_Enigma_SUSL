"""Fetch selected manuals once and index their pages for local evidence review."""
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys

import httpx
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCES = json.loads((ROOT / "rag/sources.json").read_text(encoding="utf-8-sig"))
DIRECT = {"RRDI": "https://drive.usercontent.google.com/download?id=1_3IzlrVF10Av2mlhrGlobinCuXOQDsTr&export=download&confirm=t"}


def index():
    folder = ROOT / "data/manuals"
    folder.mkdir(parents=True, exist_ok=True)
    failures = []
    with sqlite3.connect(folder / "pages.sqlite") as db:
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS pages USING fts5(title, page UNINDEXED, digest UNINDEXED, body)")
        for source in SOURCES:
            title = source["title"]
            target = folder / ("rrdi-fertilizer-2013.pdf" if "RRDI" in source["publisher"] else "irri-plant-health.pdf")
            try:
                if target.exists():
                    content = target.read_bytes()
                else:
                    url = DIRECT["RRDI"] if "RRDI" in source["publisher"] else source["url"]
                    response = httpx.get(url, timeout=20, follow_redirects=True)
                    response.raise_for_status()
                    content = response.content
                if not content.startswith(b"%PDF-"):
                    raise ValueError("Download did not return a PDF")
                reader = PdfReader(io.BytesIO(content))
                digest = hashlib.sha256(content).hexdigest()
                rows = [(title, n, digest, p.extract_text() or "") for n, p in enumerate(reader.pages, 1)]
                if not target.exists():
                    target.write_bytes(content)
                if not any(row[3].strip() for row in rows):
                    raise ValueError("Scanned pages need text review")
                with db:
                    db.execute("DELETE FROM pages WHERE title=?", (title,))
                    db.executemany("INSERT INTO pages VALUES (?,?,?,?)", rows)
                print(f"{title}: indexed {len(rows)} pages for review")
            except Exception as exc:
                failures.append(title)
                print(f"{target.name}: {exc}", file=sys.stderr)
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(index())
