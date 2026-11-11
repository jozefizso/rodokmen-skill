#!/usr/bin/env python3
"""Databáze politicky a rasově pronásledovaných osob (Památník Terezín, pamatnik-terezin.cz/databaze) bez prohlížeče.

Čeští vězni v koncentračních táborech Buchenwald, Dachau, Flossenbürg (a pobočky), Mauthausen, Ravensbrück, v ghettu Terezín,
internačním táboře, Malé pevnosti Terezín, na Pankráci a dalších (úplnost se liší podle tábora).

Použití (z kořene projektu):
  vezni.py hledat [--prijmeni P] [--jmeno J] [--narozeni "15. 3. 1910"] [--misto M] [--cislo C] [--stran N]
        -> příjmení | jméno | narozen | místo narození | databáze (tábor) | odkaz; N stran po 20 záznamech (výchozí 2).
           Příjmení zkus s diakritikou i bez ní (Novák / Novak – tábory je psaly různě). Hodnota je „začíná na“.
  vezni.py detail <odkaz|slug>
        -> všechna pole: bydliště, kdo předal, transporty, věznění, vězeňská čísla, kde je uložený originál
Údaje jsou z dobových dokumentů (často z Národního archivu) – ověř datum a místo narození v rodině a v matrice.
Citlivé – na web jen se souhlasem rodiny (soukromi.md).
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # shared archive rate limiter

import html, http.cookiejar, json, re, sys, time, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.pamatnik-terezin.cz"
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
_op.addheaders = [("User-Agent", "Mozilla/5.0 (rodokmen)")]
POLE = {"--prijmeni": "s1", "--jmeno": "s2", "--narozeni": "s3", "--misto": "s4", "--cislo": "s7"}


def get(url, data=None, ajax=False):
    err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None,
                                         headers={"X-Requested-With": "XMLHttpRequest"} if ajax else {})
            with _op.open(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except OSError as e:
            err = e
            if getattr(e, "code", 0) in (403, 404):
                break
            time.sleep(2 * (attempt + 1))
    raise err


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def hledat(pole, stran):
    form = get(BASE + "/databaze")
    f = re.search(r'<form method="post" action="">.*?</form>', form, re.S)
    if not f:
        sys.exit("Portál změnil stránku (nenašel jsem hledací formulář). Hledej v prohlížeči.")
    data = dict(re.findall(r'name="(db_\d+)" value="(\d)"', f.group(0)))   # všechny databáze (tábory) zapnuté
    data.update({f"s{i}": "" for i in range(1, 11)})
    data.update(pole)
    n, celkem = 0, None
    for p in range(1, stran + 1):
        j = json.loads(get(BASE + "/databaze", {"ax": "searchBasic", "p": str(p), "o0": "0", "o1": "0", **data}, ajax=True))
        if j.get("err") == "no_result":
            break   # nic nenalezeno – hláška se vypíše níže
        if j.get("err"):
            sys.exit("Portál vrátil chybu: " + text(str(j["err"]))[:200])
        res = j["results"]
        celkem = celkem or re.search(r"Záznamů:\s*([\d\s\xa0]+)", res)
        radky = re.findall(r'<div id="i\d+" class="tr trd">(.*?)</a></div>\s*</div>', res, re.S)
        for r in radky:
            bunky = {c: text(v) for c, v in re.findall(r'<div class="td (\w+)">(.*?)</div>', r, re.S)}
            odkaz = re.search(r'href="(/vezen/[^"]+)"', r)
            print(" | ".join([bunky.get("fmn", ""), bunky.get("gvn", ""), bunky.get("brd", "") or "-", bunky.get("pln", "") or "-",
                              (re.findall(r'<div class="td dbn">(.*?)</div>', r, re.S) or [""])[0].strip(),
                              BASE + odkaz.group(1) if odkaz else "-"]))
            n += 1
        if not radky or f"page_{p + 1}" not in res:
            break
        time.sleep(0.7)
    if n == 0:
        print("Nic nenalezeno (zkus příjmení bez diakritiky, jen příjmení, nebo kratší začátek).", file=sys.stderr)
    elif celkem and n < int(re.sub(r"\D", "", celkem.group(1)) or 0):
        print(f"… celkem {celkem.group(1).strip()} záznamů, zobrazeno {n}; zúžit jde jménem a rokem, víc dá --stran", file=sys.stderr)


def detail(arg):
    url = arg if arg.startswith("http") else f"{BASE}/vezen/{arg.strip('/').split('/')[-1]}"
    if not url.startswith(BASE + "/vezen/"):
        sys.exit("Odkaz musí být ze stránek Památníku Terezín (…/vezen/…).")
    page = get(url)
    t = text(re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S))
    i = t.find("Databáze českých vězňů")
    if i < 0:
        i = t.find("Jméno")
    k = t.find("Cookies", i)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    print((text(h1.group(1)) + " – " if h1 else "") + t[i:k if k > i else i + 1500].strip())


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "hledat":
        pole, stran, i = {}, 2, 1
        while i < len(a):
            if a[i] == "--stran" and i + 1 < len(a) and a[i + 1].isdigit() and int(a[i + 1]) >= 1:
                stran, i = int(a[i + 1]), i + 2
            elif a[i] in POLE and i + 1 < len(a):
                pole[POLE[a[i]]], i = a[i + 1], i + 2
            else:
                sys.exit(__doc__)
        if not pole:
            sys.exit("Zadej aspoň --prijmeni (nebo --jmeno, --narozeni, --misto, --cislo).")
        hledat(pole, stran)
    elif a[0] == "detail" and len(a) == 2:
        detail(a[1])
    else:
        sys.exit(__doc__)
