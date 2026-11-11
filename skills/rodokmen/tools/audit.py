#!/usr/bin/env python3
"""Nezávislý pohled na kolo výzkumu (zpětná vazba pro hlavní chat): Codex – jiná rodina modelů – zkontroluje, co se
v kole zapsalo, podívá se na výsledky z jiné strany (jiné výklady, co se přehlíží, kde ještě hledat) a rozhodne,
jak dál. Nahrazuje ruční kopírování zprávy kola do ChatGPT.

Použití: python3 -I tools/audit.py [--kolo N] [--od REF] [--model MODEL] [--bez-webu] [--jen-zadani]
  --kolo N        kolo z pracovni/kolo_<N>/ (plan.md, zprava.md a hlášení čtenářů); bez něj poslední kolo
  --od REF        git revize, od které se počítají změny v data/, vyrezy/ a zdroje/; bez ní revize z minulého
                  auditu (pracovni/audit/kolo_*.json, pole „commit“), jinak HEAD (jen necommitnuté změny)
  --model MODEL   model pro Codex (jinak výchozí z nastavení Codexu)
  --bez-webu      bez webového vyhledávání (jinak ho Codex smí použít na rady, kde hledat)
  --jen-zadani    Codex nespouštět, jen uložit zadání do pracovni/audit/kolo_<N>_zadani.md (pro auditora
                  v podobě pomocníka s čistým kontextem, když Codex není k dispozici)

Codex běží jen pro čtení a jeho příkazy nemají síť (codex exec --sandbox read-only): nic nezmění, na archivy nesahá.
Webové vyhledávání (codex --search) běží na straně OpenAI jako hledání, ne stahování z archivů.
Výsledek uloží do pracovni/audit/kolo_<N>.json a vypíše shrnutí: rozhodnutí, nálezy, jiný pohled, kde hledat
a další úkoly.
Návratový kód: 0 audit proběhl, 1 chyba, 2 Codex není nainstalovaný (zadání je uložené, viz --jen-zadani).
"""
import datetime, glob, json, os, re, shutil, subprocess, sys, tempfile
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRACOVNI = os.path.join(ROOT, "pracovni")
AUDIT = os.path.join(PRACOVNI, "audit")
MAX_DIFF = 60000      # znaků diffu v zadání; delší se zkrátí a auditor si zbytek přečte sám
MAX_KONTROLA = 15000

ROZHODNUTI = ["pokracovat", "opravit", "overit_znovu", "zmenit_postup", "zeptat_se_uzivatele", "zastavit"]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["rozhodnuti", "oduvodneni", "nalezy", "jiny_pohled", "hypotezy", "kde_hledat", "dalsi_ukoly",
                 "otazky_pro_uzivatele", "overeno"],
    "properties": {
        "rozhodnuti": {"type": "string", "enum": ROZHODNUTI},
        "oduvodneni": {"type": "string"},
        "jiny_pohled": {"type": "string"},
        "hypotezy": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["tvrzeni", "proc", "jak_overit"],
            "properties": {
                "tvrzeni": {"type": "string"},
                "proc": {"type": "string"},
                "jak_overit": {"type": "string"}}}},
        "kde_hledat": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["priorita", "pramen", "co_tam_najit", "proc", "odkaz"],
            "properties": {
                "priorita": {"type": "integer"},
                "pramen": {"type": "string"},
                "co_tam_najit": {"type": "string"},
                "proc": {"type": "string"},
                "odkaz": {"type": "string"}}}},
        "nalezy": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["zavaznost", "kde", "problem", "dukaz", "navrh"],
            "properties": {
                "zavaznost": {"type": "string", "enum": ["chyba", "riziko", "poznamka"]},
                "kde": {"type": "string"},
                "problem": {"type": "string"},
                "dukaz": {"type": "string"},
                "navrh": {"type": "string"}}}},
        "dalsi_ukoly": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["priorita", "kdo", "ukol", "proc"],
            "properties": {
                "priorita": {"type": "integer"},
                "kdo": {"type": "string", "enum": ["hlavni", "ctenar", "uzivatel"]},
                "ukol": {"type": "string"},
                "proc": {"type": "string"}}}},
        "otazky_pro_uzivatele": {"type": "array", "items": {"type": "string"}},
        "overeno": {"type": "array", "items": {"type": "string"}},
    },
}

