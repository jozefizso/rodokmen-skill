"""Test nezávislého auditu kola (tools/audit.py) a zavedení čtenáře do projektu (novy_projekt.py).

Codex napodobí falešný program `codex` v PATH: zapíše zadání a argumenty do souboru a vrátí pevnou odpověď –
do sítě nechodí a kredity nestojí.
Z kořene repozitáře:
  python3 -I tests/audit/test_audit.py skills/rodokmen
"""
import json, os, shutil, stat, subprocess, sys, tempfile

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:700]}", flush=True)


tmp = tempfile.mkdtemp(prefix="audit_")
proj = os.path.join(tmp, "projekt")
bin_ = os.path.join(tmp, "bin")
os.makedirs(bin_)
zaznam = os.path.join(tmp, "codex_volani.json")

ODPOVED = {"rozhodnuti": "overit_znovu", "oduvodneni": "Rok křtu nesedí s výřezem.",
           "nalezy": [{"zavaznost": "chyba", "kde": "zaznamy.json: krest_jan_1890", "problem": "rok 1890 × 1896",
                       "dukaz": "vyrezy/krest_jan_1890.jpg, 2. řádek", "navrh": "přečíst znovu v plném rozlišení"}],
           "dalsi_ukoly": [{"priorita": 1, "kdo": "hlavni", "ukol": "ověřit křest Jana", "proc": "rok"}],
           "jiny_pohled": "Jan mohl přijít z vedlejší farnosti.",
           "hypotezy": [{"tvrzeni": "otec Jana je z Lhoty", "proc": "kmotři z Lhoty", "jak_overit": "křty Lhota 1860"}],
           "kde_hledat": [{"priorita": 1, "pramen": "SOA Zámrsk, matriky Lhota", "co_tam_najit": "křest otce",
                           "proc": "kmotři", "odkaz": ""}],
           "otazky_pro_uzivatele": [], "overeno": ["vyrezy/krest_jan_1890.jpg"]}

with open(os.path.join(bin_, "codex"), "w", encoding="utf-8") as f:
    f.write(f"""#!{sys.executable}
import json, sys
a = sys.argv[1:]
zadani = sys.stdin.read()
json.dump({{"argv": a, "zadani": zadani}}, open({zaznam!r}, "w", encoding="utf-8"), ensure_ascii=False)
if "SPATNE" in open({os.path.join(tmp, "rezim")!r}).read():
    sys.exit(3)
json.dump({ODPOVED!r}, open(a[a.index("-o") + 1], "w", encoding="utf-8"), ensure_ascii=False)
print("tokens used", file=sys.stderr)
print("48,213", file=sys.stderr)
""")
os.chmod(os.path.join(bin_, "codex"), 0o755)
open(os.path.join(tmp, "rezim"), "w").write("DOBRE")


def run(*args, codex=True):
    path = (bin_ + os.pathsep if codex else "") + os.pathsep.join(
        p for p in os.environ["PATH"].split(os.pathsep) if not os.path.exists(os.path.join(p, "codex")))
    env = dict(os.environ, PATH=path)
    return subprocess.run([sys.executable, "-I", os.path.join(proj, "tools", "audit.py"), *args], cwd=proj, env=env,
                          capture_output=True, text=True, encoding="utf-8")


