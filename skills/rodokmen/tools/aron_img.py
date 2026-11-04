#!/usr/bin/env python3
"""Stažení snímku matriky z portálu ARON (SOA Zámrsk, aron.vychodoceskearchivy.cz).

Použití:
  aron_img.py <apu_id> <snimek> [uroven] [vystup.jpg] [x0,y0,x1,y1]
      uroven: 0 = plné rozlišení, 1 = polovina (výchozí), 2 = čtvrtina
      x0,y0,x1,y1: jen výřez (zlomky 0..1 celé stránky); u svazku bez ZIPu se stahují jen potřebné dlaždice
  aron_img.py <apu_id> info          -> název svazku a počet snímků
  aron_img.py <apu_id> link <n>      -> trvalý odkaz na snímek n v prohlížeči ARON (pole "odkaz" v zaznamy.json)
  aron_img.py <apu_id> svazek        -> zapíše svazek do data/svazky.json (klíč = prvních 8 znaků apu_id)
  aron_img.py odkazy [--opravit]     -> najde v data/ odkazy z dřívějšího `link`, které otevřou knihu na prvním
                                        snímku (id souboru PUBLISHED); s --opravit je přepíše na správný snímek (TILE)

Snímek se bere ze ZIPu „Stáhnout všechny snímky“ na storage.vychodoceskearchivy.cz: nástroj stáhne jen obsah ZIPu
(asi 50 kB, jednou na svazek) a pak jen ten jeden snímek (1–2 MB), nikdy celý ZIP. Snímky v ZIPu mají asi 3/4 rozlišení
dlaždic, na čtení to stačí. Dlaždicový server imgx.vychodoceskearchivy.cz odpovídá velmi pomalu nebo vůbec,
proto se použije jen u svazku bez ZIPu (nebo když ZIP selže).

Popis svazků a obsah ZIPu se ukládají do pracovni/.cache_aron/ (<apu_id>.json, <apu_id>.zip.json), snímek ze ZIPu
do sdílené mezipaměti obrázků (tools/cache.py, aron/<apu_id>/sn<n>.jpg) – úroveň a výřez se pak dělají z disku.
"""
import glob, json, math, os, re, shutil, ssl, struct, subprocess, sys, tempfile, time, urllib.error, urllib.request, zipfile, zlib
import concurrent.futures as cf
import xml.etree.ElementTree as ET
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
import cache  # noqa: E402 – sdílená mezipaměť obrázků (tools/cache.py): snímek ze ZIPu se stáhne jen jednou

API = "https://aron.vychodoceskearchivy.cz/api/aron"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "pracovni", ".cache_aron")


def magick():
    """Cesta k ImageMagicku; když chybí, skončí hned (před stahováním) srozumitelnou hláškou."""
    m = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, "
                 "Windows: winget install ImageMagick.ImageMagick a restartuj agenta) a spusť nástroj znovu.")
    return m


def get(url, binary=False, tries=2, headers=None, timeout=45):
    # krátký limit a jen 2 pokusy: neodpovídající server (imgx) jinak zdržel nástroj přes 6 minut bez výpisu
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=timeout) as r:
                data = r.read()
            return data if binary else data.decode("utf-8")
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def volume(apu_id):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, apu_id + ".json")
    if not os.path.exists(path):
        data = get(f"{API}/apu/{apu_id}")
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
        os.replace(tmp, path)  # atomic, safe when several processes fetch the same volume
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tiles_by_order(vol):
    out = {}
    for dao in vol.get("digitalObjects", []):
        for f in dao["files"]:
            if f["type"] == "TILE":
                out[f["order"]] = f["referencedFile"]
    return out


def zip_url(vol):
    """Odkaz „Stáhnout všechny snímky“ z popisu svazku (položka typu URL končící .zip), nebo None."""
    for part in vol.get("parts", []):
        for it in part.get("items", []):
            if it.get("type") == "URL" and (it.get("href") or "").lower().endswith(".zip"):
                return it["href"]
    return None


TAIL = 1 << 18   # 256 kB: obsah ZIPu se 500 snímky má asi 50 kB
ZIP_HOST = "storage.vychodoceskearchivy.cz"


