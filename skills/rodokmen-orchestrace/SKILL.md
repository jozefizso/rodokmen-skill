---
name: rodokmen-orchestrace
description: Jak vést rodopisný výzkum po kolech s čtenáři na levnějším modelu (Sonnet) a nezávislým auditem v Codexu (ARON, SOA, Acta Publica) – plán kola, rozdělení práce, limity stahování, ověřování zápisů, audit a rozhodnutí, jak dál, vedlejší nálezy a postup po generacích. Použít, kdykoli se hledá víc předků paralelně nebo se zadává práce pomocným agentům.
---

# Rodopis: orchestrace čtenářů

## Role
- **Hlavní chat** plánuje, zapisuje do `data/`, ověřuje klíčové údaje na snímku a mluví s uživatelem. Čtenář (Sonnet) čte rukopis a hlásí; Haiku se na rukopis nepoužívá.
- **Auditor (Codex)** po každém kole nezávisle zkontroluje zápisy proti výřezům a hlášením, přinese pohled
  z jiné strany (jiné výklady, kde hledat) a rozhodne, jak dál. Nic nemění; opravy a zápis dělá hlavní chat.
- **Čtenář nikdy nepíše do `data/`**, ukládá jen do `pracovni/pom_<kód>/`. Každý nález (datum, čp., rodiče, kmotři) musí hlavní chat ověřit na vlastním výřezu, než ho zapíše jako `doc`.

## Kolo výzkumu: plán → čtenáři → ověření → audit → rozhodnutí
Práce jde po kolech. Hlavní chat (dražší model) kolo řídí, čtení dělají čtenáři na levnějším modelu a na konci
kolo zkontroluje nezávislý auditor (Codex, jiná rodina modelů). Kolo = 2–4 úkoly, jedna generace nebo větev.

1. **Plán** – `pracovni/kolo_<N>/plan.md`: cíl kola (generace, větve), úkoly s kódem čtenáře (`pom_<kód>`), knihou,
   snímky a koho hledat, a úkoly z minulého auditu (`pracovni/audit/kolo_<N-1>.json`, `dalsi_ukoly`), které
   kolo přebírá. Před prvním velkým kolem plán uživateli řekni a nech schválit (kredity).
2. **Čtenáři** – každý úkol jeden pomocník, paralelně nejvýš 4, na jeden archiv nejvýš jeden.
   - Claude Code: pomocník `rodokmen-ctenar` (`.claude/agents/rodokmen-ctenar.md` v projektu, běží na Sonnetu).
     Projekt bez něj (starší verze) ho dostane aktualizací projektu (`novy_projekt.py` na stejnou složku).
   - Codex, Cursor, OMP: pomocník na levnějším modelu podle pravidel prostředí; jako zadání mu dej obsah
     `.claude/agents/rodokmen-ctenar.md` (bez hlavičky) a úkol z plánu.
   - Zadání podle oddílu „Zadání čtenáři“ níže. Čtenář odevzdá `pracovni/pom_<kód>/hlaseni.md`.
3. **Ověření a zápis** – hlavní chat přečte každý nález na vlastním výřezu (`tools/overit.py`) a teprve pak ho zapíše
   (pořadí v oddílu „Zápis nálezu“). Co neověřil, nezapisuje jako `doc`. `kontrola.py` musí projít.
   Změny kola **ulož do gitu před auditem** (`git add -A && git commit -m "Kolo <N>: …"`), ať další audit
   kontroluje jen nové změny.
   Napiš **zprávu kola** `pracovni/kolo_<N>/zprava.md` – stejnou, jakou bys dal uživateli: koho jsi hledal, co se
   našlo a v jakých knihách, co ne (rozsah), čím si nejsi jistý, jak si vykládáš souvislosti a co plánuješ dál.
   Piš ji pro nezávislého čtenáře, který projekt nezná (jména, roky, obce, farnosti, archivy).