ZADANI = """\
# Nezávislý pohled na kolo rodopisného výzkumu

Jsi nezávislý rodopisec a auditor projektu rodokmenu (české a slovenské matriky). Hlavní agent (Claude) v tomto
kole naplánoval práci, zadal čtení matrik pomocníkům na levnějším modelu („čtenářům“), jejich nálezy měl ověřit
na výřezech a zapsat do `data/`. Ty jsi pohled z jiné strany – jiná rodina modelů, jiné znalosti pramenů.
Máš dva úkoly stejně důležité: **A) ověřit, co se zapsalo**, a **B) podívat se na výsledky jinak, než je vidí
hlavní agent**, a poradit, kde a jak hledat dál.

## Pravidla
- Pracuješ jen pro čtení. Nic neměň, nic nestahuj, na weby archivů nechoď (příkazy v sandboxu nemají síť).
- Spouštět smíš jen příkazy, které nic nezapisují (`git diff`, `git log`, `python3 -I tools/kontrola.py`, čtení souborů).
- Máš-li webové vyhledávání, použij ho na prameny a postupy (který archiv má fond, jaké prameny pro obec a dobu
  existují, digitalizace, regionální literatura). Nehledej jména žijících lidí.
- **Nenech se ukotvit závěry hlavního agenta.** Nejdřív si udělej vlastní obraz z hlášení čtenářů, výřezů a dat,
  teprve potom čti jeho zprávu kola (`pracovni/kolo_<N>/zprava.md`) a porovnej.
- Obrázky výřezů (`vyrezy/`, `zdroje/`, `pracovni/**`) si **otevři a přečti sám** – hlavně u údajů, které se
  v kole nově zapsaly jako doložené (`doc`). Do pole `overeno` napiš, které výřezy jsi skutečně viděl.
- Nejisté čtení nehlas jako chybu; hlas ho jako `riziko` a napiš, co přesně na výřezu vidíš.
- Piš česky, stručně a konkrétně (soubor, klíč záznamu, Kekulé číslo, snímek).

## A) Co zkontrolovat
1. **Zápis proti výřezu:** jméno, datum (den, měsíc, rok), číslo popisné, rodiče, kmotři, stav (svobodný ×
   vdovec), povolání. Nejčastější chyby čtenářů: roky, číslice, stav, povolání a jména svědků u německých
   formulářů. Každý údaj `doc` musí mít záznam v `data/zaznamy.json` s výřezem, přepis v `data/prepisy.json`
   a svazek v `data/svazky.json`.
2. **Hlášení čtenářů proti datům:** nezapsalo se něco, co čtenář hlásil jen jako nejisté? Zapsaly se vedlejší
   nálezy (sourozenci, kmotři, další manželství) do `RODINA` / `SIDE` v `data/osoby.py` nebo do `data/vedlejsi_nalezy.md`?
   Hlásí čtenář u každého prošlého snímku, co na něm skutečně přečetl? Má negativní výsledek přesný rozsah
   (kniha, snímky, roky, čitelnost) a je v `data/research_log.md`?
3. **Logika rodokmenu:** věk rodičů při narození dětí (matka 15–50 let), dítě narozené po smrti matky, křest
   před narozením, sňatek před narozením nevěsty, rodič a dítě stejného jména a místa (záměna generací),
   dvě rodiny stejného jména ve vsi, Kekulé čísla (otec = 2n, matka = 2n + 1), stejná osoba dvakrát (`SAME`).
4. **Pravidla dat:** žádný otazník „?“ jako hodnota (nejisté pole má chybět a být popsané v poznámce), nová
   kniha má záznam v `svazky.json`. Žijící lidé: jen jméno a rok narození (žádné adresy, telefony, rodná čísla,
   zdravotní údaje, rozvody, nemanželské děti u žijících či nedávno zemřelých); citlivé věci z posledních ~100 let
   (sebevražda, věznění, nemoc, oběti války) jen se souhlasem uživatele – jinak `zeptat_se_uzivatele`.
   Ukázková data (příznak `ukazka`, „vymyšlený zápis“) nejsou chyby výzkumu – jen je zmiň v `poznamka`.
5. **Postup:** vyplatilo se kolo? Opakují se chyby čtenářů na stejné knize nebo písmu? Hledá se ve správné
   knize a farnosti? Dokončuje se generace, než se jde do další (pokud uživatel neurčil prioritní větev)?

## B) Pohled z jiné strany
- `jiny_pohled`: několik vět – jak čteš výsledky ty. Co hlavní agent možná bere jako samozřejmé, co by šlo
  vyložit jinak, kde je linie slabší, než vypadá, co je na nálezech zajímavé nebo neobvyklé (migrace, povolání,
  sociální postavení, epidemie, války, změny hranic farností a panství).
- `hypotezy`: jiné výklady, které data připouštějí (jiný otec, jiná rodina stejného jména, přistěhování odjinud,
  nemanželský původ, chybně spojené zápisy, změna příjmení či jména domu) – u každé proč a čím ji ověřit.
- `kde_hledat`: konkrétní prameny, kde najít chybějící údaje nebo ověřit hypotézy – i mimo matriky: matriky
  sousedních farností a filiálek, indexy, sčítání lidu (1857, 1869–1921), pozemkové knihy a gruntovnice,
  urbáře a soupisy poddaných (Berní rula, tereziánský katastr, josefský katastr, soupis podle víry 1651),
  vojenské kmenové listy, domovské a policejní přihlášky, školní a cechovní prameny, notářské a soudní spisy,
  noviny (Kramerius, ANNO), regionální literatura a rodopisné spolky. Uveď archiv nebo portál a odkaz, když
  ho znáš (jinak prázdný řetězec), co přesně tam najít a proč zrovna tam. Seřaď podle priority (1 = nejdřív).

## Rozhodnutí (pole `rozhodnuti`, vyber jedno)
- `pokracovat` – žádná `chyba`; další kolo podle plánu (případně s tvými úkoly navíc).
- `opravit` – v datech je chyba, kterou jde opravit z toho, co už je stažené a přečtené.
- `overit_znovu` – údaj `doc` nesedí s výřezem, výřez chybí nebo je nečitelný: hlavní agent musí zápis znovu
  přečíst sám, než se pokračuje.
- `zmenit_postup` – čtenáři opakovaně chybují, kniha je pro ně nečitelná (kurent, nízké rozlišení), hledá se
  ve špatné knize nebo kolo nepřináší výsledky: změnit zadání, knihu, archiv nebo dělat čtení v hlavním chatu.
- `zeptat_se_uzivatele` – rozhodnutí patří člověku: rozpor s tím, co řekla rodina, výběr větve, soukromí
  žijících, dvě stejně pravděpodobné osoby. Otázky dej do `otazky_pro_uzivatele` (srozumitelně pro laika).
- `zastavit` – další práce by škodila: archiv blokuje (403, brzda hlásí zastavení), data jsou rozbitá tak, že
  `kontrola.py` padá a není jasné proč, nebo by pokračování stavělo na nepodloženém předkovi.

`dalsi_ukoly` seřaď podle priority (1 = nejdřív). `kdo`: `hlavni` (ověřit, opravit, zapsat), `ctenar` (hledat
a číst – zadání musí být přesné: kniha, snímky, koho hledat), `uzivatel` (otázka nebo rozhodnutí).
Odpověz jen JSON podle zadaného schématu.
"""


