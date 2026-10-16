"""Läser riksdagens öppna data (person.csv från riksdagen.se) och sammanställer en post per person.

Filen hämtas manuellt från
https://www.riksdagen.se/sv/dokument-och-lagar/riksdagens-oppna-data/ledamoter/
och läggs i projektroten (den versionshanteras inte).
"""
import csv
import re
import unicodedata
from datetime import date
from pathlib import Path

CSV = Path(__file__).parent.parent / "person.csv"

SEAT_ROLES = {"Riksdagsledamot", "Talman", "Förste vice talman", "Andre vice talman", "Tredje vice talman"}
SUB_ROLES = {"Ersättare", "Statsrådsersättare", "Talmansersättare"}


def norm_name(s):
    s = unicodedata.normalize("NFC", s).lower()
    s = re.sub(r"\s*\(.*?\)", "", s)
    s = re.sub(r"[.,]", " ", s)
    return " ".join(s.split())


def name_keys(first, last):
    """Nycklar för namnmatchning: fullt namn och första förnamn + efternamn."""
    first, last = norm_name(first), norm_name(last)
    keys = {f"{first} {last}"}
    if first:
        keys.add(f"{first.split()[0]} {last}")
        keys.add(f"{first.split('-')[0].split()[0]} {last}")
    return keys


def split_title(t):
    t = t.strip().rstrip(".").strip()
    if not t:
        return []
    parts = re.split(r",|;|\s+och\s+|\s+samt\s+|\s+senare\s+|\s+f\.d\.\s+", t)
    out = []
    for p in parts:
        p = re.sub(r"^(senare|f\.d\.|fd|tidigare)\s+", "", p.strip().lower()).strip(" .")
        if p and not any(ch.isdigit() for ch in p):
            out.append(p)
    return out


def term_bounds(terms):
    """Ungefärliga datumgränser per mandatperiod (val i september, ny riksdag i oktober)."""
    bounds = []
    for i, t in enumerate(terms):
        start = date(1971, 1, 1) if i == 0 else date(t["start"], 10, 1)
        end = date(terms[i + 1]["start"], 10, 1) if i + 1 < len(terms) else date(t["end"] + 1, 1, 1)
        bounds.append((start, end))
    return bounds


def parse_date(s):
    return date.fromisoformat(s[:10]) if s else None


def load(terms):
    if not CSV.exists():
        print(f"Hittar inte {CSV}, hoppar över riksdagsdata")
        return {}
    bounds = term_bounds(terms)
    people = {}
    with CSV.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            p = people.setdefault(r["Id"], {
                "id": r["Id"], "first": r["Förnamn"], "last": r["Efternamn"], "iort": r["Iort"],
                "party": r["Parti"], "gender": r["Kön"] or None,
                "born": int(r["Född"]) if r["Född"].isdigit() else None,
                "valkrets": r["Valkrets"], "titles": split_title(r["Titel"]), "terms": {},
            })
            if r["Uppdragsorgan"] != "kam":
                continue
            role = r["Uppdragsroll"]
            if role in SUB_ROLES and r["Uppdragsrollstatus"] != "Tjänstgörande":
                continue
            if role not in SEAT_ROLES | SUB_ROLES:
                continue
            a, b = parse_date(r["From"]), parse_date(r["Tom"]) or date.today()
            for ti, (s, e) in enumerate(bounds):
                if a < e and b > s and (min(b, e) - max(a, s)).days >= 7:
                    kind = "o" if role in SEAT_ROLES else "e"
                    if p["terms"].get(ti) != "o":
                        p["terms"][ti] = kind
    return {k: v for k, v in people.items() if v["terms"]}


def load_ids():
    if not CSV.exists():
        return []
    with CSV.open(encoding="utf-8-sig") as f:
        return list({r["Id"] for r in csv.DictReader(f)})


def riksdagen_url(p):
    slug = norm_name(f"{p['first']} {p['last']}")
    slug = unicodedata.normalize("NFKD", slug).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return f"https://www.riksdagen.se/sv/ledamoter-och-partier/ledamot/{slug}_{p['id']}/"
