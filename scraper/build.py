"""Steg 3: slå ihop listor + berikning till web/static/data.json."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote

import yaml

from extract import from_extract, from_fulltext, from_list_column

HERE = Path(__file__).parent
OUT = HERE / "out"
WEB = HERE.parent / "web" / "static"

PARTIES = [
    # kod, namn, färg, mönster
    ("S", "Socialdemokraterna", "#E8112D", r"^s$|socialdemokrat"),
    ("M", "Moderaterna", "#52BDEC", r"^m$|moderat"),
    ("C", "Centerpartiet", "#009933", r"^c$|center"),
    ("L", "Liberalerna (Folkpartiet)", "#006AB3", r"^(fp|l)$|folkparti|liberal"),
    ("KD", "Kristdemokraterna", "#000077", r"^kd$|kristdemokrat"),
    ("V", "Vänsterpartiet", "#DA291C", r"^v$|vänsterparti"),
    ("MP", "Miljöpartiet", "#83CF39", r"^mp$|miljöparti"),
    ("SD", "Sverigedemokraterna", "#DDDD00", r"^sd$|sverigedemokrat"),
    ("NYD", "Ny demokrati", "#FFD700", r"ny demokrati"),
    ("-", "Partilös", "#9CA3AF", r"oberoende|partilös"),
]


def party_code(text):
    t = text.lower().strip()
    if t.startswith("oberoende") or "partilös" in t:
        return "-"
    for code, _, _, pat in PARTIES:
        if re.search(pat, t):
            return code
    return "?"


def load_groups():
    cfg = yaml.safe_load((HERE / "yrkesgrupper.yaml").read_text())
    ignore = [re.compile(p) for p in cfg["ignorera"]]
    groups = [(g["namn"], [re.compile(p) for p in g["monster"]]) for g in cfg["grupper"]]
    return ignore, groups


IGNORE, GROUPS = load_groups()
OTHER = "Övrigt"


def classify(raw):
    if any(p.search(raw) for p in IGNORE):
        return None
    for name, pats in GROUPS:
        if any(p.search(raw) for p in pats):
            return name
    return OTHER


def normalize_raw(raw):
    raw = re.sub(r"^(bland annat|utbildad|legitimerad|leg\.|e\.|f\.d\.|förste|andre|bitr\.|biträdande|tillika)\s+", "", raw)
    return raw.strip()


def thumb(image):
    if not image:
        return None
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(image.replace(' ', '_'))}?width=240"


def main():
    terms = json.loads((OUT / "terms.json").read_text())
    enr = json.loads((OUT / "enriched.json").read_text())
    pages, people, occ_labels = enr["pages"], enr["people"], enr["occ_labels"]
    ft_path = OUT / "fulltext.json"
    fulltext = json.loads(ft_path.read_text()) if ft_path.exists() else {}
    overrides_path = HERE / "overrides.yaml"
    overrides = yaml.safe_load(overrides_path.read_text()) if overrides_path.exists() else {}
    overrides = overrides or {}

    members = {}
    unknown_parties = Counter()
    for ti, t in enumerate(terms):
        for m in t["members"]:
            page = pages.get(m["page"]) if m["page"] else None
            key = page["title"] if page else f"{m['name']}#röd"
            p = members.setdefault(key, {
                "id": key, "name": (page["title"] if page else m["name"]), "page": page,
                "list_yrken": [], "terms": [],
            })
            p["name"] = re.sub(r"\s*\(.*\)$", "", p["name"])
            code = party_code(m["party"])
            if code == "?":
                unknown_parties[m["party"]] += 1
            p["terms"].append({"t": ti, "p": code, "vk": m["valkrets"],
                               "r": "o" if m["role"] == "ordinarie" else "e"})
            if m["yrke_lista"]:
                p["list_yrken"].append(m["yrke_lista"])
    if unknown_parties:
        print("Okända partier:", unknown_parties)

    out_members = []
    group_raw = defaultdict(Counter)
    for key, p in members.items():
        page = p["page"] or {}
        qid = page.get("qid")
        wd = people.get(qid, {}) if qid else {}
        cands = []
        for txt in p["list_yrken"]:
            cands += [(r, "lista") for r in from_list_column(txt)]
        cands += [(r, "wikipedia") for r in from_extract(page.get("extract", ""))]
        cands += [(occ_labels.get(o, o).lower(), "wikidata") for o in wd.get("occ", [])]
        if page.get("title") in fulltext:
            cands += [(r, "wikipedia") for r in from_fulltext(fulltext[page["title"]])]
        if key in overrides:
            cands = [(r.lower(), "manuell") for r in overrides[key]] + cands
        profs, seen = [], set()
        for raw, src in cands:
            raw = normalize_raw(raw)
            if raw in seen:
                continue
            seen.add(raw)
            g = classify(raw)
            if not g:
                continue
            profs.append({"y": raw, "g": g, "s": src})
            group_raw[g][raw] += 1
        main = next((x["g"] for x in profs if x["g"] != "Politiska uppdrag"), None) \
            or (profs[0]["g"] if profs else None)
        intro = next((ln for ln in page.get("extract", "").split("\n")
                      if ln.strip() and not re.match(r"(Uppslagsordet|För andra|Den här artikeln|Denna artikel|Se även)", ln)), "")[:600]
        out_members.append({
            "id": key,
            "n": p["name"],
            "w": page.get("title"),
            "q": qid,
            "b": wd.get("born"),
            "k": wd.get("gender"),
            "img": thumb(wd.get("image")),
            "y": profs,
            "h": main,
            "t": p["terms"],
            "i": intro,
        })

    out_members.sort(key=lambda m: m["n"])
    group_names = [g for g, _ in GROUPS] + [OTHER]
    data = {
        "generated": __import__("datetime").date.today().isoformat(),
        "terms": [{"s": t["start"], "e": t["end"], "title": t["title"]} for t in terms],
        "parties": [{"c": c, "n": n, "f": f} for c, n, f, _ in PARTIES],
        "groups": group_names,
        "members": out_members,
    }
    WEB.mkdir(parents=True, exist_ok=True)
    (WEB / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))

    no_prof = [m for m in out_members if not m["y"]]
    print(f"{len(out_members)} personer, {len(no_prof)} utan yrkesuppgift")
    hc = Counter(m["h"] for m in out_members)
    for g, c in hc.most_common():
        print(f"  {c:5}  {g}")
    print("Övrigt:", group_raw[OTHER].most_common(80))
    (OUT / "utan_yrke.txt").write_text("\n".join(m["id"] for m in no_prof))


if __name__ == "__main__":
    main()
