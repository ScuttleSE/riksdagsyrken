"""Läser riksdagens öppna data (person.csv från riksdagen.se) och sammanställer en post per person.

Filen hämtas manuellt från
https://www.riksdagen.se/sv/dokument-och-lagar/riksdagens-oppna-data/ledamoter/
och läggs i projektroten (den versionshanteras inte).
"""
import csv
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

CSV = Path(__file__).parent.parent / "person.csv"

SEAT_ROLES = {"Riksdagsledamot", "Talman", "Förste vice talman", "Andre vice talman", "Tredje vice talman"}
SUB_ROLES = {"Ersättare", "Statsrådsersättare", "Talmansersättare"}


def fold_accents(s):
    """Tar bort accenter (Dženan Čišija -> dzenan cisija) men behåller å, ä och ö."""
    out = []
    for ch in unicodedata.normalize("NFC", s):
        if ch in "åäöÅÄÖ":
            out.append(ch)
        else:
            out.append("".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c)))
    return "".join(out)


def norm_name(s):
    s = fold_accents(s).lower()
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


PERSONLISTA = Path(__file__).parent / "out" / "riksdagen_personlista.json"
PERSONLISTA_URL = "https://data.riksdagen.se/personlista/?rdlstatus=samtliga&utformat=json"


def load_personlista():
    """Riksdagens personlista (med biografi och bildlänkar), cachad i out/."""
    if not PERSONLISTA.exists():
        from common import SESSION
        r = SESSION.get(PERSONLISTA_URL, timeout=300)
        r.raise_for_status()
        PERSONLISTA.write_bytes(r.content)
    persons = json.loads(PERSONLISTA.read_text())["personlista"]["person"]
    return {p["intressent_id"]: p for p in persons}


# "Juristexamen" -> "jurist", "Sjuksköterskeutbildning" -> "sjuksköterska" osv.
DEGREE_STEMS = {
    "jurist": "jurist", "lärar": "lärare", "förskollärar": "förskollärare", "socionom": "socionom",
    "sjuksköterske": "sjuksköterska", "barnskötar": "barnskötare", "undersköterske": "undersköterska",
    "mentalskötar": "mentalskötare", "läkar": "läkare", "polis": "polis", "ingenjörs": "ingenjör",
    "civilingenjörs": "civilingenjör", "officers": "officer", "präst": "präst", "journalist": "journalist",
    "ekonom": "ekonom", "civilekonom": "civilekonom", "fritidsledar": "fritidsledare",
    "fritidspedagog": "fritidspedagog", "yrkeslärar": "yrkeslärare", "speciallärar": "speciallärare",
    "tandläkar": "tandläkare", "apotekar": "apotekare", "psykolog": "psykolog", "agronom": "agronom",
    "arkitekt": "arkitekt", "sjukgymnast": "sjukgymnast", "arbetsterapeut": "arbetsterapeut",
}
DIRECT_DEGREES = re.compile(r"^(civilingenjör|civilekonom|jur\.? ?kand|socionom|agronom|läkare|"
                            r"sjuksköterska|arkitekt|ingenjör|lärare|förskollärare|tandläkare)\b")


TITLE_END = re.compile(r"(are|ör|ist|man|nom|chef|log|iker|sköterska|biträde|ent|tör|konsult|assistent)$")


def _items(text):
    text = text.replace("\r\n", "\n")
    for part in re.split(r"\.\s+|\n|\.$", text):
        part = part.strip(" .¶")
        if part:
            yield part


def _clean(item):
    item = re.sub(r"\([^)]*\)", "", item)
    item = re.split(r",", item)[0]
    item = re.sub(r"\s*\d{2,4}\s*[-–]+\s*(\d{2,4})?.*$", "", item)  # årtal
    item = re.sub(r"\s+\d{2,4}$", "", item)
    item = re.sub(r"\b(vik\.|vikarierande|arvoderad|tf\.?)\s*", "", item, flags=re.I)
    item = item.strip(" -–.").lower()
    words = item.split()
    # "Ekonomichef Jergo" -> "ekonomichef" (arbetsgivaren står ibland utan komma)
    if len(words) > 1 and not words[0].endswith("-") and TITLE_END.search(words[0]):
        item = words[0]
    return item


def bio_professions(person):
    """Yrken ur riksdagens biografi: senaste anställningarna först, därefter yrkesexamina."""
    if not person:
        return []
    up = (person.get("personuppgift") or {}).get("uppgift") or []
    if isinstance(up, dict):
        up = [up]
    jobs, degrees = [], []
    for x in up:
        text = "\n".join(v if isinstance(v, str) else " ".join(map(str, v.values()))
                         for v in (x.get("uppgift") or []))
        if x.get("kod") == "Anställningar":
            for it in _items(text):
                for part in _clean(it).split("/"):
                    if part and len(part.split()) <= 3:
                        jobs.append(part.strip())
        elif x.get("kod") == "Utbildning":
            for it in _items(text):
                w = _clean(it)
                m = DIRECT_DEGREES.match(w)
                if m:
                    degrees.append(m.group(1))
                    continue
                first = w.split()[0] if w else ""
                m = re.match(r"^(.*?)(?:examen|utbildning)$", first)
                if m and m.group(1) in DEGREE_STEMS:
                    degrees.append(DEGREE_STEMS[m.group(1)])
                elif len(w.split()) == 1 and re.search(r"(are|ör|ist|man|nom|tör|eut|log|iker|ska)$", w):
                    # äldre format där yrkesbanan står under "Utbildning": "Skogsarbetare 56-63"
                    jobs.append(w)
    return list(dict.fromkeys(list(reversed(jobs)) + degrees))
