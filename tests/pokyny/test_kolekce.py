"""Pokyny pro agenty smí jmenovat jen ty sbírky dat (`RODINA`, `SIDE`…), které projekt opravdu má.

Kontroluje dvě věci:
1. Každá sbírka ze šablony `template/data/osoby.py` (přiřazení na nejvyšší úrovni, např. `RODINA = {`) je
   podporovaná exportem webu (`tools/export_web.py`) i kontrolou dat (`tools/kontrola.py`).
2. Každý název velkými písmeny v obrácených uvozovkách v pokynech (SKILL.md všech skillů, reference/,
   šablony CLAUDE.md/AGENTS.md, definice pomocníků a zadání auditu v tools/audit.py) je buď sbírka z bodu 1,
   nebo se vyskytuje v kódu skillu (nástroje, web) – například hláška `NOVA_VERZE_SKILLU`.
   Neexistující sbírka (dřív `MANZELSTVI` z doplňujícího skillu) tak neprojde.

Z kořene repozitáře:
  python3 -I tests/pokyny/test_kolekce.py skills/rodokmen
"""
import glob, os, re, sys

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
SKILLS = os.path.dirname(SKILL)
vysledky = []
OBECNE = {"PATH", "LOCALAPPDATA", "PYTHONUTF8", "UTF", "HTTP", "URL", "API", "JSON", "CSV", "PDF", "ZIP", "ID",
          "GEDCOM", "RTF", "NO_COLOR", "TODO"}   # běžné zkratky a proměnné prostředí, nejsou to sbírky dat


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:900]}", flush=True)


def cti(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


sablona = cti(os.path.join(SKILL, "template", "data", "osoby.py"))
sbirky = set(re.findall(r"^([A-Z][A-Z_]*)\s*=", sablona, re.M))
check("šablona osoby.py má sbírky", {"P", "RODINA", "SIDE"} <= sbirky, sorted(sbirky))

for nastroj in ("export_web.py", "kontrola.py"):
    kod = cti(os.path.join(SKILL, "tools", nastroj))
    chybi = sorted(s for s in sbirky if not re.search(rf"\b{s}\b", kod))
    check(f"{nastroj} zná všechny sbírky z osoby.py", not chybi, f"nezná: {chybi}")

# Kód, ve kterém se smí vyskytovat ostatní názvy (hlášky nástrojů, konstanty); audit.py je zadání, ne kód.
korpus = []
for vzor in ("tools/*.py", "tools/*.sh", "tools/*.js", "template/web/src/**/*", "template/web/scripts/*",
             "template/data/*", "template/web/*.js", "template/web/*.mjs"):
    for p in glob.glob(os.path.join(SKILL, vzor), recursive=True):
        if os.path.isfile(p) and not p.endswith("audit.py"):
            korpus.append(cti(p))
korpus = "\n".join(korpus)

pokyny = (glob.glob(os.path.join(SKILLS, "*", "SKILL.md")) + glob.glob(os.path.join(SKILL, "reference", "*.md"))
          + [os.path.join(SKILL, "template", n) for n in ("CLAUDE.md", "AGENTS.md")]
          + glob.glob(os.path.join(SKILL, "template", ".claude", "agents", "*.md"))
          + glob.glob(os.path.join(SKILL, "tools", "audit.py")))
nezname = []
for p in sorted(pokyny):
    if not os.path.isfile(p):
        continue
    for i, radek in enumerate(cti(p).splitlines(), 1):
        for obsah in re.findall(r"`([^`\n]+)`", radek):
            m = re.match(r"([A-Z][A-Z_]*)(?=$|[.\[\s(/=,])", obsah)
            if not m:
                continue
            nazev = m.group(1)
            if nazev in sbirky or nazev in OBECNE or len(nazev) == 1 or re.search(rf"\b{nazev}\b", korpus):
                continue
            nezname.append(f"{os.path.relpath(p, SKILLS)}:{i} `{nazev}`")
check("pokyny jmenují jen existující sbírky a názvy z kódu", not nezname, "\n  " + "\n  ".join(nezname))

print(f"\n{sum(vysledky)}/{len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