def sh(args, **kw):
    try:
        r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
        return r.returncode, r.stdout + r.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        return -1, str(e)


def arg(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 >= len(sys.argv):
            sys.exit(f"Chybí hodnota za {name}.\n\n{__doc__}")
        return sys.argv[i + 1]
    return None


def cislo_kola(d):
    m = re.search(r"kolo_(\d+)$", d.rstrip("/\\"))
    return int(m.group(1)) if m else -1


def najdi_kolo():
    k = arg("--kolo")
    if k is not None:
        if not k.isdigit():
            sys.exit(f"--kolo čeká číslo, ne „{k}“.")
        return int(k)
    kola = [cislo_kola(d) for d in glob.glob(os.path.join(PRACOVNI, "kolo_*")) if os.path.isdir(d)]
    kola = [k for k in kola if k >= 0]
    return max(kola) if kola else 0


def git():
    return shutil.which("git") and sh(["git", "rev-parse", "--is-inside-work-tree"])[0] == 0


def posledni_commit():
    """Revize z posledního úspěšného auditu (pole „commit“ v pracovni/audit/kolo_*.json)."""
    nej, cas = None, 0
    for p in glob.glob(os.path.join(AUDIT, "kolo_*.json")):
        try:
            v = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if v.get("commit") and os.path.getmtime(p) > cas:
            nej, cas = v["commit"], os.path.getmtime(p)
    return nej


def hlaseni(kolo):
    """Soubory kola: pracovni/kolo_<N>/ a složky pomocníků pom_* zmíněné v plánu (bez plánu všechny pom_*)."""
    kdir = os.path.join(PRACOVNI, f"kolo_{kolo}")
    plan = os.path.join(kdir, "plan.md")
    pom = None
    if os.path.isfile(plan):
        pom = set(re.findall(r"pom_[\w.-]+", open(plan, encoding="utf-8", errors="replace").read()))
    dirs = [kdir] + [d for d in sorted(glob.glob(os.path.join(PRACOVNI, "pom_*")))
                     if os.path.isdir(d) and (pom is None or os.path.basename(d) in pom)]
    out = []
    for d in dirs:
        for base, _, files in os.walk(d):
            for f in sorted(files):
                if f.lower().endswith((".md", ".txt", ".json")):
                    out.append(os.path.relpath(os.path.join(base, f), ROOT).replace(os.sep, "/"))
    return out, os.path.isfile(plan)


def zkrat(text, n):
    return text if len(text) <= n else text[:n] + f"\n… (zkráceno, celkem {len(text)} znaků – zbytek si přečti sám)\n"


def sestav_zadani(kolo, od):
    casti = [ZADANI, f"\n## Kontext kola {kolo}\n"]
    soubory, ma_plan = hlaseni(kolo)
    if not ma_plan:
        casti.append(f"Plán kola (`pracovni/kolo_{kolo}/plan.md`) chybí – to je samo o sobě `riziko`.\n")
    if not os.path.isfile(os.path.join(PRACOVNI, f"kolo_{kolo}", "zprava.md")):
        casti.append(f"Zpráva hlavního agenta (`pracovni/kolo_{kolo}/zprava.md`) chybí – výsledky kola posuď"
                     " podle dat, hlášení a konce `data/research_log.md`.\n")
    casti.append("### Plán a hlášení čtenářů (přečti všechny)\n"
                 + ("\n".join(f"- `{s}`" for s in soubory) if soubory else "- žádná hlášení nenalezena") + "\n")
    kod, vystup = sh([sys.executable, "-I", os.path.join("tools", "kontrola.py")], timeout=300)
    casti.append(f"### Výstup `tools/kontrola.py` (návratový kód {kod})\n```\n{zkrat(vystup.strip(), MAX_KONTROLA)}\n```\n")
    if git():
        casti.append(f"### Změny od revize `{od}`\n")
        _, diff = sh(["git", "diff", "--stat", od, "--", "data", "vyrezy", "zdroje"])
        _, nove = sh(["git", "ls-files", "--others", "--exclude-standard", "--", "data", "vyrezy", "zdroje"])
        casti.append(f"```\n{diff.strip() or '(beze změn v evidovaných souborech)'}\n```\n")
        if nove.strip():
            casti.append("Nové (necommitnuté) soubory:\n" + "\n".join(f"- `{n}`" for n in nove.split()) + "\n")
        _, diff = sh(["git", "diff", "-U2", od, "--", "data"])
        casti.append(f"```diff\n{zkrat(diff, MAX_DIFF)}\n```\n")
        casti.append("Když jsou změny prázdné, projdi poslední zápisy v `data/research_log.md` a k nim patřící data.\n")
    else:
        casti.append("Projekt není v gitu: změny kola najdi podle konce `data/research_log.md` a hlášení výše.\n")
    return "".join(casti)


def shrnuti(v):
    print(f"Rozhodnutí auditora: {v['rozhodnuti']}\n  {v['oduvodneni']}")
    for z in ("chyba", "riziko", "poznamka"):
        n = [x for x in v["nalezy"] if x["zavaznost"] == z]
        if n:
            print(f"\n{z.upper()} ({len(n)}):")
            for x in n:
                print(f"  - [{x['kde']}] {x['problem']}\n      důkaz: {x['dukaz']}\n      návrh: {x['navrh']}")
    if v["jiny_pohled"]:
        print(f"\nJiný pohled:\n  {v['jiny_pohled']}")
    if v["hypotezy"]:
        print("\nHypotézy:")
        for h in v["hypotezy"]:
            print(f"  - {h['tvrzeni']}\n      proč: {h['proc']}\n      ověřit: {h['jak_overit']}")
    if v["kde_hledat"]:
        print("\nKde hledat:")
        for k in sorted(v["kde_hledat"], key=lambda k: k["priorita"]):
            print(f"  {k['priorita']}. {k['pramen']}: {k['co_tam_najit']} – {k['proc']}"
                  + (f"\n      {k['odkaz']}" if k["odkaz"] else ""))
    if v["dalsi_ukoly"]:
        print("\nDalší úkoly:")
        for u in sorted(v["dalsi_ukoly"], key=lambda u: u["priorita"]):
            print(f"  {u['priorita']}. ({u['kdo']}) {u['ukol']} – {u['proc']}")
    if v["otazky_pro_uzivatele"]:
        print("\nOtázky pro uživatele:")
        for q in v["otazky_pro_uzivatele"]:
            print(f"  - {q}")
    print(f"\nAuditor ověřil na výřezech: {', '.join(v['overeno']) or 'nic'}")


def platny(v):
    if not isinstance(v, dict) or v.get("rozhodnuti") not in ROZHODNUTI:
        return False
    return isinstance(v.get("jiny_pohled"), str) and all(isinstance(v.get(k), list) for k in (
        "nalezy", "hypotezy", "kde_hledat", "dalsi_ukoly", "otazky_pro_uzivatele", "overeno"))


def tokeny(vystup):
    """Spotřeba z výpisu Codexu („tokens used“ a číslo na dalším řádku); None, když ji nevypsal."""
    m = re.search(r"tokens used\s*\n?\s*([\d,.  ]+)", vystup)
    cislo = re.sub(r"\D", "", m.group(1)) if m else ""
    return int(cislo) if cislo else None


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return 0
    kolo = najdi_kolo()
    od = arg("--od") or posledni_commit() or "HEAD"
    if git() and sh(["git", "rev-parse", "--verify", "--quiet", od + "^{commit}"])[0] != 0:
        print(f"Revize {od} v gitu není (přepsaná historie?), beru HEAD.")
        od = "HEAD"
    if git() and sh(["git", "status", "--porcelain", "--", "data"])[1].strip():
        print("POZOR: data/ mají neuložené změny. Audit je uvidí, ale další audit (od uložené revize) je uvidí znovu –\n"
              "před auditem změny kola ulož (git add -A && git commit).")
    os.makedirs(AUDIT, exist_ok=True)
    zadani = sestav_zadani(kolo, od)
    p_zadani = os.path.join(AUDIT, f"kolo_{kolo}_zadani.md")
    with open(p_zadani, "w", encoding="utf-8") as f:
        f.write(zadani)
    if "--jen-zadani" in sys.argv:
        print(f"Zadání auditu uloženo: {p_zadani}")
        return 0
    codex = shutil.which("codex")
    if not codex:
        print(f"Codex není nainstalovaný. Zadání auditu je v {p_zadani} – dej ho pomocníkovi s čistým kontextem\n"
              f"(jen čtení, bez sítě) a jeho JSON ulož do {os.path.join(AUDIT, f'kolo_{kolo}.json')}.")
        return 2
    tmp = tempfile.mkdtemp(prefix="audit_")
    try:
        schema, vystup = os.path.join(tmp, "schema.json"), os.path.join(tmp, "odpoved.json")
        with open(schema, "w", encoding="utf-8") as f:
            json.dump(SCHEMA, f)
        cmd = [codex] + ([] if "--bez-webu" in sys.argv else ["--search"]) + ["exec", "--sandbox", "read-only", "--ephemeral", "--skip-git-repo-check", "--color", "never",
               "-C", ROOT, "--output-schema", schema, "-o", vystup]
        if arg("--model"):
            cmd += ["-m", arg("--model")]
        print(f"Audit kola {kolo} (změny od {od}) běží v Codexu, může to trvat několik minut…", flush=True)
        try:
            r = subprocess.run(cmd + ["-"], input=zadani, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=3600)
        except subprocess.TimeoutExpired:
            print("Audit nedoběhl do hodiny – zkus menší kolo (--od novější revize).")
            return 1
        try:
            v = json.load(open(vystup, encoding="utf-8"))
        except (OSError, ValueError):
            v = None
        if r.returncode != 0 or not platny(v):
            log = os.path.join(AUDIT, f"kolo_{kolo}_chyba.log")
            with open(log, "w", encoding="utf-8") as f:
                f.write(r.stdout + "\n" + r.stderr)
            print(f"Codex skončil s kódem {r.returncode} a bez platné odpovědi. Výpis: {log}\n"
                  "Častá příčina: Codex není přihlášený (`codex login`).")
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    v["kolo"], v["od"], v["tokeny"] = kolo, od, tokeny(r.stdout + "\n" + r.stderr)
    v["cas"] = datetime.datetime.now().isoformat(timespec="seconds")
    v["commit"] = sh(["git", "rev-parse", "HEAD"])[1].strip() if git() else None
    out = os.path.join(AUDIT, f"kolo_{kolo}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
    shrnuti(v)
    print(f"\nUloženo: {out}" + (f" (Codex spotřeboval {v['tokeny']:,} tokenů)".replace(",", " ") if v["tokeny"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