try:
    r = subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "novy_projekt.py"), proj, "--ukazka"],
                       capture_output=True, text=True, encoding="utf-8")
    check("novy_projekt.py doběhl", r.returncode == 0, r.stdout + r.stderr)
    agent = os.path.join(proj, ".claude", "agents", "rodokmen-ctenar.md")
    check("čtenář je v .claude/agents", os.path.isfile(agent))
    hlavicka = open(agent, encoding="utf-8").read().split("---")[1] if os.path.isfile(agent) else ""
    check("čtenář běží na Sonnetu a jmenuje se rodokmen-ctenar",
          "model: sonnet" in hlavicka and "name: rodokmen-ctenar" in hlavicka, hlavicka)
    check("audit.py je v tools/ projektu", os.path.isfile(os.path.join(proj, "tools", "audit.py")))

    for c in (["git", "init", "-q"], ["git", "add", "-A"],
              ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "zalozeni"]):
        subprocess.run(c, cwd=proj, check=True)
    os.makedirs(os.path.join(proj, "pracovni", "kolo_2"))
    os.makedirs(os.path.join(proj, "pracovni", "pom_krest"))
    os.makedirs(os.path.join(proj, "pracovni", "pom_jiny"))
    open(os.path.join(proj, "pracovni", "kolo_2", "plan.md"), "w", encoding="utf-8").write("- pom_krest: křest Jana\n")
    open(os.path.join(proj, "pracovni", "pom_krest", "hlaseni.md"), "w", encoding="utf-8").write("# krest\n")
    open(os.path.join(proj, "pracovni", "pom_jiny", "hlaseni.md"), "w", encoding="utf-8").write("# jiny\n")
    with open(os.path.join(proj, "data", "research_log.md"), "a", encoding="utf-8") as f:
        f.write("\n- ZMENA_KOLA_2: nalezen křest\n")

    r = run()
    check("audit doběhl", r.returncode == 0, r.stdout + r.stderr)
    volani = json.load(open(zaznam, encoding="utf-8"))
    a, z = volani["argv"], volani["zadani"]
    check("Codex jen pro čtení a bez ukládání relace",
          a[:2] == ["--search", "exec"] and a[a.index("--sandbox") + 1] == "read-only" and "--ephemeral" in a, a)
    check("Codex dostal schéma výstupu (po auditu uklizené)",
          "--output-schema" in a and not os.path.isfile(a[a.index("--output-schema") + 1]), a)
    check("zadání chce jiný pohled a kde hledat", "Pohled z jiné strany" in z and "kde_hledat" in z
          and "Nenech se ukotvit" in z)
    check("chybějící zpráva kola se v zadání ohlásí", "zprava.md`) chybí" in z)
    check("vybráno poslední kolo a jeho hlášení", "kolo_2/plan.md" in z and "pom_krest/hlaseni.md" in z, z[-3000:])
    check("hlášení mimo plán kola se nepřidá", "pom_jiny" not in z)
    check("zadání obsahuje diff dat", "ZMENA_KOLA_2" in z)
    check("zadání obsahuje výstup kontroly", "tools/kontrola.py" in z and "návratový kód" in z)
    check("varování na neuložené změny", "neuložené změny" in r.stdout, r.stdout)
    out = os.path.join(proj, "pracovni", "audit", "kolo_2.json")
    v = json.load(open(out, encoding="utf-8")) if os.path.isfile(out) else {}
    check("výsledek uložen s revizí", v.get("rozhodnuti") == "overit_znovu" and v.get("kolo") == 2
          and len(v.get("commit") or "") == 40, v)
    check("shrnutí vypisuje rozhodnutí a chybu", "overit_znovu" in r.stdout and "CHYBA (1)" in r.stdout, r.stdout)
    check("shrnutí vypisuje jiný pohled, hypotézy a kde hledat", "Jiný pohled" in r.stdout
          and "otec Jana je z Lhoty" in r.stdout and "SOA Zámrsk" in r.stdout, r.stdout)
    check("spotřeba tokenů uložena", v.get("tokeny") == 48213 and "48 213" in r.stdout, (v.get("tokeny"), r.stdout[-200:]))

    subprocess.run(["git", "add", "-A"], cwd=proj, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "kolo 2"], cwd=proj, check=True)
    open(os.path.join(proj, "pracovni", "kolo_2", "zprava.md"), "w", encoding="utf-8").write("# Kolo 2\n")
    r = run("--kolo", "2", "--bez-webu")
    volani = json.load(open(zaznam, encoding="utf-8"))
    z = volani["zadani"]
    check("--bez-webu vypne vyhledávání a zpráva kola je v zadání",
          "--search" not in volani["argv"] and "kolo_2/zprava.md" in z and "zprava.md`) chybí" not in z, volani["argv"])
    check("další audit začíná od revize minulého auditu", r.returncode == 0 and v.get("commit", "")[:7] in z
          and "ZMENA_KOLA_2" in z, r.stdout[-500:])

    open(os.path.join(tmp, "rezim"), "w").write("SPATNE")
    r = run("--kolo", "2")
    check("chyba Codexu → kód 1 a log", r.returncode == 1
          and os.path.isfile(os.path.join(proj, "pracovni", "audit", "kolo_2_chyba.log")), r.stdout)

    r = run("--kolo", "2", codex=False)
    check("bez Codexu kód 2 a uložené zadání", r.returncode == 2
          and os.path.isfile(os.path.join(proj, "pracovni", "audit", "kolo_2_zadani.md")), r.stdout)
    r = run("--jen-zadani", "--kolo", "7")
    check("--jen-zadani bez plánu hlásí chybějící plán", r.returncode == 0 and "Plán kola" in open(
        os.path.join(proj, "pracovni", "audit", "kolo_7_zadani.md"), encoding="utf-8").read(), r.stdout)
    r = run("--kolo", "x")
    check("--kolo s nečíslem skončí srozumitelně", r.returncode != 0 and "čeká číslo" in r.stderr, r.stderr)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(vysledky)}/{len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
