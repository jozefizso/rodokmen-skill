#!/usr/bin/env python3
"""Rychlá kontrola, že síťové nástroje a portály pořád fungují (spouští se ručně, třeba jednou za čas nebo když nástroj selže).

Použití (z kořene projektu):
  smoke_test.py                  -> vyzkouší všechny nástroje jedním bezpečným dotazem (hledání, žádné stahování snímků)
  smoke_test.py mza arolsen      -> jen vybrané (názvy viz `--seznam`)
  smoke_test.py --seznam         -> vypíše názvy a dotazy bez spuštění
Výstup: OK | CHYBA | NEDOSTUPNÉ (portál neodpovídá – síť, výpadek, blokace; nepovažuje se za chybu nástroje) | PŘESKOČENO.
CHYBA znamená, že portál odpověděl, ale nástroj nenašel očekávaný obsah – portál se nejspíš změnil a návod v `portaly.md` je třeba
ověřit a opravit. Návratový kód je 1 jen při CHYBĚ. Mezi dotazy jsou pauzy; nástroj `litomerice` dělá několik požadavků na stránky
portálu, který po ~100 rychlých požadavcích blokuje – nespouštěj test v rychlém sledu.
"""
import os, shutil, subprocess, sys, time
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PY = [sys.executable, "-I", "-X", "utf8"]

# (název, [nástroj, argumenty…], očekávaný text ve výstupu, „volitelné“ = NEDOSTUPNÉ i při jiné chybě sítě je v pořádku)
TESTY = [
    ("aron", ["aron_search.py", "Holice"], "count", False),
    ("trebon", ["trebon.py", "misto", "Tábor"], "Tábor", False),
    ("portafontium", ["portafontium.py", "fara", "Dolní Bělá"], "dolni-bela", False),
    ("ebadatelna", ["ebadatelna.py", "hledat", "Kladno"], "Kladno", False),
    ("ahmp", ["@bash", "ahmp_search.sh", "Smíchov"], "Smíchov", False),
    ("prihlasky", ["policie_prihlasky.py", "Novak", "Jan"], "záznamů", False),
    ("kramerius", ["kramerius.py", 'text_ocr:"Jan Novák" AND datum_begin:[1900 TO 1905]', "3"], "found", False),
    ("anno", ["anno.py", '"Johann Nowak"', "1880", "1890", "1"], "", True),
    ("mza", ["mza.py", "hledat", "Hustopeče", "--stran", "1"], "Hustop", False),
    ("vademecum", ["vademecum.py", "hledat", "Hustopeče", "--stran", "1", "--jen-snimky"], "matrik", False),
    ("litomerice", ["litomerice.py", "hledat", "Lovosice", "--stran", "1"], "|", False),
    ("brno", ["brno_encyklopedie.py", "hledat", "Bakala dirigent"], "Bakala", False),
    ("obeti", ["obeti.py", "hledat", "--prijmeni", "Neumannová", "--jmeno", "Anna", "--stran", "1"], "Neumann", False),
    ("vezni", ["vezni.py", "hledat", "--prijmeni", "Novák", "--jmeno", "Josef", "--stran", "1"], "Josef", False),
    ("arolsen", ["arolsen.py", "hledat", "Novák Josef 1905", "--max", "3"], "|", False),
    ("mauthausen", ["mauthausen.py", "hledat", "Novak", "--stran", "1"], "Novak", False),
    ("matricula", ["matricula.py", "oblasti"], "oesterreich", False),
]
SIT = ("urlopen error", "timed out", "Connection", "connection", "Name or service", "Temporary failure", "CERTIFICATE", "HTTP Error 403",
       "HTTP Error 5", "HTTP Error 429", "Max retries", "remote end closed", "RemoteDisconnected", "Errno 104", "Errno 111", "gaierror",
       "Server Exception", "blokac")


def spust(nazev, prikaz, ocek, volitelne):
    if prikaz[0] == "@bash":
        if not shutil.which("bash"):
            return "PŘESKOČENO", "bash není k dispozici"
        cmd = ["bash", os.path.join(HERE, prikaz[1]), *prikaz[2:]]
    else:
        cmd = [*PY, os.path.join(HERE, prikaz[0]), *prikaz[1:]]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=150, cwd=os.path.dirname(HERE))
    except subprocess.TimeoutExpired:
        return "NEDOSTUPNÉ", "časový limit 150 s"
    vystup = (r.stdout or "") + "\n" + (r.stderr or "")
    dt = f"{time.time() - t0:.0f} s"
    if r.returncode == 0 and ocek in (r.stdout or ""):
        return "OK", dt
    if any(s in vystup for s in SIT) or volitelne:
        return "NEDOSTUPNÉ", (vystup.strip().splitlines() or ["bez výstupu"])[-1][:140]
    return "CHYBA", f"{dt}; očekáváno „{ocek}“; poslední řádek: " + (vystup.strip().splitlines() or ["bez výstupu"])[-1][:160]


def main():
    a = sys.argv[1:]
    if "--seznam" in a:
        for n, p, o, v in TESTY:
            print(f"{n:14} {' '.join(p)[:100]}")
        return 0
    vyber = [t for t in TESTY if not a or t[0] in a]
    nezname = [x for x in a if x not in {t[0] for t in TESTY}]
    if nezname:
        sys.exit("Neznámé nástroje: " + ", ".join(nezname) + " (viz --seznam)")
    chyby = 0
    for i, (n, p, o, v) in enumerate(vyber):
        stav, popis = spust(n, p, o, v)
        chyby += stav == "CHYBA"
        print(f"{stav:11} {n:14} {popis}", flush=True)
        if i < len(vyber) - 1:
            time.sleep(1.5)   # pauza mezi portály
    print(f"\nHotovo: {len(vyber)} nástrojů, chyb {chyby}.")
    return 1 if chyby else 0


if __name__ == "__main__":
    sys.exit(main())
