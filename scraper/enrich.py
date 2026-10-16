"""Steg 2: berika varje person med Wikidata (yrke, födelseår, kön, bild) och ingressen från sv.wikipedia."""
import json
from pathlib import Path

from common import WD, WP, get_json

OUT = Path(__file__).parent / "out"


def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def wp_pages(titles):
    info = {}
    for batch in chunks(titles, 20):
        d = get_json(WP, {"action": "query", "titles": "|".join(batch), "prop": "pageprops|extracts",
                          "ppprop": "wikibase_item", "exintro": 1, "explaintext": 1, "redirects": 1,
                          "format": "json", "formatversion": 2})
        q = d["query"]
        alias = {t: t for t in batch}
        for n in q.get("normalized", []):
            alias = {k: (n["to"] if v == n["from"] else v) for k, v in alias.items()}
        for r in q.get("redirects", []):
            alias = {k: (r["to"] if v == r["from"] else v) for k, v in alias.items()}
        pages = {p["title"]: p for p in q["pages"]}
        for orig, canon in alias.items():
            p = pages.get(canon)
            if not p or p.get("missing"):
                continue
            info[orig] = {"title": canon, "qid": p.get("pageprops", {}).get("wikibase_item"),
                          "extract": p.get("extract", "")}
    return info


def claim_ids(ent, prop):
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if isinstance(v, dict) and "id" in v:
            out.append(v["id"])
        elif isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict) and "time" in v:
            out.append(v["time"])
    return out


def wd_entities(qids, props="claims|labels"):
    ents = {}
    for batch in chunks(qids, 50):
        d = get_json(WD, {"action": "wbgetentities", "ids": "|".join(batch), "props": props,
                          "languages": "sv|en", "format": "json"})
        ents.update(d.get("entities", {}))
    return ents


def main():
    terms = json.loads((OUT / "terms.json").read_text())
    titles = sorted({m["page"] for t in terms for m in t["members"] if m["page"]})
    print(len(titles), "artiklar")
    pages = wp_pages(titles)
    qids = sorted({p["qid"] for p in pages.values() if p["qid"]})
    print(len(qids), "wikidata-objekt")
    ents = wd_entities(qids)
    people = {}
    occ_ids = set()
    for q in qids:
        e = ents.get(q, {})
        occ = claim_ids(e, "P106")
        occ_ids.update(occ)
        birth = claim_ids(e, "P569")
        people[q] = {
            "occ": occ,
            "born": int(birth[0][1:5]) if birth and birth[0][1:5].isdigit() else None,
            "gender": {"Q6581097": "man", "Q6581072": "kvinna"}.get((claim_ids(e, "P21") or [None])[0]),
            "image": (claim_ids(e, "P18") or [None])[0],
        }
    occ_ents = wd_entities(sorted(occ_ids), "labels")
    labels = {}
    for q, e in occ_ents.items():
        l = e.get("labels", {})
        labels[q] = (l.get("sv") or l.get("en") or {}).get("value", q)
    (OUT / "enriched.json").write_text(json.dumps(
        {"pages": pages, "people": people, "occ_labels": labels}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
