#!/usr/bin/env python3
"""Matriky MZA Brno (Acta Publica, www.mza.cz/actapublica) bez prohlížeče.

Použití (z kořene projektu):
  mza.py hledat "Obec" [slovo ...] [--stran N]
        -> knihy, které obsahují obec (české, německé i historické jméno). Další slova zúží výsledek (musí být v řádku
           všechna): „Hustopeče 1850“ = jen knihy, jejichž rozsah N/O/Z zahrnuje rok 1850; „Lhota Prostějov“ = jen knihy,
           ve kterých je Prostějov v původci či obcích. --stran N = nejvýš N stran výsledků po 20 knihách (výchozí 5,
           u „Lhota“ jich je přes 30). Výpis: id | č. knihy | původce (typ) | N | O | Z (v závorce rejstřík) | obcí N: obce | snímků
  mza.py puvodce "Farnost" [typ]
        -> knihy podle původce (farnosti); typ = římskokatolická, evangelická, civilní… (část názvu typu původce)
  mza.py info <id>
        -> záhlaví knihy, obce s okresy, jazyk, poznámky, počet snímků a snímky mimo digitalizaci/s omezením
  mza.py snimek <id> <snímek> <vystup.jpg> [nahled] [x0,y0,x1,y1]
        -> snímek v plném rozlišení (slepí dlaždice DeepZoom); "nahled" = 1/4 rozlišení; výřez v relativních
           souřadnicích 0–1 jako u ARON (stáhne jen potřebné dlaždice)
  mza.py link <id> <snímek>   -> trvalý odkaz na snímek (pole `odkaz` v zaznamy.json)
  mza.py svazek <id>          -> zapíše svazek do data/svazky.json (klíč mza_<id>)
<id> je interní číslo knihy z odkazu `…/matrika/detail/<id>` (první sloupec výpisu), NE „číslo knihy“ (signatura).
<snímek> je pořadí snímku v knize od 1 (stejné číslo je v prohlížeči v poli „snímek“).
Ber ohled na server: stahuj jen snímky, které čteš. Podmínky užití: https://www.mza.cz/actapublica/page/view/podminky-uziti-sluzeb
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # shared archive rate limiter

import concurrent.futures as cf
import html, http.cookiejar, json, math, os, re, shutil, subprocess, sys, tempfile, time, unicodedata, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.mza.cz/actapublica/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cj = http.cookiejar.CookieJar()
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))
_op.addheaders = [("User-Agent", "Mozilla/5.0 (rodokmen)")]


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidává složku skriptu
from obraz import magick   # společný hledač ImageMagicku (tools/obraz.py)


def get(url, binary=False):
    err = None
    for attempt in range(4):
        try:
            with _op.open(url, timeout=60) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", "replace")
        except OSError as e:   # i HTTPError (404 u neexistující dlaždice) – volající si ho umí odchytit
            err = e
            if getattr(e, "code", 0) in (403, 404):
                break
            time.sleep(2 * (attempt + 1))
    raise err


def curl_get(url):
    """Obrázkový server (iipsrv) odpovídá jen na HTTP/2 – Python ho neumí (HTTP 426), proto curl (macOS, Windows 10+, Linux)."""
    c = shutil.which("curl") or shutil.which("curl.exe")
    if not c:
        sys.exit("Chybí příkaz curl (obrázky MZA vyžadují HTTP/2). Windows 10+ a macOS ho mají; jinak ho nainstaluj.")
    # The shared limiter wraps curl and handles HTTP rejection and connection failures.
    r = subprocess.run([c, "-sS", "--fail", "-m", "90", "-A", "Mozilla/5.0 (rodokmen)", url], capture_output=True)
    if r.returncode:
        sys.exit(r.returncode if r.returncode == slusne.KOD else f"Stažení selhalo: {url}\n{r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def radky(page):
    """Řádky tabulky „Nalezené matriky“ -> slovníky."""
    out = []
    for tr in re.findall(r"<tr>\s*<td class=\"clickable\".*?</tr>", page, re.S):
        m = re.search(r"matrika/detail/(\d+)", tr)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if not m or len(tds) < 7:
            continue
        bid = m.group(1)
        pv = re.sub(r"<a .*?</a>", "", tds[1], flags=re.S)   # tlačítko s poznámkou o původci
        parts = [text(x) for x in re.split(r"<br\s*/?>", pv)]
        poz = re.search(r'data-content="([^"]*)"', tds[1])
        obce = re.search(r'data-content="([^"]*)"', tds[5])
        names = re.findall(r"<strong>(.*?)</strong>", html.unescape(obce.group(1))) if obce else []

        def rok(td):   # „1621 - 1679 <br> index - “
            a = [text(x) for x in re.split(r"<br\s*/?>", td)]
            return a[0], (a[1] if len(a) > 1 else "")
        out.append({"id": bid, "kniha": text(tds[0]), "puvodce": parts[0], "typ": parts[1] if len(parts) > 1 else "",
                    "poznamka": text(html.unescape(poz.group(1))) if poz else "",
                    "N": rok(tds[2]), "O": rok(tds[3]), "Z": rok(tds[4]),
                    "obce": names, "obce_plne": text(html.unescape(obce.group(1))) if obce else "",
                    "snimku": text(tds[6])})
    return out


def vypis(r):
    def u(k):
        a, i = r[k]
        return f"{k} {a.replace(' - ', '–')}" + (f" (rejstřík {i.replace(' - ', '–')})" if i.strip(" -") else "")
    obce = r["obce_plne"] or ", ".join(r["obce"])
    print(f"{r['id']} | č. {r['kniha']} | {r['puvodce']} ({r['typ']}) | {u('N')} | {u('O')} | {u('Z')} | "
          f"obcí {len(r['obce'])}: {obce[:260]} | {r['snimku']} snímků")


def vysledky(url, stran):
    nalez, videno = [], set()
    for p in range(1, stran + 1):
        page = get(url + ("" if p == 1 else f"&page={p}"))
        rows = radky(page)
        if p == 1 and not rows and "matrika/detail/" in page:
            sys.exit("Výsledky se nepodařilo přečíst (portál změnil stránku?). Hledej na portálu v prohlížeči.")
        nove = [r for r in rows if r["id"] not in videno]
        if not nove:
            break
        videno |= {r["id"] for r in nove}
        nalez += nove
        if f"page={p + 1}" not in page:
            break
        time.sleep(0.5)
    return nalez


def holy(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c))


def shoda(r, w):
    """Čtyřmístné číslo = rok uvnitř některého z rozsahů N/O/Z; jinak slovo (bez diakritiky) v textu řádku."""
    if re.fullmatch(r"\d{4}", w):   # i jednoletý rozsah („1850“) a otevřený („1850 -“)
        return any(int(a) <= int(w) <= int(b or (9999 if pom else a)) for k in ("N", "O", "Z")
                   for a, pom, b in re.findall(r"(\d{4})(\s*-\s*(?=\d{4}|$|,))?(?:(\d{4}))?", r[k][0]))
    hodnoty = [r["kniha"], r["puvodce"], r["typ"], r["poznamka"], r["obce_plne"]]
    return holy(w) in holy(" ".join(hodnoty))


def hledat(args, stran):
    if not args:
        sys.exit(__doc__)
    nalez = vysledky(f"{BASE}matrika/hledani_obec?typ=obec&search_by_obec={urllib.parse.quote(args[0])}", stran)
    shody = [r for r in nalez if all(shoda(r, w) for w in args[1:])]
    for r in shody:
        vypis(r)
    if not shody:
        print(f"Nic nenalezeno (prohlédnuto {len(nalez)} knih). Zkus jiný tvar jména (německý, bez přívlastku) nebo méně slov.",
              file=sys.stderr)
    if len(nalez) >= 20 * stran:
        print(f"… možná je výsledků víc (načteno {stran} stran); zúžit jde dalším slovem (farnost, okres, rok) nebo --stran", file=sys.stderr)


def puvodce(nazev, typ, stran=5):
    typy = {t: i for i, t in re.findall(r'<option value="(\d+)"[^>]*>(.*?)</option>',
                                       get(BASE + "matrika/hledani_puvodce"))}
    tid = ""
    if typ:
        shody = [i for t, i in typy.items() if typ.lower() in html.unescape(t).lower()]
        if len(shody) != 1:
            sys.exit(f"Typ původce „{typ}“ neodpovídá právě jednomu z: " + "; ".join(html.unescape(t) for t in typy))
        tid = shody[0]
    url = (f"{BASE}matrika/hledani_puvodce?typ_puvodce_id={tid}&search_by_puvodce={urllib.parse.quote(nazev)}")
    nalez = vysledky(url, stran)
    for r in nalez:
        vypis(r)
    if not nalez:
        print("Nic nenalezeno (původce se hledá podle začátku názvu; zkus kratší název nebo jiný typ).", file=sys.stderr)
    elif len(nalez) >= 20 * stran:
        print(f"… možná je výsledků víc (načteno {stran} stran); zúžit jde typem původce nebo přesnějším názvem, víc dá --stran", file=sys.stderr)


def kniha(bid):
    if not (bid.isascii() and bid.isdigit()):
        sys.exit("id knihy je číslo z prvního sloupce výpisu `hledat` (ne „číslo knihy“ / signatura).")
    page = get(f"{BASE}matrika/detail/{bid}")
    m = re.search(r"CreateSeadragon\(\s*(\[.*?\]),\s*(\[.*?\]),\s*(\[.*?\])", page, re.S)
    if not m:
        sys.exit(f"Kniha {bid} nemá digitalizované snímky (nebo číslo neexistuje).")
    return page, json.loads(m.group(1)), json.loads(m.group(2)), json.loads(m.group(3))


def hlavicka(page):
    """Číslo knihy, původce, roky N/O/Z (první řádek buňky, bez rejstříku) a oddíly záložky „Podrobnosti o matrice“."""
    cislo = re.search(r"Číslo knihy</span>\s*<br><span[^>]*>(.*?)</span>", page, re.S)
    pv = re.search(r"Původce</span>\s*<br><span[^>]*>(.*?)</span>", page, re.S)
    roky = {}
    for lab in ("Narození", "Oddaní", "Zemřelí"):
        m = re.search(lab + r":\s*<span[^>]*>\s*(.*?)\s*</span>", page, re.S)
        if m:
            roky[lab] = text(re.split(r"<br\s*/?>", m.group(1))[0]).replace(" - ", "–")
    i = page.find('id="pill_data_extra"')
    extra = text(page[i:]) if i >= 0 else ""   # celý zbytek stránky (seznam obcí bývá dlouhý)
    oddily = {}
    for lab, stop in (("Obce a jiné lokality", "Technické informace"), ("Technické informace", "Poznámka o původci"),
                      ("Poznámka o původci", "Provozovatel")):
        m = re.search(lab + r"(.*?)" + stop, extra)
        if m:
            oddily[lab] = m.group(1).strip()
    return (text(cislo.group(1)) if cislo else "?", text(pv.group(1)) if pv else "?", roky, oddily)


def info(bid):
    page, src, names, stat = kniha(bid)
    cislo, pv, roky, oddily = hlavicka(page)
    print(f"id {bid} | č. knihy {cislo} | původce {pv} | {len(src)} snímků")
    for lab, v in roky.items():
        print(f"{lab}: {v}")
    for lab, v in oddily.items():
        print(f"{lab}: {v[:900]}")
    n = sum(1 for s in stat if s)
    if n:
        print(f"Snímků s příznakem stavu (pravděpodobně omezený nebo chybějící): {n}, "
              f"např. {', '.join(str(i + 1) for i, s in enumerate(stat) if s)[:120]}")
    print("Části matriky / rejstříky: na portálu v záložce „Části matriky“ (odkazují na snímky)")


def cislo_snimku(n, names):
    if not (n.isascii() and n.isdigit()) or not 1 <= int(n) <= len(names):
        sys.exit(f"Snímek musí být číslo 1–{len(names)}.")
    return int(n)


def link(bid, n):
    _, _, names, _ = kniha(bid)
    k = cislo_snimku(n, names)
    return f"{BASE}matrika/detail/{bid}?image={names[k - 1]}"


def snimek(bid, n, out, nahled=False, orez=None):
    MAGICK = magick()
    _, src, names, _ = kniha(bid)
    k = cislo_snimku(n, names)
    dzi = src[k - 1]
    if not dzi.startswith("https://www.mza.cz/") or not dzi.endswith(".dzi"):
        sys.exit(f"Neočekávaná adresa obrázku: {dzi[:80]}")
    base = dzi[:-len(".dzi")] + "_files"
    x = curl_get(dzi).decode()
    W, H, T = (int(re.search(fr'{a}="(\d+)"', x).group(1)) for a in ("Width", "Height", "TileSize"))
    pripona = (re.search(r'Format="(\w+)"', x) or [0, "jpg"])[1].lower()
    if int((re.search(r'Overlap="(\d+)"', x) or [0, "0"])[1]) or pripona not in ("jpg", "jpeg"):
        sys.exit(f"Snímek má dlaždice s překryvem nebo ve formátu {pripona} – nástroj je neumí slepit. Stáhni snímek v prohlížeči.")
    top = math.ceil(math.log2(max(W, H)))   # nejvyšší úroveň DeepZoom = plné rozlišení
    L = top - (2 if nahled else 0)
    w, h = (max(1, math.ceil(a / 2 ** (top - L))) for a in (W, H))
    x0, y0, x1, y1 = orez or (0, 0, 1, 1)
    px0, py0, px1, py1 = int(x0 * w), int(y0 * h), math.ceil(x1 * w), math.ceil(y1 * h)
    tx0, ty0, tx1, ty1 = px0 // T, py0 // T, (px1 - 1) // T, (py1 - 1) // T
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    d = tempfile.mkdtemp(prefix="mza_")   # systémová dočasná složka – v pracovni/ nezůstane nic, ani při přerušení
    try:
        def tile(yx):
            ty, tx = yx
            with open(os.path.join(d, f"{ty:03d}_{tx:03d}.jpg"), "wb") as fh:
                fh.write(curl_get(f"{base}/{L}/{tx}_{ty}.jpg"))
        with cf.ThreadPoolExecutor(4) as ex:   # 4 souběžně jako ostatní nástroje
            list(ex.map(tile, [(ty, tx) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]))
        rows = []
        for ty in range(ty0, ty1 + 1):
            rows.append(f"row{ty:03d}.miff")   # MIFF zachová vlastnosti JPEG (podvzorkování barev)
            subprocess.run([MAGICK, *[f"{ty:03d}_{tx:03d}.jpg" for tx in range(tx0, tx1 + 1)], "+append", rows[-1]],
                           check=True, cwd=d)
        subprocess.run([MAGICK, *rows, "-append", "-crop", f"{px1 - px0}x{py1 - py0}+{px0 - tx0 * T}+{py0 - ty0 * T}",
                        "+repage", "-quality", "88", os.path.abspath(out)], check=True, cwd=d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print(out, f"{px1 - px0}x{py1 - py0}", "odkaz:", f"{BASE}matrika/detail/{bid}?image={names[k - 1]}")


def svazek(bid):
    page, src, _, _ = kniha(bid)
    cislo, pv, rr, oddily = hlavicka(page)
    roky = ", ".join(f"{lab[0]} {v}" for lab, v in rr.items() if v.strip("–- "))
    nazev = f"{pv}, č. knihy {cislo}" + (f" ({roky})" if roky else "")
    path = os.path.join(ROOT, "data", "svazky.json")
    dat = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    dat[f"mza_{bid}"] = {"archiv": "Moravský zemský archiv v Brně – Acta Publica", "portal": "www.mza.cz/actapublica",
                         "svazek": nazev, "popis": oddily.get("Obce a jiné lokality", "")[:400],
                         "url": f"{BASE}matrika/detail/{bid}"}
    tmp = path + ".tmp"   # zápis přes dočasný soubor: přerušení nesmí zkrátit svazky.json
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dat, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    print(f"mza_{bid} -> {nazev}")


def okno(s):
    p = [float(v) for v in s.split(",")]
    if len(p) != 4 or not all(0 <= v <= 1 for v in p) or p[0] >= p[2] or p[1] >= p[3]:
        sys.exit("Výřez: x0,y0,x1,y1 v rozsahu 0–1 (zleva doprava, shora dolů).")
    return p


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    stran = 5
    if "--stran" in a:
        i = a.index("--stran")
        if i + 1 >= len(a) or not a[i + 1].isdigit() or int(a[i + 1]) < 1:
            sys.exit("--stran chce kladné číslo (kolik stran výsledků načíst).")
        stran = int(a[i + 1])
        del a[i:i + 2]
    if not a:
        sys.exit(__doc__)
    if a[0] == "hledat":
        hledat(a[1:], stran)
    elif a[0] == "puvodce" and len(a) >= 2:
        puvodce(a[1], a[2] if len(a) > 2 else "", stran)
    elif a[0] == "info" and len(a) == 2:
        info(a[1])
    elif a[0] == "snimek" and len(a) >= 4:
        rest = a[4:]
        orez = next((okno(r) for r in rest if "," in r), None)
        snimek(a[1], a[2], a[3], "nahled" in rest, orez)
    elif a[0] == "link" and len(a) == 3:
        print(link(a[1], a[2]))
    elif a[0] == "svazek" and len(a) == 2:
        svazek(a[1])
    else:
        sys.exit(__doc__)
