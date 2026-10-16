"""Extrahera yrkesord ur listornas yrkeskolumn och ur artikelns första mening."""
import re

POLITICAL = {
    "politiker", "riksdagspolitiker", "riksdagsledamot", "kommunalpolitiker", "riksdagsman",
    "partiledare", "statsråd", "minister", "landstingspolitiker", "parlamentsledamot",
    "kvinnosakspolitiker", "lokalpolitiker", "europaparlamentariker", "riksdagskvinna",
}

ADJ = re.compile(
    r"^(?:(?:före detta|f\.d\.|f d|tidigare|förutvarande|pensionerad|svensk|svenska|"
    r"[a-zåäö-]*(?:demokratisk|demokratiske|partistisk|partistiske|kristen|moderat|moderata|liberal|"
    r"centerpartistisk|kommunistisk|konservativ|borgerlig|grön|nationalistisk|"
    r"socialistisk|vänsterpartistisk|folkpartistisk|kristdemokratisk|miljöpartistisk|"
    r"sverigedemokratisk|socialdemokratisk|högerpartistisk|bondeförbundare|"
    r"politiskt aktiv|aktiv|framstående|känd|verksam|uppmärksammad|fackligt aktiv|facklig)|"
    r"och|samt|även|senare|sedermera|numera|f\.? ?d\.?)\s+)+")

STOP_AFTER = re.compile(r"\s(?:som|med|från|i|inom|vid|för|på|hos|och\s+tidigare|under|mellan|åren|sedan|till|av)\s.*$")


def split_terms(phrase):
    phrase = re.sub(r"\([^)]*\)", " ", phrase)
    phrase = re.sub(r"\[[^\]]*\]", " ", phrase)
    parts = re.split(r",|;|/|\s+och\s+|\s+samt\s+|\s+&\s+|\s+senare\s+|\s+sedermera\s+", phrase)
    out = []
    for p in parts:
        p = p.strip().lower()
        p = STOP_AFTER.sub("", " " + p).strip()
        p = ADJ.sub("", p).strip(" .:-–")
        if not p or len(p) < 3 or len(p) > 45:
            continue
        if any(ch.isdigit() for ch in p):
            continue
        words = p.split()
        if len(words) > 3:
            continue
        if p in POLITICAL or words[-1] in POLITICAL:
            continue
        out.append(p)
    return out


def from_list_column(text):
    return split_terms(text)


WORK = re.compile(
    r"\b(?:(?:har\s+|hade\s+)?(?:även\s+|också\s+)?(?:tidigare\s+)?"
    r"(?:arbetat|arbetade|arbeta|jobbat|jobbade|jobba|verkat|verkade)\s+"
    r"(?:(?:hon|han|bland annat|bl\.a\.|tidigare|först|länge|i många år|under många år|bland annat)\s+)*som|"
    r"anställd\s+som|anställdes\s+som|verksam\s+som|yrkesverksam\s+som|tjänstgjorde\s+som|tjänstgjort\s+som|"
    r"studerade\s+till|utbildade\s+sig\s+till|utbildat\s+sig\s+till|utbildad\s+till|utbildad|examen\s+som|"
    r"till\s+yrket|till\s+professionen|bakgrund\s+som|var\s+(?:han|hon)\s+(?:verksam\s+som|anställd\s+som))\s+"
    r"((?:[a-zåäöé-]+)(?:,\s+[a-zåäöé-]+)*(?:\s+och\s+[a-zåäöé-]+)?)")
PROF_SUFFIX = re.compile(
    r"(are|ör|man|log|ist|ent|iker|ekonom|nom|jurist|läkare|sköterska|biträde|lärare|chef|"
    r"redaktör|ingenjör|tekniker|sekreterare|assistent|bonde|präst|pastor|officer|polis|"
    r"inspektör|rektor|adjunkt|lektor|kurator|advokat|socionom|agronom|författare|journalist|"
    r"konsult|kamrer|kassör|elektriker|snickare|ombudsman|arbetare|arbeterska|tjänsteman|"
    r"vetare|forskare|kantor|frisör|egenföretagare|företagare|professor|docent|ambassadör|"
    r"handläggare|samordnare|utredare|säljare|vårdare|skötare|pedagog|terapeut|"
    r"montör|kock|bagare|chaufför|förare|soldat|brandman|väktare|revisor|controller)$")
NOT_PROF = re.compile(r"^(senare|tidigare|sedan|ledamot|ersättare|suppleant|ordförande|talesperson|gruppledare|partiledare|"
                      r"språkrör|kommunalråd|regionråd|politiker|vice)$")


def from_fulltext(text):
    out = []
    for m in WORK.finditer(text or ""):
        words = re.split(r",\s+|\s+och\s+", m.group(1))
        for w in words:
            w = w.strip().lower()
            # "SFI- och högstadielärare": den avkortade första delen hoppas över
            if w.endswith("-") or len(w) < 4 or NOT_PROF.match(w):
                continue
            if PROF_SUFFIX.search(w) and w not in POLITICAL and not w.endswith("partist"):
                out.append(w)
    return list(dict.fromkeys(out))


SENT = re.compile(r"\b(?:är|var)\s+(?:en\s+|ett\s+)?(?:svensk|svenska|sverigefinsk|finlandssvensk)\s+(.*)",
                  re.S)


def from_extract(extract):
    if not extract:
        return []
    m = SENT.search(extract[:1500])
    if not m:
        return []
    rest = m.group(1)
    rest = re.sub(r"\([^)]*\)", " ", rest)
    end = re.search(r"\.\s+[A-ZÅÄÖ0-9]|\.$|\n|,\s+som\s|,\s+född\s|,\s+verksam\s|,\s+bosatt\s|\s+som\s+(?:var|är|mellan|sedan|åren|under|blev|har|satt|valdes|representerade)", rest)
    phrase = rest[:end.start()] if end else rest[:250]
    return split_terms(phrase)