4. **Nezávislý pohled (audit)** – `python3 -I tools/audit.py --kolo <N>`. Codex (jiná rodina modelů) dělá dvě věci:
   (A) ověří zápisy proti výřezům a hlášením čtenářů, (B) podívá se na výsledky z jiné strany – jiné výklady,
   co se přehlíží, kde ještě hledat (smí použít webové vyhledávání, ne stahování z archivů). Nejdřív si udělá
   vlastní obraz z dat a výřezů, tvou zprávu čte až potom. Příkazy běží jen pro čtení a bez sítě. Výsledek je
   v `pracovni/audit/kolo_<N>.json`, trvá několik minut (pusť ho na pozadí). Tím odpadá ruční kopírování zpráv
   do ChatGPT; když to uživatel dělal, řekni mu, že teď to proběhne samo po každém kole. Bez Codexu (kód 2): `--jen-zadani` a zadání dej pomocníkovi s čistým kontextem – v Claude
   Code obecnému pomocníkovi na hlavním modelu, jen čtení, ne `rodokmen-ctenar` (čtenář nesmí kontrolovat sám sebe);
   v Codexu jako hlavním chatu je audit z Codexu méně nezávislý, řekni to uživateli.
5. **Rozhodnutí** – podle pole `rozhodnuti`:
   - `pokracovat` → další kolo; úkoly auditora zařaď do plánu.
   - `opravit` → nejdřív oprav všechny nálezy `chyba`, `kontrola.py`, ulož; pak další kolo.
   - `overit_znovu` → dotčené zápisy přečti znovu sám na výřezu v plném rozlišení; do té doby z nich nestav další
     generaci (jejich rodiče nehledej).
   - `zmenit_postup` → změň zadání (přesné snímky, výřez sloupce), knihu nebo archiv; nečitelnou knihu čti sám.
   - `zeptat_se_uzivatele` → otázky polož uživateli srozumitelně a čekej na odpověď.
   - `zastavit` → skonči, řekni uživateli proč a co dál (archiv blokuje, rozbitá data).
   Auditor rozhoduje, ale nepřebíjí pravidla skillu: brzdu, soukromí a souhlas uživatele s velkým kolem.
   **Jiný pohled ber vážně, i když nesouhlasíš:**
   - `hypotezy` – každou buď vyvrať doloženým zápisem (napiš kterým), nebo ji zapiš: k jedné osobě do `ISSUES`
     („Hypotéza: …“, „Otevřené: …“), o původu rodu do `HYPOTEZY` v `data/osoby.py`. Hypotéza není `doc`.
   - `kde_hledat` – prameny zařaď do plánu dalšího kola podle priority; co je jen v archivu na místě, do
     `data/archivni_dotazy.md`. Nový portál nebo archiv bez nástroje ve skillu → `poznamky_pro_skill.md`.
   - Uživateli po každém kole krátce řekni, co nezávislý pohled přinesl (`jiny_pohled`, nejzajímavější hypotéza
     a kam se podíváš), a odliš to od toho, co je doložené.
   **S nálezem nesouhlasíš?** Ověř to znovu na výřezu a do `data/research_log.md` zapiš „Audit kola N: …,
   ověřeno na <výřez> – ponecháno, protože …“. Když se rozpor týká údaje `doc` nebo se opakuje, rozhodne uživatel.
6. **Zápis kola** – do `data/research_log.md` krátce: co se našlo, rozhodnutí auditu a co se s ním udělalo;
   „Rozpracováno“ v `data/STAV.md`.

Bez uživatele nejvýš 3 kola za sebou, pak mu shrň výsledky (noví předci, opravy po auditu, co dál) a zeptej se,
jestli pokračovat. Uživateli vysvětli, proč to tak je: čtenáři jsou levnější, hlavní model ověřuje a nezávislý
auditor z jiné rodiny modelů chytí chyby, které by oba přehlédli stejně, a přinese jiný pohled a jiné znalosti
pramenů. Audit Codexu přihlášeného přes ChatGPT čerpá z limitů ChatGPT plánu, ne z kreditů Claude; spotřebu tokenů
vypíše a uloží (`tokeny`). Kdyby byl drahý, stačí audit každé druhé kolo nebo jen po kole s novými `doc` údaji.

