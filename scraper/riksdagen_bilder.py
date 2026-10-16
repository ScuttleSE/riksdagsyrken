"""Steg 2c: hämta porträttbilder från Riksdagens öppna data (personlista) för matchade personer.

Riksdagen visar en grå siluett när foto saknas; de filerna är mycket små och filtreras bort.
Resultatet sparas i out/riksdagen_bilder.json (riksdagens person-id -> bild-URL).
"""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import SESSION
import riksdagen

OUT = Path(__file__).parent / "out"
PLACEHOLDER_MAX_BYTES = 3000


def main():
    persons = riksdagen.load_personlista()
    urls = {i: p.get("bild_url_192") for i, p in persons.items() if p.get("bild_url_192")}

    ids = set(riksdagen.load_ids())
    todo = {i: u for i, u in urls.items() if i in ids}
    out_path = OUT / "riksdagen_bilder.json"
    done = json.loads(out_path.read_text()) if out_path.exists() else {}

    def check(item):
        rid, url = item
        try:
            r = SESSION.head(url, timeout=30, allow_redirects=True)
            size = int(r.headers.get("Content-Length", 0))
            ok = r.ok and r.headers.get("Content-Type", "").startswith("image/") and size > PLACEHOLDER_MAX_BYTES
            return rid, url if ok else None
        except Exception:
            return rid, None

    pending = [(i, u) for i, u in todo.items() if i not in done]
    with ThreadPoolExecutor(8) as ex:
        for rid, url in ex.map(check, pending):
            done[rid] = url
    out_path.write_text(json.dumps(done, indent=0))
    print(f"{sum(1 for v in done.values() if v)} bilder, {sum(1 for v in done.values() if not v)} saknar foto")


if __name__ == "__main__":
    main()