class _RangeFile:
    """Soubor na serveru čtený po kouscích (HTTP Range) – zipfile si z něj přečte jen obsah ZIPu."""
    def __init__(self, url, size):
        self.url, self.size, self.pos, self.tail = url, size, 0, None

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def read(self, n=-1):
        if n < 0 or self.pos + n > self.size:
            n = self.size - self.pos
        if n <= 0:
            return b""
        if self.pos >= self.size - TAIL:   # obsah ZIPu je na konci: stáhne se celý jedním dotazem a pak se čte z paměti
            if self.tail is None:
                self.tail = get(self.url, binary=True, headers={"Range": f"bytes={max(0, self.size - TAIL)}-"})
                if len(self.tail) > TAIL:
                    raise OSError("server nepodporuje čtení po částech (Range)")
            start = self.pos - (self.size - len(self.tail))
            data = self.tail[start:start + n]
        else:
            data = get(self.url, binary=True, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"})
            if len(data) != n:
                raise OSError("server nepodporuje čtení po částech (Range)")
        self.pos += len(data)
        return data


def zip_index(apu_id, url):
    """{jméno souboru: [offset hlavičky, komprimovaná velikost, metoda]} – stáhne se jednou a uloží do CACHE."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, apu_id + ".zip.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=45) as r:
        size = int(r.headers["Content-Length"])
    with zipfile.ZipFile(_RangeFile(url, size)) as z:
        idx = {i.filename: [i.header_offset, i.compress_size, i.compress_type] for i in z.infolist()}
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(idx, f)
    os.replace(tmp, path)
    return idx


def snimek_ze_zipu(vol, apu_id, n):
    """Celý snímek n ze ZIPu svazku jedním dotazem Range, uložený ve sdílené mezipaměti. Vrací cestu k souboru."""
    klic = f"aron/{apu_id}/sn{n:04d}.jpg"
    src = cache.cesta(klic)
    if os.path.exists(src):
        cache._pouzito(src)
        cache._zapocti(ZIP_HOST, os.path.getsize(src))
        return src
    url = zip_url(vol)
    name = next(f["name"] for f in vol["digitalObjects"][0]["files"] if f["type"] == "PUBLISHED" and f["order"] == n)
    idx = zip_index(apu_id, url)
    if name not in idx:
        raise OSError(f"{name} v ZIPu chybí")
    off, csize, method = idx[name]
    raw = get(url, binary=True, headers={"Range": f"bytes={off}-{off + 30 + 1024 + csize - 1}"})
    sig, *_, nlen, elen = struct.unpack("<IHHHHHIIIHH", raw[:30])
    if sig != 0x04034B50:
        raise OSError("neplatná hlavička souboru v ZIPu")
    data = raw[30 + nlen + elen: 30 + nlen + elen + csize]
    if len(data) != csize:
        raise OSError("ze ZIPu přišla jen část snímku")
    if method == zipfile.ZIP_DEFLATED:
        data = zlib.decompress(data, -15)
    elif method != zipfile.ZIP_STORED:
        raise OSError(f"nepodporovaná komprese v ZIPu ({method})")
    if cache.pripona(data) != ".jpg":
        raise OSError("snímek v ZIPu není JPEG")
    src = cache.uloz(klic, data)
    if not src:   # mezipaměť nejde zapsat (plný disk, sandbox) – snímek jen do dočasného souboru
        fd, src = tempfile.mkstemp(prefix="aron_", suffix=".jpg")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
    cache._zapocti(ZIP_HOST, len(data), z_disku=False)
    return src


def fetch_from_zip(vol, apu_id, n, level_offset=1, out="page.jpg", crop=None):
    """Snímek ze ZIPu svazku; úroveň a výřez udělá ImageMagick z uloženého snímku."""
    MAGICK = magick()
    src = snimek_ze_zipu(vol, apu_id, n)
    W, H = (int(v) for v in subprocess.run([MAGICK, src + "[0]", "-format", "%w %h", "info:"],
                                            capture_output=True, text=True, check=True).stdout.split())
    if not cache.odvod(src, out, crop, 2 ** level_offset):
        raise OSError("ImageMagick nezpracoval snímek ze ZIPu")
    return out, (W, H)


def fetch_image(dzi_url, level_offset=1, out="page.jpg", crop=None):
    MAGICK = magick()
    dzi = ET.fromstring(get(dzi_url))
    ns = {"d": "http://schemas.microsoft.com/deepzoom/2009"}
    ts = int(dzi.get("TileSize"))
    ov = int(dzi.get("Overlap"))
    size = dzi.find("d:Size", ns)
    W, H = int(size.get("Width")), int(size.get("Height"))
    maxlevel = math.ceil(math.log2(max(W, H)))
    level = maxlevel - level_offset
    scale = 2 ** level_offset
    w, h = math.ceil(W / scale), math.ceil(H / scale)
    cols, rows = math.ceil(w / ts), math.ceil(h / ts)
    c0, r0, c1, r1 = 0, 0, cols - 1, rows - 1
    if crop:
        x0, y0, x1, y1 = crop
        c0, c1 = int(x0 * w // ts), min(cols - 1, int(x1 * w // ts))
        r0, r1 = int(y0 * h // ts), min(rows - 1, int(y1 * h // ts))
    base = dzi_url[: -len(".dzi")] + "_files"
    tmp = tempfile.mkdtemp(prefix="aron_")
    try:
        jobs = []
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                jobs.append((c, r, f"{base}/{level}/{c}_{r}.jpg", os.path.join(tmp, f"{c}_{r}.jpg")))

        def dl(job):
            c, r, url, p = job
            with open(p, "wb") as f:
                f.write(get(url, binary=True, tries=6))
            return job

        # 4 vlákna: brzda pustí 10 obrázků za s i tak a víc souběžných dotazů na macOS shazuje překlad adres
        # (URLError [Errno 8] nodename nor servname) u plného rozlišení
        with cf.ThreadPoolExecutor(4) as ex:
            list(ex.map(dl, jobs))
        # a tile with c > 0 (r > 0) carries `ov` extra pixels on its left (top) edge;
        # crop every tile to its own ts x ts cell, then append rows and columns
        # po řádcích: jeden příkaz na celou stránku by na Windows přesáhl limit délky příkazové řádky (32 767 znaků)
        row_files = []
        for r in range(r0, r1 + 1):
            args = [MAGICK]
            for c in range(c0, c1 + 1):
                p = os.path.join(tmp, f"{c}_{r}.jpg")
                cw, ch = min(ts, w - c * ts), min(ts, h - r * ts)
                ox, oy = (ov if c > 0 else 0), (ov if r > 0 else 0)
                args += ["(", p, "-crop", f"{cw}x{ch}+{ox}+{oy}", "+repage", ")"]
            row_files.append(os.path.join(tmp, f"row_{r}.miff"))   # MIFF zachová vlastnosti JPEG (podvzorkování barev)
            subprocess.run(args + ["+append", row_files[-1]], check=True)
        subprocess.run([MAGICK, *row_files, "-append", "-quality", "88", out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)   # uklidit i při chybě stahování nebo magick
    return out, (W, H)


def bez_snimku(vol, tiles, n):
    """Snímek n ve svazku není: srozumitelná hláška místo KeyError."""
    if not tiles:
        sys.exit(f"Svazek „{vol.get('name', '')}“ nemá v ARONu zveřejněné snímky (scans: 0) – zkus jiný svazek fary "
                 "(bývá i samostatný rejstřík nebo druhopis), nebo ho najdi v prohlížeči ARON.")
    sys.exit(f"Snímek {n} ve svazku není – svazek má snímky {min(tiles)}–{max(tiles)} (aron_img.py <apu_id> info).")


SIT = (urllib.error.URLError, ssl.SSLError, ConnectionError, TimeoutError)   # chyby sítě (ne místních souborů)


def chyba_archivu(e):
    """Výpadek na straně ARONu (certifikát, jiná stránka místo snímku, server neodpovídá): hláška místo tracebacku."""
    duvod = getattr(e, "reason", e)
    if isinstance(duvod, ssl.SSLError) or isinstance(e, ET.ParseError):
        sys.exit("ARON: obrázkový server má neplatný certifikát nebo místo snímku vrací jinou stránku – chyba na straně "
                 f"archivu ({type(duvod).__name__}). Zkus to později; info a link fungují dál, svazky jde plánovat. "
                 "Kontrolu certifikátu nevypínej.")
    if isinstance(e, urllib.error.HTTPError):
        sys.exit(f"ARON vrátil chybu HTTP {e.code} – chyba na straně archivu, zkus to později.")
    sys.exit(f"ARON neodpovídá ({duvod}) – zkus to později.")
ODKAZ = re.compile(r"aron\.vychodoceskearchivy\.cz/apu/([0-9a-f-]{36})/dao/([0-9a-f-]{36})/file/([0-9a-f-]{36})")


def oprav_odkazy(opravit):
    """Odkazy na snímek v data/*.json a data/*.md s id souboru PUBLISHED (dřívější `link`) otevřou knihu na prvním
    snímku. Nahradí to id za id souboru TILE téhož snímku; zbytek souborů zůstane beze změny."""
    soubory = sorted(glob.glob(os.path.join(ROOT, "data", "*.json")) + glob.glob(os.path.join(ROOT, "data", "*.md")))
    texty = {}
    for p in soubory:
        with open(p, encoding="utf-8", newline="") as f:   # newline="": konce řádků zůstanou, jak jsou
            texty[p] = f.read()
    nahrady, nezname, dobre = {}, [], 0
    for apu, dao_id, file_id in sorted({m.groups() for t in texty.values() for m in ODKAZ.finditer(t)}):
        dao = next((d for d in volume(apu).get("digitalObjects", []) if d["id"] == dao_id), {})
        f = next((f for f in dao.get("files", []) if f["id"] == file_id), None)
        tile = f and next((t for t in dao["files"] if t["type"] == "TILE" and t["order"] == f["order"]), None)
        if f and f["type"] == "TILE":
            dobre += 1
        elif tile:
            nahrady[file_id] = tile["id"]
        else:
            nezname.append(f"…/apu/{apu}/dao/{dao_id}/file/{file_id}")
    zmenene = {}
    for p, t in texty.items():
        nove = t
        for stare, tile_id in nahrady.items():
            nove = nove.replace(stare, tile_id)
        if nove != t:
            zmenene[p] = (nove, sum(t.count(stare) for stare in nahrady))
    print(f"odkazy na snímky ARON: {dobre + len(nahrady) + len(nezname)} různých, správně {dobre}, "
          f"na první snímek {len(nahrady)}" + (f", nenalezeno ve svazku {len(nezname)}" if nezname else ""))
    for p, (_, kolik) in zmenene.items():
        print(f"  {os.path.relpath(p, ROOT)}: {kolik}× {'opraveno' if opravit else 'k opravě'}")
    for o in nezname:
        print("  nenalezeno:", o)
    if opravit:
        for p, (nove, _) in zmenene.items():
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(nove)
        if zmenene:
            print("Hotovo. Web: cd web && npm run data && npm run build")
    elif nahrady:
        print("Opravíš je: python3 -I tools/aron_img.py odkazy --opravit")


if __name__ == "__main__":
    if sys.argv[1:2] == ["odkazy"]:
        oprav_odkazy("--opravit" in sys.argv[2:])
        sys.exit(0)
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    apu = sys.argv[1]
    try:
        vol = volume(apu)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Svazek {apu} v ARONu není (HTTP 404) – zkontroluj apu_id (celé id z aron_search.py); "
                     "některé svazky z hledání ARON samotný nezveřejňuje, zkus jiný svazek fary.")
        chyba_archivu(e)
    except SIT + (ValueError,) as e:
        chyba_archivu(e)
    tiles = tiles_by_order(vol)
    if sys.argv[2] == "info":
        print(vol["name"], "|", vol.get("description"))
        print("scans:", len(tiles))
        sys.exit(0)
    if sys.argv[2] == "svazek":
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "data", "svazky.json")
        sv = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        fond, _, rest = vol["name"].partition(": ")
        sv[apu[:8]] = dict(archiv=fond if rest else "", portal="ARON", svazek=rest or vol["name"],
                           popis=(vol.get("description") or "")[:300], snimku=len(tiles),
                           url=f"https://aron.vychodoceskearchivy.cz/apu/{vol['id']}")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(sv, f, ensure_ascii=False, indent=1)
        print(apu[:8], "->", sv[apu[:8]]["svazek"])
        sys.exit(0)
    if sys.argv[2] == "link":
        n = int(sys.argv[3])
        dao = (vol.get("digitalObjects") or [{}])[0]
        # prohlížeč ARON pozná snímek podle id souboru TILE; s id souboru PUBLISHED otevře knihu vždy na prvním snímku
        tile = [f for f in dao.get("files", []) if f["type"] == "TILE" and f["order"] == n]
        if not tile:
            bez_snimku(vol, tiles, n)
        print(f"https://aron.vychodoceskearchivy.cz/apu/{apu}/dao/{dao['id']}/file/{tile[0]['id']}")
        sys.exit(0)
    n = int(sys.argv[2])
    lo = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    out = sys.argv[4] if len(sys.argv) > 4 else f"{apu[:8]}_{n:04d}.jpg"
    crop = tuple(float(v) for v in sys.argv[5].split(",")) if len(sys.argv) > 5 else None
    if n not in tiles:
        bez_snimku(vol, tiles, n)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    try:
        zdroj = None
        if zip_url(vol):
            try:
                path, dims = fetch_from_zip(vol, apu, n, lo, out, crop)
                zdroj = "ZIP"
            except (OSError, zipfile.BadZipFile, StopIteration, KeyError, ValueError, struct.error, zlib.error,
                    subprocess.CalledProcessError) as e:
                print(f"ZIP selhal ({e}), zkouším dlaždice z imgx…", file=sys.stderr, flush=True)
        if not zdroj:
            path, dims = fetch_image(tiles[n], lo, out, crop)
            zdroj = "dlaždice"
    except SIT + (ET.ParseError,) as e:
        chyba_archivu(e)
    print(path, "full size", dims, f"({zdroj})")