## Zadání čtenáři (vždy)
1. Jeden úkol, přesné jméno, rok, čp., apu knihy a kalibrace snímků z dřívějška.
2. „Jedno stahování najednou, nespouštěj duplicity; nejdřív se podívej, jestli snímek už není v `pracovni/<svazek>/`
   nebo v mezipaměti (`python3 -I tools/cache.py najdi <adresa>`).“
3. „Vypiš i vedlejší nálezy: sourozence, děti, povolání, úmrtí, další manželství, kmotry, svědky, příbuzná jména, kde a kdy.“
4. „U negativního výsledku přesně uveď knihu, snímky, roky a čitelnost.“
5. „Rejstřík čti po sloupcích (`python3 -I tools/mapa_knihy.py … --sloupce`, `reference/matriky.md` → Čtení písma).
   Bez toho „v rejstříku není“ nehlas jako negativní výsledek.“

## Limity serverů
- ARON vydrží asi 6–8 souběžných stahování celkem. Víc (20–40 procesů) ho zahltí a snímek pak trvá desítky minut. Stav ověř přes brzdu: `python3 -I tools/slusne.py stav` a `python3 -I tools/smoke_test.py aron`; běžící stahování podle procesů `aron_img`.
- ZA Opava a SOA Praha (eBadatelna) pouštějí jen prohlížeč tempem člověka; ZA Opava asi 50 snímků denně. Čtenáři je dávej jen s výslovně povoleným prohlížečem a s limitem v zadání (`reference/portaly.md`).
- Acta Publica (MZA Brno) nelze stahovat přes curl (HTTP 426). Čte se jen v prohlížeči; hromadné stahování dlaždic skriptem je považováno za obcházení ochrany – nedělat.

## Zápis nálezu (pořadí)
výřez `vyrez.py` → rámeček `ramecek.py` → JSON záznamu a přepisu → `zapis.py` → osoby v `osoby.py` (i prarodiče jako nové Kekulé čísla) → `kontrola.py` → `npm run data` → deník (`research_log.md`) a vedlejší nálezy (`vedlejsi_nalezy.md`).
Nová kniha = nový záznam `svazky.json` (jinak kontrola selže).

## Postup po generacích
- Nejdřív dokončit generaci, pak další (stav generací veď v `data/STAV.md`, „Rozpracováno“); co se najde navíc, uložit
  do odkladiště `data/vedlejsi_nalezy.md`.
- Větve, které uživatel označí jako prioritní, jdou nejhlouběji; ostatní se dotahují do stejné generace.
- Sourozence, děti a další manželství předka zapiš do `RODINA` v `data/osoby.py` (partner bez společného dítěte jako
  `partner=[…]`), nejistý vztah jen jako poznámku do `SIDE`. Jejich předky nehledáme.

## Kvalita čtení (měřeno na vlastních ověřených zápisech)
- **Plné rozlišení (úroveň 0, výřez jednoho zápisu)** čte český rukopis téměř bez chyb. **Poloviční rozlišení u kurentu je téměř nečitelné** (jména nahrazená „?“), hodí se jen na orientaci v knize.
- Německé formuláře (např. Vídeň) mají víc chyb: **roky, stav (ledig × vdovec), povolání, adresy a jména svědků.** Právě tyhle údaje vždy ověř na výřezu, než je zapíšeš jako `doc`. Příznak jistoty od čtenáře na to nestačí – čtenář u chybného roku napsal „střední“.
- Do databáze ani do dat neukládej „?“ jako hodnotu; nejisté pole vynech a popiš v poznámce.
- Přepis celé strany místo jedné vybrané řádky stál při měření jen asi o desetinu tokenů víc (obrázek se platí tak jako tak); užitečné je ukládat i zápisy cizích rodin, které čtenář stejně přečetl pořádně.

## Chyby, které se opakovaly
- Haiku četl špatně čísla a roky.
- Duplicitní stahování zahltila server.
- Negativní výsledek bez rozsahu zavádí.
- Kniha s „chybějícími čísly“ nemusí mít chybějící strany: čísla zápisů jsou společná pro celou farnost, obce mají vlastní knihy.
