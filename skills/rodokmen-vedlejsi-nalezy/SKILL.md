---
name: rodokmen-vedlejsi-nalezy
description: Postup pro odkládání vedlejších nálezů při rodopisném výzkumu (příbuzná jména, sourozenci, povolání, úmrtí, další manželství, domy, svědci) a jejich pozdější zpětné spojování s rodokmenem. Použít při každém čtení matrik a při čištění odkladiště.
---

# Vedlejší nálezy: odkládat a spojovat zpětně

## Proč
Při hledání jednoho předka se na stejných stranách potká spousta jmen, která se hodí až ve vyšších generacích, u sourozenců, nebo při určování příbuzenství. Bez uložení se musí číst znovu.

## Kde se co ukládá
- `data/vedlejsi_nalezy.md` – odkladiště, po oddílech podle rodu a knihy: `- [kniha, snímek/strana, rok] osoba – údaj (jistota)`. Nic odtud není ověřeno jako příbuzenství.
- `RODINA` v `data/osoby.py` – sourozenci a děti předků, jejich partneři a další manželství předků (partner bez společného dítěte jako `partner=[…]`): kdy a kde se narodili, zemřeli (nebo „úmrtí nenalezeno“). Předky těchto osob nehledáme. Formát je v hlavičce `osoby.py` a v `reference/data.md` skillu rodokmen.
- `SIDE` v `data/osoby.py` – příbuzní s nejistým vztahem nebo celá větev jednou větou (nejde-li zapsat do `RODINA`).
- `data/research_log.md` – deník včetně neúspěšných hledání (kniha, snímky, roky, čitelnost).
- Domy podle čísel popisných: polohy dohledá skill **stare-adresy**, jeho `domy.geojson` patří do `data/domy/` (stránka Domy na webu, viz `reference/web.md` skillu rodokmen).

## Pravidla
1. Čtenář uvede vedlejší nálezy v každém hlášení. Hlavní chat je zapíše dřív, než zapíše hlavní nález.
2. Ke každému údaji patří zdroj (kniha, snímek) a jistota `(?)`.
3. Nikdy nepřepisovat vedlejší nález do `P` (osoby) bez ověření na snímku.

## Zpětné spojování (čistění)
- Po každém uzavřeném nálezu projít odkladiště podle příjmení a domu (čp.): co se shoduje s novým předkem, přesunout do `P`/`RODINA`/`SIDE` a v odkladišti označit „→ zapsáno“.
- Hledat stejné příjmení (i rodné) a stejný dům u předků z různých větví; každé takové shodě věnovat otázku „sourozenci, nebo sestřenice?“ a hledat společné rodiče.
- Nálezy pro vyšší generace nechat v odkladišti, dokud se nedokončí nižší (stav generací v `data/STAV.md`).
- Opakovaná jména a svědci (kmotři, svědci sňatku) často označují příbuzné; mezi nimi hledat nové předky.
