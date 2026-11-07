#!/usr/bin/env python3
"""Sčítacie hárky 1930 a 1940 zo Slovakiany (Slovenský národný archív, slovakiana.sk) bez prehliadača.

Použití (z kořene projektu):
  slovakiana.py hledat "Obec" [--rok 1930] [--okres "Nové Mesto nad Váhom"] [--vse]
        -> index hárků obce: rok | číslo domu | škatule/hárek | id | odkaz do prohlížeče Slovakiany.
           Uloží i pracovni/slovakiana/<obec>[_<rok>].md a .json (index na později, bez dalších dotazů).
           Hledání je fulltextové – nástroj nechá jen hárky, kde obec přesně odpovídá (--vse: všechny výsledky).
  slovakiana.py harok <cair-id>
        -> popis hárku (obec, ulice a číslo domu, škatule, hárek, datum, vlastník, práva) a adresy snímků
  slovakiana.py stahni <cair-id> [<cair-id> …] [--vystup pracovni/slovakiana]
        -> originály obou stran hárku (JPEG 2000, .jp2) a k nim .jpg na čtení (ImageMagick s JP2 nebo sips na macOS).
           Nejvýš 10 hárků najednou: snímkový server content.slovakiana.sk má v robots.txt „Disallow: /“ a hárky
           mají příznak downloadable: false. Stahuj jen hárky, které opravdu čteš (dům předků), ne celou obec.
           Už stažené soubory se přeskočí.

Šetrnost: Slovakiana chce v robots.txt „Crawl-delay: 10“, proto brzda (tools/slusne.py) pouští na slovakiana.sk
jeden požadavek za 10 s – i obrázky. Hárek jsou 4 požadavky (asi 40 s). Při odpovědi 429/503/403 se web zastaví
pro všechny procesy (30 min a déle, podle Retry-After i déle) a nástroj skončí kódem 3. Když server v hlavičkách
hlásí, že dotazy docházejí (RateLimit-Remaining), brzda počká na obnovení limitu. Nic neobcházej.

Hárky z roku 1940 jsou zčernené (osobní údaje) a snímky k nim Slovakiana nedává – v indexu jsou kvůli úplnosti.
Číslo domu je za lomítkem v poli ulice („-, -/68“ = dům č. 68; „-/-“ = bez čísla).
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda (tools/slusne.py)

import json, os, re, shutil, subprocess, sys, unicodedata, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

API = "https://wcm.slovakiana.sk"
PROHLIZEC = "https://slovakiana.sk/scitacie-harky/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VYSTUP = os.path.join(ROOT, "pracovni", "slovakiana")
STRANA = 200          # výsledků na jeden dotaz hledání (méně dotazů = menší zátěž)
MAX_HARKU = 10        # stahni: nejvýš hárků na jedno spuštění
UA = "Mozilla/5.0 (rodokmen)"
ID_RE = re.compile(r"cair-[a-z0-9]+")


def get(url, binary=False):
    """Jeden požadavek (brzda čeká a hlídá 429/503 sama). Neopakuje se – opakování by server jen zatížilo."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://slovakiana.sk/",
                                               "Accept": "*/*" if binary else "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Slovakiana nezná {url} (HTTP 404). Zkontroluj id (cair-…).")
        raise
    return data if binary else json.loads(data.decode("utf-8"))


def bez_diakritiky(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if not unicodedata.combining(c)).lower().strip()


def cislo_domu(ulice):
    """„-, -/68“ -> „68“, „Hlavná, 12/345“ -> „345 (Hlavná 12)“, „-, -/-“ -> „“."""
    ulice = (ulice or "").strip()
    m = re.match(r"(.*?),\s*([^/]*)/(.*)$", ulice)
    if not m:
        return ulice if ulice not in ("-", "") else ""
    nazev, orient, supisne = (x.strip() for x in m.groups())
    supisne = "" if supisne == "-" else supisne
    ulice_txt = " ".join(x for x in (nazev, orient) if x and x != "-")
    return f"{supisne} ({ulice_txt})" if ulice_txt and supisne else supisne or ulice_txt


def skatule_harek(nazev):
    m = re.search(r"hárok\s+(\d+)/(\d+)", nazev or "")
    return (m.group(1), m.group(2)) if m else ("", "")


def okres(x):
    return next((c["name"] for c in x.get("categories", []) if c.get("level") == 1), "")


def radek(x):
    sk, ha = skatule_harek(x.get("name"))
    ulice = (x.get("censusSheetStreet") or [""])[0]
    return {"id": x["key"], "rok": x.get("displayOriginDate", ""), "obec": x.get("municipality", ""), "okres": okres(x),
            "cislo_domu": cislo_domu(ulice), "ulice": ulice, "skatule": sk, "harek": ha,
            "zcerneny": bool(x.get("blackened")), "snimky": bool(x.get("hasImages")), "nazev": x.get("name", ""),
            "odkaz": PROHLIZEC + x["key"]}


