# Riksdagens yrken

Yrkesbakgrund för alla ledamöter i Sveriges enkammarriksdag från 1971 till idag. Ledamöterna hämtas från
[Listor över ledamöter av Sveriges riksdag](https://sv.wikipedia.org/wiki/Listor_%C3%B6ver_ledam%C3%B6ter_av_Sveriges_riksdag),
avsnittet *Ledamöter av enkammarriksdagen*.

## Datainsamling (`scraper/`)

Kräver Python 3 med `requests`, `beautifulsoup4` och `pyyaml`. Alla API-svar cachas i `scraper/cache/`.

```sh
cd scraper
python3 fetch_lists.py   # mandatperioder + ledamöter (ordinarie, ersättare, nya)
python3 enrich.py        # Wikipedia-ingress + Wikidata (yrke P106, födelseår, kön, bild)
python3 enrich_full.py   # hela artikeltexten för de som saknar yrke i ingressen
python3 riksdagen_bilder.py  # porträtt från riksdagen (kräver person.csv)
python3 build.py         # matchning mot riksdagsdata + klassificering -> web/static/data.json
```

`build.py` använder också `person.csv` från [Riksdagens öppna data](https://www.riksdagen.se/sv/dokument-och-lagar/riksdagens-oppna-data/ledamoter/)
om filen ligger i projektroten (den versionshanteras inte). Personerna matchas på namn, födelseår och mandatperioder;
personer som bara finns hos riksdagen läggs till och listas i `scraper/out/riksdagen_tillagda.txt`.

Yrken hämtas i prioritetsordning från:

1. Riksdagens titel för ledamoten (`person.csv`)
1. Yrkeskolumnen i riksdagslistorna (finns för 1971–1988)
2. Artikelns första mening ("… är en svensk **lärare** och politiker …")
3. Wikidata *yrke* (P106), utom "politiker"
4. Fraser i artikeltexten ("arbetade som …", "till yrket …")

Grupperingen styrs av `scraper/yrkesgrupper.yaml` (reguljära uttryck, första träff vinner).
Manuella rättelser läggs i `scraper/overrides.yaml`, och manuella kopplingar till riksdagsdatan i `scraper/matchningar.yaml`. Personer utan yrkesuppgift listas i `scraper/out/utan_yrke.txt`.

**Huvudyrke** = första yrke som inte är ett politiskt uppdrag. **Alla yrken** = ledamoten räknas i varje grupp.

## Webbplats (`web/`)

SvelteKit (statisk), Tailwind CSS, ECharts och Fuse.js.

```sh
cd web
npm install
npm run dev      # utveckling
npm run build    # statisk sajt i web/build/
```

För GitHub Pages under en undersökväg: `BASE_PATH=/reponamn npm run build`.

## Publicera med Docker

Datan är statisk, så containern innehåller bara den byggda sajten bakom nginx:

```sh
docker build -t riksdagsyrken .
docker run -d -p 8080:80 --name riksdagsyrken riksdagsyrken
# öppna http://localhost:8080
```

Kör scrapern och bygg om imagen när du vill uppdatera datan.
