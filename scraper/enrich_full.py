"""Steg 2b: för personer utan yrke i ingressen, hämta hela artikeltexten (wikitext, 50 åt gången)."""
import json
import re
from pathlib import Path

from common import WP, get_json
from extract import from_extract

OUT = Path(__file__).parent / "out"


def strip_wikitext(t):
    t = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    for _ in range(3):
        t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[(?:Fil|File|Bild|Kategori|Category):[^\]]*\]\]", "", t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"'{2,}", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    return t


def main():
    enr = json.loads((OUT / "enriched.json").read_text())
    titles = sorted({p["title"] for p in enr["pages"].values() if not from_extract(p["extract"])})
    print(len(titles), "artiklar att hämta i helhet")
    full = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        d = get_json(WP, {"action": "query", "titles": "|".join(batch), "prop": "revisions",
                          "rvprop": "content", "rvslots": "main", "format": "json", "formatversion": 2})
        for pg in d["query"]["pages"]:
            revs = pg.get("revisions")
            if revs:
                full[pg["title"]] = strip_wikitext(revs[0]["slots"]["main"]["content"])
    (OUT / "fulltext.json").write_text(json.dumps(full, ensure_ascii=False))
    print(len(full), "hämtade")


if __name__ == "__main__":
    main()
