#!/usr/bin/env python3
"""Matricula Online (data.matricula-online.eu) – navigace bez prohlížeče: farnosti, knihy, popisky snímků.

Matricula = církevní matriky Rakouska (i Vídně), Německa, Polska, Itálie, Lucemburska, Srbska (Banát) a Slovinska.
Obrázky ale chrání token, který počítá JavaScript prohlížeče – ten nástroj NEnapodobuje. Snímek se čte v prohlížeči uživatele
(Claude in Chrome / Playwright, viz `portaly.md` → Matricula) nebo si ho uživatel uloží; nástroj najde knihu a číslo snímku.

Použití (z kořene projektu):
  matricula.py oblasti [cesta]        -> země/diecéze (bez cesty: země); cesta např. "oesterreich" nebo "oesterreich/wien"
  matricula.py fary <cesta> [slovo]   -> farnosti v oblasti (např. "oesterreich/wien"); slovo zúží výpis (Matricula nehledá podle obce)
  matricula.py knihy <cesta-fary>     -> knihy fary: id | druh | roky | úložiště (např. "oesterreich/wien/01-am-hof")
  matricula.py snimky <cesta-knihy>   -> popisky snímků knihy v pořadí (např. „02-Taufe_0001“): rejstříky (Index) se poznají podle popisku,
                                         číslo řádku = číslo snímku v prohlížeči; trvalý odkaz je …/<kniha>/?pg=<číslo>
Ber ohled na server: stahuj jen to, co čteš.
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # shared archive rate limiter

import html, json, re, sys, time, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://data.matricula-online.eu/en/"


def get(cesta):
    cesta = cesta.strip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+){0,4}", cesta or "x"):
        sys.exit("Cesta smí obsahovat jen písmena, číslice, pomlčky a lomítka (např. oesterreich/wien/01-am-hof).")
    url = BASE + (cesta + "/" if cesta else "")
    err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rodokmen)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except OSError as e:
            err = e
            if getattr(e, "code", 0) in (403, 404):
                sys.exit(f"Stránka {url} neexistuje (HTTP {e.code}). Zkontroluj cestu pomocí `oblasti` / `fary`.")
            time.sleep(2 * (attempt + 1))
    raise err


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def seznam(cesta, slovo=None):
    koren = not cesta.strip("/")
    page = get("bestande" if koren else cesta)   # země jsou na stránce „Fonds“
    pref = "/en/" + (cesta.strip("/") + "/" if not koren else "")
    n = 0
    for href, nazev in re.findall(r'<a class="list-group-item[^"]*" href="([^"]+)">(.*?)</a>', page, re.S):
        if koren and re.fullmatch(r"/en/[a-z]+/", href) and href not in ("/en/bestande/",):
            nazev = re.sub(r"^\d+\s*", "", text(nazev))
            print(f"{href[len('/en/'):].strip('/')} | {nazev}")
            n += 1
        elif not koren and href.startswith(pref) and href != pref:
            nazev = text(nazev)
            if not slovo or slovo.lower() in nazev.lower() or slovo.lower() in href.lower():
                print(f"{href[len('/en/'):].strip('/')} | {nazev}")
                n += 1
    if n == 0:
        print("Nic nenalezeno.", file=sys.stderr)


def knihy(cesta):
    page = get(cesta)
    n = 0
    for tr in re.findall(r"<tr>\s*<td nowrap>.*?</tr>\s*<tr class=\"collapse\".*?</tr>", page, re.S):
        href = re.search(r'href="(/en/[^"]+/)" target="_blank"', tr)
        bunky = [text(c) for c in re.findall(r"<td nowrap>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>", tr, re.S)[0]] if re.search(r"<td nowrap>.*?</td>\s*<td>", tr, re.S) else []
        ulozeni = re.search(r"<dt>Storage location</dt><dd>(.*?)</dd>", tr, re.S)
        popis = re.search(r"<dt>Description</dt><dd>(.*?)</dd>", tr, re.S)
        if href and bunky:
            print(f"{href.group(1)[len('/en/'):].strip('/')} | {bunky[1]} | {bunky[2]} | {text(ulozeni.group(1)) if ulozeni else '-'}"
                  + (f" | {text(popis.group(1))}" if popis else ""))
            n += 1
    if n == 0:
        print("Žádné knihy (je to opravdu cesta farnosti?).", file=sys.stderr)


def snimky(cesta):
    page = get(cesta)
    m = re.search(r'"labels":\s*', page)
    if not m:
        sys.exit("Stránka nemá seznam snímků (je to cesta knihy, např. oesterreich/wien/01-am-hof/01-01?).")
    try:   # JSON pole se čte celé (i s „]“ v popiscích); prázdné popisky zůstanou na svém místě, escape sekvence se dekódují
        labely, _ = json.JSONDecoder().raw_decode(page, m.end())
    except ValueError:
        sys.exit("Seznam snímků se nepodařilo přečíst (portál změnil stránku?). Otevři knihu v prohlížeči.")
    for i, lab in enumerate(labely, 1):
        print(f"{i} | {lab or '(bez popisku)'}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "oblasti" and len(a) <= 2:
        seznam(a[1] if len(a) > 1 else "")
    elif a[0] == "fary" and 2 <= len(a) <= 3:
        seznam(a[1], a[2] if len(a) > 2 else None)
    elif a[0] == "knihy" and len(a) == 2:
        knihy(a[1])
    elif a[0] == "snimky" and len(a) == 2:
        snimky(a[1])
    else:
        sys.exit(__doc__)
