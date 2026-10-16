"""Steg 1: hämta alla mandatperioder och ledamöter från listorna på sv.wikipedia."""
import json
import re
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup

from common import parse_html

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

INDEX = "Listor_över_ledamöter_av_Sveriges_riksdag"
TERM_RE = re.compile(r"^Lista över ledamöter av Sveriges riksdag (\d{4})–(\d{4})$")

NAME_HEADERS = ("riksdagsledamot", "namn", "ledamot", "avgången ledamot", "ny ledamot", "ersättare")
SKIP_HEADERS = ("ersättare för", "ersätter", "ordinarie ledamot", "ersatt av")


def term_pages():
    soup = BeautifulSoup(parse_html(INDEX), "html.parser")
    head = next(h for h in soup.find_all(["h2"]) if "enkammarriksdag" in h.get_text())
    section = head.find_parent("div", class_="mw-heading") or head
    terms = []
    for el in section.find_next_siblings():
        if el.name in ("h2",) or (el.name == "div" and "mw-heading2" in el.get("class", [])):
            break
        for a in el.find_all("a", title=TERM_RE):
            m = TERM_RE.match(a["title"])
            terms.append((a["title"], int(m.group(1)), int(m.group(2))))
    return sorted(set(terms), key=lambda t: t[1])


def table_grid(table):
    """Expanderar rowspan/colspan till ett rutnät av celler."""
    grid, pending = [], {}
    for tr in table.find_all("tr"):
        row, col = [], 0
        cells = tr.find_all(["td", "th"], recursive=False)
        it = iter(cells)
        while True:
            if col in pending:
                cell, left = pending[col]
                row.append(cell)
                if left <= 1:
                    del pending[col]
                else:
                    pending[col] = (cell, left - 1)
                col += 1
                continue
            cell = next(it, None)
            if cell is None:
                break
            span = int(re.sub(r"\D", "", cell.get("colspan", "1")) or 1)
            rspan = int(re.sub(r"\D", "", cell.get("rowspan", "1")) or 1)
            for _ in range(span):
                row.append(cell)
                if rspan > 1:
                    pending[col] = (cell, rspan - 1)
                col += 1
        while col in pending:
            cell, left = pending.pop(col)
            row.append(cell)
            if left > 1:
                pending[col] = (cell, left - 1)
            col += 1
        grid.append(row)
    return grid


def clean(text):
    text = re.sub(r"\[[^\]]*\]", "", text)
    return re.sub(r"\s+", " ", text).strip(" ,*†")


def person_link(cell):
    for a in cell.find_all("a"):
        href = a.get("href", "")
        if "cite_note" in href or a.find_parent("sup"):
            continue
        if href.startswith("/wiki/") and ":" not in unquote(href[6:]):
            return a.get("title") or unquote(href[6:]).replace("_", " "), clean(a.get_text())
        if "redlink=1" in href:
            return None, clean(a.get_text())
    txt = clean(cell.get_text(" "))
    return (None, txt) if txt else None


def parse_term(title, start, end):
    soup = BeautifulSoup(parse_html(title), "html.parser")
    rows = []
    first_main = True
    for ti, table in enumerate(soup.select("table.wikitable")):
        grid = table_grid(table)
        if len(grid) < 2:
            continue
        header = [clean(c.get_text(" ")).lower() for c in grid[0]]
        if "senaste statusförändring" in header:
            continue  # "nuvarande ledamöter" – dubblett
        name_cols = [i for i, h in enumerate(header)
                     if h.startswith(NAME_HEADERS) and not h.startswith(SKIP_HEADERS)]
        party_cols = [i for i, h in enumerate(header) if h == "parti"]
        vk_cols = [i for i, h in enumerate(header) if h.startswith("valkrets")]
        yrke_cols = [i for i, h in enumerate(header) if h == "yrke"]
        if not name_cols:
            continue
        role = "ordinarie" if first_main else "ersättare"
        first_main = False

        def val(r, cols):
            for i in cols:
                if i < len(r):
                    t = clean(r[i].get_text(" "))
                    if t:
                        return t
            return ""
        for r in grid[1:]:
            if not r or all(c.name == "th" for c in r):
                continue
            seen_cells = set()
            for ci in name_cols:
                if ci >= len(r) or id(r[ci]) in seen_cells:
                    continue
                seen_cells.add(id(r[ci]))
                cell = r[ci]
                if not cell.get_text(strip=True):
                    continue
                link = person_link(cell)
                if not link or not link[1]:
                    continue
                page, name = link
                party = val(r, party_cols)
                vk = re.sub(r",?\s*plats\s*\d+$", "", val(r, vk_cols))
                yrke = val(r, yrke_cols)
                rows.append({"page": page, "name": name, "party": party, "valkrets": vk,
                             "yrke_lista": yrke, "role": "ordinarie" if header[ci] in ("riksdagsledamot", "namn", "ledamot") and role == "ordinarie" else "ersättare/ny"})
    return rows


def main():
    result = []
    for title, start, end in term_pages():
        rows = parse_term(title, start, end)
        dedup = {}
        for r in rows:
            key = r["page"] or r["name"]
            if key not in dedup or (dedup[key]["role"] != "ordinarie" and r["role"] == "ordinarie"):
                dedup[key] = r
        ordinarie = sum(1 for r in dedup.values() if r["role"] == "ordinarie")
        print(f"{start}–{end}: {len(dedup)} personer ({ordinarie} ordinarie)")
        result.append({"title": title, "start": start, "end": end, "members": list(dedup.values())})
    (OUT / "terms.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
