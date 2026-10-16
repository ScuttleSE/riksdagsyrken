import hashlib
import json
import time
from pathlib import Path

import requests

CACHE = Path(__file__).parent / "cache"
CACHE.mkdir(exist_ok=True)
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "riksdagsyrken/1.0 (hobby project; contact via github)"


def get_json(url, params):
    key = hashlib.sha1((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    path = CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    for attempt in range(10):
        r = SESSION.get(url, params=params, timeout=60)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(int(r.headers.get("Retry-After", 0) or 0) or 10 * (attempt + 1))
            continue
        r.raise_for_status()
        data = r.json()
        path.write_text(json.dumps(data, ensure_ascii=False))
        time.sleep(0.2)
        return data
    raise RuntimeError(f"failed {url} {params}")


WP = "https://sv.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"


def parse_html(page):
    d = get_json(WP, {"action": "parse", "page": page, "prop": "text", "format": "json",
                      "formatversion": 2, "redirects": 1})
    return d["parse"]["text"]