def _poradi(r):
    c = re.match(r"\d+", r["cislo_domu"])
    return (r["rok"], int(c.group(0)) if c else 10 ** 9, r["cislo_domu"], int(r["skatule"] or 0), int(r["harek"] or 0))


def hledat(obec, rok=None, okres_=None, vse=False):
    vysledky, strana, celkem = [], 0, None
    while True:
        q = urllib.parse.urlencode({"searchText": obec, "size": STRANA, "page": strana})
        d = get(f"{API}/censussheet/search?{q}")
        celkem = d.get("totalCount", celkem)
        vysledky += d.get("results", [])
        print(f"  strana {strana + 1}: {len(vysledky)} z {celkem}", file=sys.stderr)
        if not d.get("hasMoreResults") or not d.get("results"):
            break
        strana += 1
    radky = [radek(x) for x in vysledky]
    if not vse:
        radky = [r for r in radky if bez_diakritiky(r["obec"]) == bez_diakritiky(obec)]
    if rok:
        radky = [r for r in radky if r["rok"] == str(rok)]
    if okres_:
        radky = [r for r in radky if bez_diakritiky(okres_) in bez_diakritiky(r["okres"])]
    radky = sorted({r["id"]: r for r in radky}.values(), key=_poradi)
    if not radky:
        ostatni = sorted({f"{x.get('municipality')} ({okres(x)})" for x in vysledky})[:15]
        print(f"Žádný hárek pro obec „{obec}“{f' z roku {rok}' if rok else ''}." +
              (f" Hledání našlo jiné obce: {', '.join(ostatni)} (přesný název zadej tak, jak ho píše Slovakiana, "
               "nebo --vse)." if ostatni else " Zkus slovenský název obce (Slovakiana píše názvy z roku 1930 i dnešní)."))
        return
    okresy = sorted({r["okres"] for r in radky})
    if len(okresy) > 1 and not okres_:
        print(f"Pozor: obec tohoto jména je ve více okresech ({', '.join(okresy)}). Vyber --okres.", file=sys.stderr)
    os.makedirs(VYSTUP, exist_ok=True)
    jmeno = re.sub(r"[^a-z0-9]+", "_", bez_diakritiky(obec)).strip("_") + (f"_{rok}" if rok else "")
    with open(os.path.join(VYSTUP, jmeno + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(radky, f, ensure_ascii=False, indent=1)
    md = [f"# Sčítací hárky – {obec}{f' ({rok})' if rok else ''}", "",
          f"Zdroj: Slovakiana (Slovenský národný archív), hledání „{obec}“, {len(radky)} hárků.", "",
          "| rok | číslo domu | škatule/hárek | okres | id | poznámka |", "|---|---|---|---|---|---|"]
    for r in radky:
        pozn = "zčernený, bez snímku" if r["zcerneny"] else ("" if r["snimky"] else "bez snímku")
        md.append(f"| {r['rok']} | {r['cislo_domu'] or '–'} | {r['skatule']}/{r['harek']} | {r['okres']} | "
                  f"[{r['id']}]({r['odkaz']}) | {pozn} |")
    with open(os.path.join(VYSTUP, jmeno + ".md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")
    print("rok | číslo domu | škatule/hárek | okres | id | odkaz")
    for r in radky:
        pozn = " (zčernený)" if r["zcerneny"] else ""
        print(f"{r['rok']} | {r['cislo_domu'] or '–'} | {r['skatule']}/{r['harek']} | {r['okres']} | "
              f"{r['id']}{pozn} | {r['odkaz']}")
    print(f"\n{len(radky)} hárků. Index: {os.path.relpath(os.path.join(VYSTUP, jmeno + '.md'))} (a .json).")


def popis(cair):
    d = get(f"{API}/culturalobject/{cair}")
    attr = {a["name"]: ", ".join(a.get("values", [])) for a in d.get("attributes", [])}
    return d, attr


def snimky(d):
    """Adresy originálů (JP2) všech digitálních objektů hárku, v pořadí stran."""
    out = []
    for do in d.get("digitalObjects") or []:
        obsah = get(f"{API}/digitalobject/{do['id']}")
        for c in obsah.get("content", []):
            if c.get("type") == "IMAGES":
                for img in c.get("images", []):
                    full = img.get("full") or {}
                    if full.get("fileUrl"):
                        out.append({"url": full["fileUrl"], "velikost": full.get("fileSize"),
                                    "sirka": img.get("width"), "vyska": img.get("height")})
    return out


def harok(cair):
    d, attr = popis(cair)
    print(f"{d.get('name')}\n  id: {cair}  odkaz: {PROHLIZEC}{cair}")
    for k in ("Municipality", "Street", "Box number", "Number of census sheet", "Date", "Owner", "Object's rights"):
        if attr.get(k):
            print(f"  {k}: {attr[k]}" + (f"  (číslo domu: {cislo_domu(attr[k])})" if k == "Street" else ""))
    if d.get("originDateNote"):
        print(f"  den sčítání: {d['originDateNote']}")
    if d.get("blackened") or not d.get("hasImages"):
        print("  snímky: Slovakiana je pro tento hárek nezveřejňuje (zčernený nebo bez snímků).")
        return
    for i, s in enumerate(snimky(d), 1):
        print(f"  strana {i}: {s['sirka']}×{s['vyska']} px, {round((s['velikost'] or 0) / 1024 ** 2, 1)} MB  {s['url']}")


def na_jpg(jp2):
    """.jp2 -> .jpg na čtení. Vrací cestu nebo None (když na to není program)."""
    jpg = os.path.splitext(jp2)[0] + ".jpg"
    if os.path.exists(jpg):
        return jpg
    m = shutil.which("magick")
    if m and "JP2" in subprocess.run([m, "-list", "format"], capture_output=True, text=True).stdout:
        prikaz = [m, jp2, "-quality", "90", jpg]
    elif shutil.which("sips"):   # macOS: umí JPEG 2000 vždy
        prikaz = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90", jp2, "--out", jpg]
    else:
        return None
    p = subprocess.run(prikaz, capture_output=True, text=True)
    return jpg if p.returncode == 0 and os.path.exists(jpg) else None


def stahni(ids, vystup):
    if len(ids) > MAX_HARKU:
        sys.exit(f"Nejvýš {MAX_HARKU} hárků najednou (zadáno {len(ids)}). Snímkový server Slovakiany hromadné "
                 "stahování nepovoluje (robots.txt) – vyber hárky domů, které opravdu čteš, ostatní otevři v prohlížeči.")
    os.makedirs(vystup, exist_ok=True)
    bez_jpg = False
    for cair in ids:
        d, attr = popis(cair)
        print(f"{cair}: {d.get('name')} (dům {cislo_domu(attr.get('Street')) or '–'})")
        if d.get("blackened") or not d.get("hasImages"):
            print("  Slovakiana snímky tohoto hárku nezveřejňuje (zčernený nebo bez snímků) – přeskakuji.")
            continue
        for i, s in enumerate(snimky(d), 1):
            cil = os.path.join(vystup, f"{cair}_{i}_{os.path.basename(urllib.parse.urlsplit(s['url']).path)}")
            if os.path.exists(cil) and (not s["velikost"] or os.path.getsize(cil) == s["velikost"]):
                print(f"  strana {i}: už stažená {os.path.relpath(cil)}")
            else:
                data = get(s["url"], binary=True)
                if s["velikost"] and len(data) != s["velikost"]:
                    sys.exit(f"  strana {i}: stažený soubor má {len(data)} B místo {s['velikost']} B – spojení se "
                             "přerušilo. Spusť příkaz znovu později.")
                tmp = cil + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, cil)
                print(f"  strana {i}: {os.path.relpath(cil)} ({round(len(data) / 1024 ** 2, 1)} MB)")
            jpg = na_jpg(cil)
            if jpg:
                print(f"           na čtení: {os.path.relpath(jpg)}")
            else:
                bez_jpg = True
        info = {"id": cair, "nazev": d.get("name"), "odkaz": PROHLIZEC + cair, "atributy": attr,
                "den_scitani": d.get("originDateNote")}
        with open(os.path.join(vystup, f"{cair}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(info, f, ensure_ascii=False, indent=1)
    if bez_jpg:
        print("\nJPEG 2000 (.jp2) neumím převést na .jpg: ImageMagick tu nemá podporu JP2. Nainstaluj ji "
              "(macOS: brew reinstall imagemagick, Windows: ImageMagick z winget ji má) nebo OpenJPEG (opj_decompress).")


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    prikaz, rest = argv[1], argv[2:]

    def volba(jmeno, vychozi=None):
        if jmeno in rest:
            i = rest.index(jmeno)
            if i + 1 >= len(rest):
                sys.exit(f"Chybí hodnota za {jmeno}.")
            hodnota = rest[i + 1]
            del rest[i:i + 2]
            return hodnota
        return vychozi

    if prikaz == "hledat":
        rok, okres_ = volba("--rok"), volba("--okres")
        vse = "--vse" in rest
        rest = [a for a in rest if a != "--vse"]
        if len(rest) != 1:
            sys.exit('Použití: slovakiana.py hledat "Obec" [--rok 1930] [--okres "Okres"] [--vse]')
        hledat(rest[0], rok, okres_, vse)
    elif prikaz == "harok":
        if len(rest) != 1 or not ID_RE.fullmatch(rest[0]):
            sys.exit("Použití: slovakiana.py harok <cair-id> (např. cair-ko1e3on z odkazu slovakiana.sk/scitacie-harky/…)")
        harok(rest[0])
    elif prikaz == "stahni":
        vystup = volba("--vystup", VYSTUP)
        ids = [ID_RE.search(a).group(0) for a in rest if ID_RE.search(a)]   # bere i celé odkazy
        if not ids or len(ids) != len(rest):
            sys.exit("Použití: slovakiana.py stahni <cair-id|odkaz> [… nejvýš 10] [--vystup složka]")
        stahni(list(dict.fromkeys(ids)), vystup)
    else:
        sys.exit(f"Neznámý příkaz {prikaz}. Spusť slovakiana.py --help.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
