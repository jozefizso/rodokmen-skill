# Portály archivů a jak z nich dostat snímky

Matriky jsou online u osmi státních archivů (a židovské ještě v Národním archivu) – podle toho, **kde předci žili** (dnešní kraje zhruba odpovídají):

| Archiv | Oblast | Portál s matrikami | Vyzkoušeno se skillem |
|---|---|---|---|
| SOA Zámrsk | východní Čechy (Hradecký a Pardubický kraj) | ARON – aron.vychodoceskearchivy.cz | **ano – hotové nástroje** |
| SOA Praha | střední Čechy | eBadatelna – ebadatelna.soapraha.cz | **jen v prohlížeči** – archiv nástroj od 2. 11. 2026 zakazuje (postup níže; i urbáře a gruntovní knihy) |
| SOA Plzeň | západní Čechy | Porta fontium – portafontium.eu | **ano – nástroj `portafontium.py`** |
| SOA Třeboň | jižní Čechy | digi.ceskearchivy.cz | **jen v prohlížeči** – archiv nástroj od 2. 11. 2026 odmítá (postup níže) |
| SOA Litoměřice | severní Čechy | Digitální badatelna – digi.soalitomerice.cz | **ano – nástroj `litomerice.py`** (limit portálu viz níže) |
| AHMP | hl. m. Praha | katalog.ahmp.cz (Pragapublica) | **ano – `ahmp_search.sh`, `ahmp_scan.py`** |
| MZA Brno | jižní Morava, Vysočina z části | Acta Publica – www.mza.cz/actapublica | **jen v prohlížeči** – snímek obrazovky přiblíženého zápisu; knihy hledá `mza.py hledat` (postup níže) |
| ZA Opava | severní Morava a Slezsko, Olomoucko a Litovelsko | Digitální badatelna – digi.archives.cz/da/ | **částečně – `soal_zoomify.py`** (jen s prohlížečem, CAPTCHU řeší uživatel) |
| Národní archiv | židovské matriky 1784–1949 (HBMa, HBM) | Archivní VadeMeCum – vademecum.nacr.cz | **ano – `vademecum.py`** |
| Národní archiv | pražské policejní přihlášky 1850–1914 | digi.nacr.cz/prihlasky2 | **ano – `policie_prihlasky.py`** |
| Památník Terezín | čeští vězni v táborech (Buchenwald, Dachau, Mauthausen, Flossenbürg…), Malá pevnost, ghetto | pamatnik-terezin.cz/databaze | **ano – `vezni.py`** |
| Arolsen Archives | vězni, oběti a nuceně nasazení, vysídlené osoby (DP) – desítky milionů jmen | collections.arolsen-archives.org | **ano – `arolsen.py`** |
| Archiv města Brna | Encyklopedie dějin města Brna (osobnosti, ulice, hroby) | encyklopedie.brna.cz | **ano – `brno_encyklopedie.py`** |
| Matricula Online | církevní matriky Rakouska (i Vídně), Německa, Polska, Srbska… | data.matricula-online.eu | **navigace ano – `matricula.py`**; obrázky v prohlížeči |
| Mauthausen Memorial | zemřelí v Mauthausenu a pobočkách | raumdernamen.mauthausen-memorial.org | **ano – `mauthausen.py`** |
| Terezínská iniciativa | oběti nacistické perzekuce (Židé z českých zemí) | holocaust.cz/databaze-obeti | **ano – `obeti.py`** |
| VHÚ / VÚA-VHA | vojáci 1. světové války (seznamy ztrát, vojenské matriky), válečné hroby | digitalnistudovna.mo.gov.cz, valecnehroby.army.cz | nevyzkoušeno (ze zkušebního prostředí nedostupné) |

Adresy u nevyzkoušených portálů ověř při prvním použití (portály se mění). Když nástroj selže, spusť `python3 -I tools/smoke_test.py`
(nebo jen `smoke_test.py <nástroj>`): jedním bezpečným dotazem ověří všechny síťové nástroje a řekne, jestli portál neodpovídá (NEDOSTUPNÉ),
nebo se změnil (CHYBA) – pak je třeba opravit nástroj i tento návod. Pro pohraničí a mimo ČR viz `playbook.md` §2
(Matricula pro Rakousko/Německo, Geneteka pro Polsko, FamilySearch pro Slovensko) a níže.

**Claude in Chrome – výstup JavaScriptu** (platí pro všechny portály):
- Výstup, který obsahuje adresu s parametry (`?`, `&`, `=`) nebo dlouhý hex, rozšíření zahodí jako
  „[BLOCKED: Cookie/query string data]“. Vracej jen cestu (`location.pathname`, `new URL(a.href).pathname`) a hodnoty
  parametrů zvlášť, případně znaky `?&=` nahraď mezerami; celou adresu slož až v shellu.
- Výstup se ořízne asi na 1000 znaků (u seznamů asi 30 řádků) – delší seznamy vypisuj po částech (`.slice(0, 25)`, …).
- Snímky obrazovky na těžkých stránkách padají na timeout; text čti přes `get_page_text` / `read_page` nebo
  `innerText`.

## ARON (SOA Zámrsk) – hotové nástroje
- **Hledání svazků:** `python3 -I tools/aron_search.py "Holice"` → řádky `apu_id | signatura, roky | druh, obce`.
  Popis obsahuje druh knihy (NAROZENÝCH / ODDANÝCH / ZEMŘELÝCH, index) a všechny obce farnosti.
- **Informace o svazku:** `python3 -I tools/aron_img.py <apu_id> info` → název a počet snímků.
- **Stažení snímku:** `python3 -I tools/aron_img.py <apu_id> <snímek> 1 pracovni/holice_n_57.jpg`
  (úroveň 1 = poloviční rozlišení – stačí na orientaci; 0 = plné rozlišení – na čtení a výřez).
  Jen část stránky v plném rozlišení: `… <snímek> 0 pracovni/detail.jpg 0.0,0.4,1.0,0.7`.
  Nástroj stáhne celý sken jedním požadavkem (jako tlačítko „stáhnout“ v ARONu) a zmenšení i výřez dělá z disku;
  další výřezy téže stránky už na archiv nejdou. Dlaždice (desítky pomalých požadavků) jen jako záloha.
- **Odkaz na snímek** (pole `odkaz` v `zaznamy.json`): `python3 -I tools/aron_img.py <apu_id> link <snímek>`.
  Odkazy z dřívějších verzí (id souboru PUBLISHED) otevřou knihu na prvním snímku – najde je
  `aron_img.py odkazy`, opraví `aron_img.py odkazy --opravit` (v `data/`, pak znovu `npm run data`).
- **Svazek do dat:** `python3 -I tools/aron_img.py <apu_id> svazek` (klíč = prvních 8 znaků apu_id → pole `svazek` v zápisu).
- V ARON jsou i další fondy (sčítání lidu, některé gruntovní knihy, kroniky) – `aron_search.py "Obec" "název fondu"`.
- Stejnojmenných obcí bývá víc (Vinice u Hořic × Vinice u Velké Jesenice). Výsledky jsou seřazené podle farnosti;
  zúžit jde víc slovy oddělenými čárkou, která musí být v popisu všechna: `aron_search.py "Vinice,Hořice"`
  (nebo hledej sousední obec či farní obec).
- U starých far hledej nejdřív **souhrnné indexy** (popis „index NAROZENÝCH…“ přes mnoho let), často sahají do 17. století.
- Obec nenalezena? Zkus název **bez přívlastku** („Lhota“ místo „Horní Lhota“) a starý název. Starší matriky
  (před ~1784) bývají ve faře sousedního města; indexy fary mají oddíly po vesnicích
  („Copulati Gross Lhota“).
- Ber ohled na server: stahuj jen to, co čteš; žádné hromadné stahování celých svazků.

## SOA Třeboň (digi.ceskearchivy.cz) – jen v prohlížeči
- **Od 2. 11. 2026 archiv nástroj odmítá** (HTTP 403 podle User-Agentu „rodokmen“), `trebon.py` je odstraněn a brzda
  skripty na digi.ceskearchivy.cz zastaví. Neobcházej to (jiný User-Agent, vlastní skript). Matriky čti v prohlížeči
  (nejlépe Playwright) stejně jako u MZA: přiblížit zápis, uložit snímek obrazovky, `vyrez.py`. Tempo 5–10 s mezi
  stránkami (SKILL.md, Šetrně k archivům), jen stránky, které čteš, žádní pomocníci. Bez prohlížeče ať pošle snímky
  obrazovky uživatel.
- Obec: `https://digi.ceskearchivy.cz/<Obec>` (bez diakritiky a mezer, např. `RatiborskeHory`) → stránka místa, vlevo
  „Matriční knihy“ (stránka je v rámci `ram_obsah`) → seznam knih s roky a obcemi; kliknutí otevře knihu v nové záložce.
  **Zkontroluj název a okres**: u stejnojmenných obcí portál vybere jinou (Buk → Bukovka), u měst i okres nebo synagogu.
  Malé osady portál nezná (Malá Chyška) – hledej farní nebo sousední obec a osadu v popisu knih.
- Snímek: `https://digi.ceskearchivy.cz/<kniha>/<snímek>` (zároveň trvalý odkaz). Knihy mívají dobrovolnický jmenný
  rejstřík (stránka místa → „Rejstříky“) – obrovská úspora; ne každá kniha ho má.
- **Každé zobrazení snímku stáhne všechny dlaždice znovu** – i šipka zpět na snímek, který byl právě na obrazovce
  (rám se načte znovu s novým tokenem, mezipaměť prohlížeče nepomůže). Na snímku proto vyřiď všechno najednou: přibliž
  a přečti všechny zápisy, které můžeš potřebovat, než přejdeš dál.
- Prohlížeč je Zoomify v rámci `ram_obsah`. Postup: snímek okna (scale css) → odečti rohy zápisu → úryvek níže
  (browser_evaluate) schová panely Navigátor a Náhledy, přiblíží zápis a vrátí odkaz `/<kniha>/<snímek>/<x>/<y>/<zoom>/0`
  přímo na zápis (do `odkaz`) → snímek okna v rozlišení zařízení do `pracovni/trebon_<kniha>_<snímek>.png` → `vyrez.py`
  (ořízni lištu nahoře a dole):
  ```js
  async () => {
    const [x0, y0, x1, y1] = [185, 688, 590, 795];   // rohy zápisu na snímku okna (CSS px)
    const f = document.querySelector('iframe[name=ram_obsah]'), d = f.contentDocument, vp = f.contentWindow.Z.Viewport;
    if (!d.getElementById('rodokmen-skryj')) d.head.insertAdjacentHTML('beforeend',
      '<style id="rodokmen-skryj">#navigat_b,#thumbs_b{display:none!important}</style>');
    const r = f.getBoundingClientRect(), z = vp.getZoom(), c = vp.calculateCurrentCenterCoordinates();
    const W = vp.getViewW(), H = vp.getViewH();
    const obr = (x, y) => ({x: (x - r.left - W / 2) / z + c.x, y: (y - r.top - H / 2) / z + c.y});
    const a = obr(x0, y0), b = obr(x1, y1);
    vp.zoomAndPanToView((a.x + b.x) / 2, (a.y + b.y) / 2, Math.min(W / (b.x - a.x), H / (b.y - a.y)));
    await new Promise(ok => setTimeout(ok, 6000));
    return location.href;
  }
  ```
  Souřadnice ber vždy z aktuálního snímku okna (po načtení stránky nebo `vp.reset()`), ne ze staršího.
- Svazek do `svazky.json` ručně (Ostatní portály, krok 4, klíč `trebon_<kniha>`).
- Některé fary mají knihy po vesnicích, které nejsou v seznamu knih místa (Vacov → Žár) – hledej podle titulků knih fary.
- **Civilní matriky (1920–1945) lidí bez vyznání** jsou v knihách okresních úřadů (např. Tábor, kniha 12304) a mají
  dobrovolnický rejstřík. Dobrá cesta, když farní matrika mlčí. U obce se neukážou (patří okresu) – hledej u okresního města.

## SOA Plzeň (Porta fontium, portafontium.eu) – `tools/portafontium.py`, bez prohlížeče
- **Obec → knihy:** `portafontium.py obec "<obec>"` → všechny knihy s obcí v popisu, seskupené podle fary a seřazené podle
  let (kniha | obce | roky a druhy: `*` N, `oo` O, `+` Z, `i` index | popis). Je z něj vidět i přechod obce mezi farami
  (Bučí: Dolní Bělá do 1795, Krašovice od 1787) a civilní matriky okresních úřadů. Portál hledá i historické a podobné
  názvy – stejnojmenné obce jiných far (Bučí × Buč u Komárova) vyřaď podle sloupce obcí. Nic nenalezeno? Zkus jiný tvar
  (Stajanovice × Stojanovice, německý název) nebo sousední obec.
- `portafontium.py fara <fara>` → všechny knihy fary ve stejném tvaru. `<fara>` je název („Dolní Bělá“, „Mýto“ –
  diakritiku nástroj odstraní) nebo část adresy fary (`dolni-bela`); stejnojmenné fary mají příponu okresu
  (`plana-ps`, `radnice-ro`) – správnou adresu ukáže `obec`.
- `portafontium.py info <kniha>` (`dolni-bela-17`) → signatura, druh, text desky a **obsah** – u knih psaných po vesnicích
  vypíše, na kterých foliích je která obec („Ves X z let 1862–1901 = fol. 121–200“).
- `portafontium.py snimek <kniha> <snímek> pracovni/x.jpg [nahled] [x0,y0,x1,y1]` → celá stránka v plném rozlišení jedním
  požadavkem (IIIF), `nahled` = 1/4. Číslo snímku = pořadí náhledu v prohlížeči; soubory nesou číslo folia
  (`dolni-bela-17_0951` = fol. 95), takže u knih se souvislou foliací je **snímek ≈ folio**.
  Odkaz z cizího rodokmenu (MyHeritage) s `…_0450` v adrese je proto folio 45, ne snímek – stáhni i sousední snímek.
- `link <kniha> <snímek>` → trvalý odkaz, `svazek <kniha>` → `svazky.json` (klíč `pf_<kniha>`).
- **Tempo:** portál žádá 10 s mezi dotazy (robots.txt „Crawl-delay: 10“) – brzda to drží sama, i u snímků.
- Zaniklé obce (Slavkovský les, Doupovsko, pohraničí): stejné jméno má často víc vsí (Schönlind = Krásná Lípa u Kraslic
  i zaniklá Krásná Lípa u Sokolova). Rozhodne sousední obec z rodinných údajů a fara: např. Schönlind ve Slavkovském lese
  → fara Kostelní Bříza (`kostelni-briza`), Perlsberg/Lazy a Rockendorf/Žitná → fara Smrkovec (`smrkovec`). Svatby hledej
  i ve faře nevěsty (sousední fara), oddací rejstříky jsou v knihách `…ooi`.
- Bez prohlížečového User-Agentu portál vrací 403 (nástroj ho posílá). Jmenné hledání portál nemá – indexy jsou jen uvnitř knih
  (`*i`, `ooi`, `+i` v seznamu knih fary).

## SOA Praha (eBadatelna, ebadatelna.soapraha.cz) – jen v prohlížeči
- **Od 2. 11. 2026 archiv nástroj zakazuje** (robots.txt „User-agent: rodokmen – Disallow: /“, HTTP 403),
  `ebadatelna.py` stahovat nesmí (fungují `link`, `a-link` a `snimek` ze snímků uložených z prohlížeče) a brzda
  skripty na soapraha.cz zastaví. Neobcházej to (jiný User-Agent, vlastní skript, fetch). Matriky čti v prohlížeči
  (nejlépe Playwright).
  Tempo 5–10 s mezi stránkami (SKILL.md, Šetrně k archivům), jen stránky, které čteš, žádní pomocníci. Bez prohlížeče
  ať pošle snímky obrazovky uživatel.
- Hledání: Matriky → pole „lokalita“ vyplň obcí bez posledního písmene (`browser_type`) a poslední písmeno napiš
  se `slowly` (teprve to ukáže našeptávač; psaní po písmenech do prázdného pole se připojí k textu „lokalita“). Vyber
  celý název (`.ui-menu-item`, „Obec - obec X - okres Y“), Vyhledat. Seznam knih jedním `browser_evaluate`:
  `[...document.querySelectorAll('table tr')].map(r => [...r.cells].map(c => c.innerText.trim()).join(' | ') + ' | ' + (r.querySelector('a')?.getAttribute('href') ?? ''))`
  (kniha | původce | okres | lokality | roky N, O, Z, indexy | snímků | `/pages/MatrikaPage/matrikaId/<id>`).
- Popis knihy: `https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/<id>` (archiválie
  `…/pages/ArchivaliePage/archivalieId/<id>`) – `document.body.innerText`. „Obecný popis matriky“ uvádí u knih psaných
  po vsích **rozvržení stran** („1–48 Ves A, 49–82 Ves B …“, každá ves může mít vlastní stránkování) – neodhaduj snímek
  podle roku, ale podle stran vsi; je-li rejstřík, začni jím.
  Archiv popis ořezává asi na 250 znaků (konec rozvržení chybí) – úplný seznam vsí je v poli Lokality, zbytek viz
  `matriky.md` (Knihy řazené po vsích).
- Snímek: `https://ebadatelna.soapraha.cz/d/<matrikaId>/<snímek>` (archiválie `/a/<archivalieId>/<snímek>`, zároveň
  trvalý odkaz, do `odkaz`; šipky „<“ a „>“ v prohlížeči na tuto adresu taky přejdou). Prohlížeč načte celý snímek
  v plném rozlišení. **Ulož ho jednou do mezipaměti a dál pracuj z disku** – archiv už nedostane žádný další dotaz.
  Při listování ulož každý zobrazený snímek hned (uložení archiv nic nestojí) a před dalším krokem se podívej, jestli
  další snímek už nemáš – pak ho čti z disku a v prohlížeči přejdi rovnou na adresu toho, který ještě nemáš:
  1. Už ho máš? `python3 -I tools/cache.py najdi <adresa snímku> --nahled pracovni/nahled.jpg` – vypíše cestu
     a udělá náhled (1600 px), pak prohlížeč neotevírej.
  2. Jinak otevři adresu, počkej na načtení (pár s) a ulož ho (`browser_evaluate` s `filename: "pracovni/ebad.json"`):
     ```js
     () => {
       const im = document.getElementById('scanImage');
       if (!im || !im.complete || !im.naturalWidth) return 'snímek se ještě načítá – zkus to za chvíli';
       const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight;
       c.getContext('2d').drawImage(im, 0, 0);
       return JSON.stringify({w: c.width, h: c.height, adresa: location.origin + new URL(im.src).pathname.split(';')[0],
                              data: c.toDataURL('image/jpeg', 0.92)});
     }
     ```
     a `python3 -I tools/cache.py uloz pracovni/ebad.json --nahled pracovni/nahled.jpg` (uloží snímek, udělá náhled
     1600 px ke čtení stránky a soubor .json smaže).
  3. Jiný náhled nebo výřez z uloženého snímku bez sítě: `python3 -I tools/ebadatelna.py snimek <matrikaId> <snímek>
     pracovni/x.jpg [nahled] [x0,y0,x1,y1]` (archiválie `a-snimek`), dál `vyrez.py` jako u jiných archivů.
  Bez Playwrightu (Claude in Chrome neumí výsledek uložit do souboru) ať snímek uloží uživatel (snímek obrazovky).
- Starší snímky bývají z mikrofilmu nebo silně vybledlé – výřez dělej s `--kontrast` (`vyrez.py`, `overit.py`;
  viz `matriky.md`, Čtení písma) a poznamenej to v přepisu.
- Svazek do `svazky.json` ručně (Ostatní portály, krok 4, klíč `ebad_<matrikaId>`, archiválie `ebad_a_<id>`).
  Denní údržba portálu kolem 4:44 (asi 2 minuty); večer a v noci bývá nedostupná (zhruba 22:45–0:45 a kolem 2:00).

## AHMP Praha – `tools/ahmp_search.sh`, `tools/ahmp_scan.py`
- `bash tools/ahmp_search.sh "Smíchov"` → svazky Sbírky matrik: popis | farnost | (XID, id, počet snímků).
- `python3 -I tools/ahmp_scan.py <XID> <snímek> pracovni/x.jpg [1] [x0,y0,x1,y1]` → snímek (1 = poloviční rozlišení).
- Trvalý odkaz `https://katalog.ahmp.cz/pragapublica/permalink?xid=<XID>&scan=<N>`.
- Nový portál digi.ahmp.cz má ochranu proti robotům – nepoužívat. Pražské matriky 1890–1940 většinou **nemají rejstříky**
  a farností je mnoho – bez přesného data a farnosti (z úmrtí/sňatku nebo od rodiny) je hledání velmi drahé.

## SOA Litoměřice (severní Čechy) – `tools/soal_zoomify.py`
Stejný software jako ZA Opava (Digitální badatelna) – platí i tamní pasti (`vysledekDetail` přímou adresou ukáže jiný
svazek, výstup JavaScriptu bez parametrů v Claude in Chrome).
- `https://digi.soalitomerice.cz/digitalnibadatelna/` má na vstupu automatické ověření (asi 15 s „počítání“, projde
  samo) → knihu a cestu k obrázkům najdi v prohlížeči (Playwright nebo Claude in Chrome), snímky stahuj nástrojem.
- **Hledání:** ikona Matriky a obec do pole **„Místo / Lokalita“** (hlavní fulltext vrací všech ~18 000 matrik), Enter.
  Výsledky všechny najednou (počet na stránku přepni jedním výběrem, neprocházej stránky). Svazek otevři kliknutím
  ve výsledcích a **na detailu ověř signaturu**. Popis knihy uvádí „Územní rozsah“ (obce knihy) – čti ho první.
  Knihy bývají **rozdělené po obcích** s vlastním stránkováním a rejstříkem na konci.
- **Adresy snímků** (záložka snímků, `actualDetailTab=attachmentsImg`) zjisti úryvkem – jen pro snímky, které čteš,
  postupně s pauzou 3 s (`browser_evaluate`; na stránce téhož svazku, jinak showZoomify vrací prázdnou odpověď):
  ```js
  async () => {
    const snimky = [1, 50, 120];   // jen snímky, které opravdu čteš
    const ent = document.querySelector('[entityuuid]').getAttribute('entityuuid');
    const ids = Object.fromEntries([...document.querySelectorAll('select.getScanSelect option')].map(o => o.value.split('%20')));
    const out = [];
    for (const n of snimky) {
      if (!ids[n]) { out.push(`${n}: snímek v knize není`); continue; }
      const h = await (await fetch(`/digitalnibadatelna/showZoomify/${ent}/${ids[n]}`)).text();
      if (h.trim().length < 300 && !/images\//.test(h)) { out.push(`${n}: BLOKACE („${h.trim().slice(0, 20)}“) – přestaň na 35 minut`); break; }
      const m = h.match(/https?:\/\/images\.[^"'\s]+?\/images\/[^"'\s]+?\.jpe?g/i);
      out.push(`${n}: ${m ? m[0] : 'adresa v odpovědi nenalezena'}`);
      await new Promise(ok => setTimeout(ok, 3000));
    }
    return out.join('\n');
  }
  ```
  Složka v cestě (`…/images/0046/…`, `…/NAD-856/dao/images/0701/…`) se liší mezi knihami i uvnitř jedné knihy –
  adresu nikdy neskládej, vždy celou z výstupu.
- Snímky stahuj nástrojem: `python3 -I tools/soal_zoomify.py "<celá adresa>" 0 pracovni/x.jpg` (0 = plné rozlišení,
  1 = poloviční, 2 = čtvrtinové na orientaci). Obrázkový server images.soalitomerice.cz neomezuje a cookies nepotřebuje.
- **POZOR na blokaci aplikace** (obrázky ne): přijde už po 25–100 rychlých krocích (listování výsledky, Zpět, rychlé
  `fetch`). Ohlásí ji stránka „!“ s **HTTP 200** (asi 116 bajtů) – kontroluj obsah, ne stavový kód. Dotazy jen postupně
  (žádné `Promise.all`), pauza aspoň 3 s, vždy jen jedna smyčka; po blokaci 35 minut nic (další pokusy ji prodlužují).
  Pomocníkům to napiš do zadání.
### SOA Litoměřice – nástroj `tools/litomerice.py` (bez prohlížeče; vyzkoušeno koncem 10. 2026, při selhání nebo blokaci postupuj podle návodu výše)
- Digitální badatelna `https://digi.soalitomerice.cz/digitalnibadatelna/` – Sbírka matrik Severočeského kraje (NAD 856, farní i další matriky,
  často německé). Dřívější návod (CAPTCHA/„počítání“) při ověření v říjnu 2026 nevyšel: hledání i obrázky jdou bez prohlížeče.
- `litomerice.py hledat "Obec" [slovo…] [--stran N]` → `id | pořadí | druh • obce • roky • NAD • signatura`. Dotaz hledá jen mezi **matrikami**
  (99 knih na stránku); u velké obce přidej rok nebo farnost. `litomerice.py info <id>` → původce, roky, signatura, územní rozsah, počet snímků.
- `litomerice.py snimek <id> <snímek> pracovni/x.jpg [nahled] [x0,y0,x1,y1]`, `link`, `svazek` (klíč `soal_<id>`). Portál zobrazuje záznam
  podle pořadí ve výsledcích hledání, proto si nástroj u každého id pamatuje dotaz (`pracovni/litomerice_dotazy.json`) nebo zadej `--dotaz "Obec"`.
- **POZOR: po zhruba 100 rychlých požadavcích na stránky portálu archiv zablokuje přístup na 30 minut.** Každé `snimek`/`info`/`link`
  jsou ~4 požadavky (nástroj dělá pauzy). Nestahuj desítky snímků za sebou; obrázkový server images.soalitomerice.cz limit nemá. Pomocníkům to napiš do zadání.
- Starší návod přes prohlížeč (jen když nástroj selže): zjisti **celou adresu obrázku** (`https://images.soalitomerice.cz/…`)
  v síťovém provozu (`…/ImageProperties.xml`) nebo `document.querySelector('#navigatorImage').src` na stránce snímku a stáhni ho
  `soal_zoomify.py "<celá adresa>" 0 pracovni/x.jpg`. Archiv koncem října 2026 změnil cesty
  (`…/CZ-214000010/NAD-<číslo>/dao/images/<složka>/<uuid>.jpg`); starší zkrácená `<cesta>` za `…/matriky/` vrací 404.

## ZA Opava (severní Morava, Slezsko, Olomoucko, Litovelsko) – `tools/soal_zoomify.py`
- Pozor na hranici: obce na Litovelsku a Olomoucku patří pod **ZA Opava**, ne pod MZA Brno.
- **Bez prohlížeče to nejde.** Badatelna `https://digi.archives.cz/da/` (stará adresa matriky.archives.cz jen přesměruje)
  má ochranu proti robotům – curl ani WebFetch se nedostanou ani na hledání. Potřebuješ připojený prohlížeč (Claude in
  Chrome – uživatel ho v Claude Code připojí příkazem `/chrome` – nebo prohlížeč agenta v Cursoru, nebo Playwright); jinak ať knihu najde a snímky uloží uživatel.
  **Vestavěný prohlížeč aplikace Claude** (desktop, Code) archiv odmítne hned („Anomaly detected“) – nepoužívej ho.
  Úvodní ověření projde samo, ale jen v kartě v popředí. Okno nastav aspoň na 1400×900, v užším se nezobrazí
  filtry ani snímek. **CAPTCHA přijde typicky už u prvního hledání**, pak zhruba po hodině a v nové relaci
  prohlížeče vždy znovu: **vyřeší ji uživatel** v okně prohlížeče, ty nikdy.
- Hledej obec a vyfiltruj Matriky (ikona, potom znovu lupa). Hledání vrací i civilní matriky (u obce stovky svazků) –
  filtr „Datum od – do“ (podle začátku svazku, např. 1680–1873) nechá jen církevní. Knihy bývají řazené po obcích
  a na konci mají rejstřík. Vedle farních knih bývají i **druhopisy** („T“ v signatuře, viz `matriky.md`).
  Když pole Signatura „zamrzne“ a vrací pořád předchozí knihu, napiš obec do hlavního fulltextového pole (Enter)
  nebo ji vyber v poli „Územní rozsah“ z našeptávače.
- **Detail svazku nikdy neotvírej přímou adresou `vysledekDetail/<id>`.** Badatelna drží výsledky hledání v relaci
  a taková adresa ukáže N-tý (bez `page` první) výsledek posledního hledání nebo snímky naposledy otevřeného
  svazku – ne svazek z adresy. Svazek otevři trvalým odkazem `https://digi.archives.cz/da/permalink?xid=<id>`
  (id je konec cesty odkazu ve výsledcích, `vysledekDetail/<id>`) – ten ukáže svazek podle id bez ohledu na poslední
  hledání, ale jen v prohlížeči, který už prošel ověřením. Jinak klikni ve výsledcích (ikona snímků v řádku, nebo
  mozaika výsledků a dvojklik na náhled). **Vždy na stránce ověř signaturu a název knihy**, než z ní cokoli čteš.
- **Seznam svazků a ID snímků si hned ulož** do `pracovni/<svazek>/` – relace po pár hodinách vyprší a výsledky
  hledání platí jen v ní. Na detailu svazku: entita `document.querySelector('[entityuuid]').getAttribute('entityuuid')`
  (u svazků uložených v jiném archivu nemá tvar UUID – nehledej ji regexem), ID snímků jsou hodnoty
  `select.getScanSelect option` (tvar „N%20uuid“). Snímek pak otevřeš kdykoli bez hledání (jediná přímá adresa,
  která na relaci nezávisí):
  `/da/showZoomifySeparate?imageNumberSeparate=N&myEntityUuid=<entita>&myImageUuid=<uuid>`.
- Adresa obrázku: `fetch('/da/showZoomify/<id svazku z URL>/<část option.value za „%20“>')` vrátí HTML s cestou
  `…/images/<složka>/<uuid>.jpg`. Cesta se u svazků liší (`…/CZ-217000010/NAD-165/dao/images/…`, `…/zao/matriky/dao/images/…`)
  a přípona bývá i `.JPG` – nástroji dej vždy **celou adresu z HTML**:
  `python3 -I tools/soal_zoomify.py "<adresa>" 2 pracovni/x.jpg` (2 = čtvrtinové rozlišení na orientaci podle záhlaví
  stránek, 0 = plné jen u nalezeného zápisu). Obrázkový server images.archives.cz neomezuje a cookies nepotřebuje.
- **POZOR na blokování** (jen stránky aplikace, obrázky ne): rychlé dotazy → CAPTCHA, „operace vyhodnoceny jako
  nestandardní“ nebo „Access blocked“ na 30 minut; po desítkách dotazů za den vrací showZoomify „Server Exception“
  (denní limit – pokračuj až další den). Pauza 3–6 s mezi stránkami, dávky do ~80 stránek, žádné rychlé `fetch` hned
  po hledání a stránky výsledků neprocházej za sebou. Delší smyčku pusť v prohlížeči na pozadí, výsledky ukládej do
  `window` nebo `localStorage` a vyzvedávej po částech (nástroj pro JavaScript má limit asi 45 s). Pomocníkům to napiš do zadání.

## MZA Brno (jižní Morava, Acta Publica) – jen v prohlížeči
- Portál `https://www.mza.cz/actapublica/`, bez přihlášení. **Od 2. 11. 2026 MZA blokuje stahovací skripty** (ověření
  Altcha, adresy dlaždic s tokenem) a výjimky nedělá. Skriptem jen hledání knih (níže, brzda 1 dotaz za 4 s, jiné
  adresy MZA brzda zastaví). Snímky jen v jejich prohlížeči: přiblížit zápis a uložit snímek obrazovky. Žádné
  stahování, `fetch` ani skládání dlaždic, žádní pomocníci. Nejlépe Playwright (uloží
  snímek do souboru); jinak ať uživatel pošle snímky obrazovky sám (celá dvoustrana na orientaci, pak přiblížený zápis
  – kolečko myši, macOS Cmd+Shift+4, Windows Win+Shift+S) a ulož je do `pracovni/`.
- Knihy hledá i `mza.py hledat "Obec" [slovo…]` (české, německé i historické jméno obce; čtyřmístné číslo = rok uvnitř
  rozsahu N/O/Z, jiné slovo = text v řádku) a `mza.py puvodce "Farnost" [typ]`. Výpis: `id | č. knihy | původce | N | O | Z | obce | snímků`;
  **`id` je interní číslo z adresy `…/matrika/detail/<id>`**, ne „č. knihy“. Ostatní příkazy `mza.py` (`info`, `snimek`,
  `link`, `svazek`) brzda zastaví – detail knihy a snímky jen v prohlížeči.
- Kniha: `python3 -I tools/slusne.py curl -s "https://www.mza.cz/actapublica/matrika/hledani?typ=obec&search_by_obec=<obec>&page=<n>"`
  → HTML tabulka (číslo knihy, původce, roky N/O/Z, počet snímků, odkaz `matrika/detail/<id>`; číslo knihy ≠ id).
  Výsledky po 20 – projdi i další stránky, než řekneš, že tam obec není. U velkých far jsou samostatné svazky rejstříků (N/O/Z) – začni jimi. Fary založené
  kolem 1784 mají starší zápisy v mateřské faře. Ověření na detailu knihy proběhne samo za pár sekund.
- Detail knihy má „Části matriky“ s rozsahy snímků (narození 1–43, index narozených 43–93, u knih pro víc obcí po obcích).
  Snímek s hledaným rokem odhadni (snímky ÷ roky). Rejstříky uvádějí stranu, ne snímek: přečti čísla stran na 1–2 snímcích
  a dopočítej (vztah bývá lineární, kniha od knihy jiný).
  Pole „Snímek“ v prohlížeči skáče přímo na zadaný snímek. Sňatek bývá ve farnosti nevěsty.
- **Listuj v otevřené stránce** (`viewer.goToPage(n-1)`, šipky) – návrat na už zobrazený snímek jde z mezipaměti
  prohlížeče a MZA nic nestojí. Stránku neobnovuj a adresu snímku znovu neotvírej: nové načtení dostane nový token
  a stáhne všechny dlaždice znovu.
- Prohlížeč je OpenSeadragon v proměnné `viewer`: `viewer.goToPage(n-1)`, `viewer.viewport.goHome(true)` a snímek okna
  (scale css) – rok a měsíc v záhlaví. U nalezeného zápisu odečti z aktuálního snímku okna rohy zápisu a přibliž ho
  úryvkem (browser_evaluate); pak ulož snímek prvního prvku `.openseadragon-container` v rozlišení zařízení do
  `pracovni/mza_<kniha>_<snímek>.png` (Playwright ukládá jen do složky projektu) a dál `vyrez.py` jako u jiných portálů:
  ```js
  async () => {
    const [x0, y0, x1, y1] = [145, 435, 595, 500];   // rohy zápisu na snímku okna (CSS px)
    const vp = viewer.viewport, e = viewer.container.getBoundingClientRect();
    const P = (x, y) => vp.pointFromPixel(new OpenSeadragon.Point(x - e.left, y - e.top));
    const a = P(x0, y0), b = P(x1, y1);
    vp.fitBounds(new OpenSeadragon.Rect(a.x, a.y, b.x - a.x, b.y - a.y), true);
    await new Promise(ok => setTimeout(ok, 5000));
    return location.href;
  }
  ```
- Nezobrazuj celou stránku v plném rozlišení (velké okno) – stovky dlaždic naráz a MZA vrací 503. Tempo 5–10 s mezi
  stránkami (SKILL.md, Šetrně k archivům), jen stránky, které opravdu čteš. Když ověření nepustí nebo MZA hlásí chybu, skonči a řekni to uživateli.
- Trvalý odkaz = adresa v prohlížeči `…/matrika/detail/<id>?image=<soubor>.jp2` (soubor končí číslem snímku × 10:
  snímek 16 → `…-00160.jp2`). Svazek do `svazky.json` ručně (Ostatní portály, krok 4).
- Doména actapublica.eu MZA nepatří (MZA to potvrdila) – nepoužívej ji, jen www.mza.cz/actapublica. Když MZA nejde
  načíst ani v prohlížeči, ať uživatel zkusí vypnout VPN nebo jinou síť.
- **Sčítací operáty (1857–1921) nejsou v Acta Publica**, ale v samostatném portálu
  `https://www.mza.cz/scitacioperaty/digisada/search` – jen v prohlížeči (brzda jiné adresy MZA nepustí), stejná pravidla
  jako u matrik: žádné stahování ani skládání dlaždic. Hledej obec (pole „Město/obec nebo část obce/osada“); sada =
  jedna obec a jeden rok (u obce bývá jen některý rok, např. jen 1921), s rozsahem čísel popisných. Detail
  `…/digisada/detail/<id>` má stejný prohlížeč `viewer` jako matriky (postup výše). Snímek 1 je soupis s metadaty
  (rozpis čísel, poznámky typu „čp. 134 má 2 archy“), pak archy po domech. 1857 uvádí jen rok narození, 1869 a 1880
  místo i datum; sloupec dat narození bývá psaný svisle – při čtení přiblížený výřez otoč o 90°.

## Po válce přistěhovaní, reemigranti, přesídlení (osídlování pohraničí 1945–1950)
Ověřené (2026-10): v Národním archivu je fond **Ministerstvo práce a sociální péče, Praha** (NAD 1028), inv. č. 655, sign. 3521: „Reemigrace – čs. reemigrační mise ve Vídni,
reemigrační střediska v Žatci, Berouně, Chebu, reemigrace z jednotlivých zemí (Argentina, Bulharsko, Čína, Francie, Německo, Polsko, **Rumunsko**…), 1946–1949“ – nezdigitalizováno
(0 snímků), jde o badatelnu (dotaz do `archivni_dotazy.md`). Další fondy hledej `vademecum.py hledat "reemigrace"` a podle obce. Zbytek postupu níže je z literatury (nevyzkoušeno):
Matriky tady nestačí: lidé, kteří přišli po 1945 do pohraničí (Volyňští Češi, reemigranti z Rumunska, Jugoslávie,
Polska, Slováci a Češi z vnitrozemí), mají v matrikách jen narození a sňatky *před* příchodem v jiné farnosti, často v zahraničí.
Skill pro ně zatím nemá hotový nástroj ani vyzkoušený portál. Postup, který je podle literatury rozumný, ale na skutečném případu
ho nikdo neověřil – vždy ho zapiš do `STAV.md` a výsledek do `poznamky_pro_skill.md`:
1. **Zeptej se rodiny**: odkud a kdy přišli, na jaké hospodářství/dům (číslo popisné!), jaké měli doklady (osídlenecký
   dekret, přídělová listina, domovský list, repatriační průkaz).
2. **Rodiště před příchodem** (matriky v cizině): Volyň – skeny jsou na Ukrajině a v Polsku, ne online; Rumunsko/Jugoslávie –
   FamilySearch a farní matriky v místě; Polsko – Geneteka, Matricula (viz níže). Mladší než 100/75/30 let jen na matričním úřadě.
3. **Úřední spisy o osídlení**: národní výbory (MNV, ONV), osídlenecké komise a Národní pozemkový fond; písemnosti IX. odboru
   ministerstva zemědělství jsou podle literatury v archivu Ministerstva zemědělství ČR a nejsou uspořádané, přehled pramenů
   k Volyňským Čechům v Národním archivu je v článku L. Kločkové (Sborník NM, 2015). Spisy konkrétního domu/hospodářství hledej
   ve **státním okresním archivu** (SOkA) podle obce, fond „Místní národní výbor <obec>“ a „Okresní národní výbor“. Online to
   většinou není – zapiš do `archivni_dotazy.md` (archiv, fond, obec, číslo domu, jméno) a pošli dotaz archivu.
4. **Evidence obyvatel do 1953** (Praha): podle webů zastupitelských úřadů se o ni žádá přes Národní archiv (zvláštní formulář),
   zatímco AHMP má pražské matriky. Pro 1850–1914 viz policejní přihlášky výše; ověř si aktuální postup u archivu.
5. **Německé obyvatelstvo, které odešlo** (odsun) – jeho matriky jsou v archivech pohraničí normálně (Litoměřice, Plzeň,
   Opava); osud po odsunu v Německu: Arolsen, Lastenausgleichsarchiv (Bayreuth) – nevyzkoušeno.
6. **Narození, sňatky a úmrtí českých občanů v cizině** zapisuje **Zvláštní matrika** (Úřad městské části Brno-střed, odbor matrika, Dominikánská 264/2, Brno; podle
   webu MV zápis podáš osobně, přes zastupitelský úřad nebo přes kterýkoli matriční úřad v ČR, se zahraničním dokladem; zápis je bez poplatku, stejnopis 300 Kč – údaje ověř,
   mění se). Pro starší události zjisti u úřadu, jestli a čím lze zápis doložit. Hodí se u předků narozených v zahraničí, kteří měli československé občanství.
7. **Evidence obyvatel a sčítání** (do 1946) jsou u okresních archivů; FamilySearch je katalogizuje jako „Czech Republic, <okres>, <obec>, census, 1869-1946“.
   Mohou ukázat předchozí (německé) obyvatele domu, kam se rodina přistěhovala. Rodina, která dorazila až 1947, v nich ještě být nemusí.
Žádný z těchto kroků nenahrazuje hledání v matrikách; je to jen cesta, jak zjistit, **odkud rodina přišla**, aby se mělo
kde matriky hledat.

## Židovské matriky 1784–1949 (Národní archiv) – `tools/vademecum.py`, bez prohlížeče
- **Pozor:** dřívější adresa `badatelna.eu` už s Národním archivem nesouvisí (v říjnu 2026 je to cizí web). Židovské matriky jsou
  v **Archivním VadeMeCum** `https://vademecum.nacr.cz` (NA se přestěhoval na na.gov.cz). Dva fondy: **HBMa** „Matriky židovských
  náboženských obcí v českých krajích“ (NAD 167, 1784–1949) a **HBM** „Židovské kontrolní matriky“ (NAD 144, opisy vedené u farních
  úřadů, 1780–1911 – dobré, když originál chybí). Knihy jsou po židovských obcích (např. „FÚ Dambořice“) a letech, ne po jménech.
- `vademecum.py hledat "Obec" [--jen-snimky] [--stran N]` → `xid | druh | inv. č. | NAD | roky | popis | počet snímků`. Hledá fulltextem, takže
  najde i obec, která je uvedena jen v rejstříkových heslech spádových obcí. **Název židovské obce a seznam obcí v knize** vypíše
  `vademecum.py info <xid>` – tam ověř, že je to správná kniha. Roky v popisu bývají „(i)“ = s rejstříkem.
- `vademecum.py snimek <xid> <snímek> pracovni/x.jpg [nahled] [x0,y0,x1,y1]`, `link <xid> <snímek>` (trvalý odkaz na sken),
  `svazek <xid>` (do `svazky.json`, klíč `nacvm_<prvních 8 znaků xid>`). Snímek vyžaduje ImageMagick; staví na `soal_zoomify.py`.
- Matriky jsou psané **německy** (kurent/latinka) a tištěné rubriky jsou německé (Der Verstorbenen, Der Geborenen…); jména se píší
  německy (Jakob, Moses), přijmení jednotlivých osob se v 19. století pravopisně liší.
- Lhůty jako u církevních matrik (narození 100, sňatky 75, úmrtí 30 let); mladší židovské matriky jsou na matričním úřadě.
- Oběti, jejichž rodiny jsou v těchto matrikách, najdeš i v `obeti.py` (viz níže). Stejné VadeMeCum má i další archivy,
  nástroj je zatím nastavený jen na Národní archiv.

## Databáze obětí nacistické perzekuce – `tools/obeti.py`
- `obeti.py hledat --prijmeni Neumannová [--jmeno Anna] [--bydliste Ostrava] [--misto-narozeni …] [--rok 1906]` → jméno, datum narození,
  transporty (Terezín → Osvětim…), osud, odkaz. `obeti.py detail <odkaz>` vypíše poslední bydliště, adresu v protektorátu a transporty.
  Příjmení hledej **v ženském tvaru** („Neumannová“, ne „Neumann“) a nejdřív jen příjmení.
- Je to vodítko k osudu osob a k tomu, **odkud rodina pocházela** (poslední bydliště před deportací). Citlivé údaje – na web jen se
  souhlasem rodiny (`soukromi.md`). Romové mají samostatnou databázi (odkaz na holocaust.cz).

## Vojáci 1. světové války – nevyzkoušeno
- **Seznamy ztrát c. a k. armády** (Verlustlisten, 1914–1919, tištěné; jména, domovská obec, datum narození, stav) jsou digitalizované
  ve **Digitální studovně Ministerstva obrany** (digitalnistudovna.mo.gov.cz, plný text) a v Kramerius NK / ANNO. Odkazy shrnuje
  stránka VHÚ „Seznamy ztrát rakousko-uherské armády“ (vhu.cz/knihovna). Vojenské úmrtní matriky téhož portálu uvádějí
  podle VHÚ přes 160 000 padlých.
- **Centrální evidence válečných hrobů**: valecnehroby.army.cz. Databázi VÚA-VHA (kartotéka padlých) shrnují webové odkazy MZV.
- Servery ministerstva obrany jsou ze zkušebního prostředí skillu nedostupné (brána vrací 502 – nejspíš blokují zahraniční IP),
  proto nástroj hotový není. `kramerius.py` umí `--server https://<knihovna>` (API Kramerius v5); studovna MO používá stejný typ adres (`/uuid/uuid:…`), takže
  to může fungovat: `kramerius.py 'text_ocr:"Jan Novák"' 10 --server https://digitalnistudovna.mo.gov.cz`. Při zkoušce z prostředí skillu (říjen 2026) server odpověděl,
  ale jeho certifikát nebyl důvěryhodný (CERTIFICATE_VERIFY_FAILED) – **kontrolu certifikátu nevypínej**; na počítači uživatele to může jít, nebo studovnu použij v prohlížeči.

## Encyklopedie dějin města Brna (Archiv města Brna) – `tools/brno_encyklopedie.py`
- `brno_encyklopedie.py hledat "Novák klempíř Králova"` → až ~30 zásahů fulltextu (osobnost, ulice, objekt, spolek…) s úryvkem a odkazem; portál vrací jen první stránku,
  zužuj dalšími slovy (příjmení, ulice, povolání). `detail osobnosti:15` (nebo odkaz z výpisu) vypíše celé heslo: narození, úmrtí, **bydliště s adresou**, vzdělání,
  zaměstnání, **hrob (hřbitov, skupina, číslo hrobu)**, poznámky.
- Je to tištěná encyklopedie významných osob a míst, ne evidence obyvatel – běžní předkové tu být nemusí. U brněnských řemeslníků a úředníků ale často dá adresy,
  povolání a hrob na Ústředním hřbitově (a z toho pokračuj v matrikách MZA, `mza.py`). Zdroj cituj jako „Encyklopedie dějin města Brna“.

## Další pomůcky a zdroje (ověřeno 2026-10)
- **Historický lexikon obcí ČR 1869–2015** (ČSÚ, `csu.gov.cz` – web se přestěhoval z czso.cz; hledej „Historický lexikon obcí“): změny názvů, příslušnost obcí k okresům, počty
  obyvatel a domů při sčítáních. Pomůže, když obec zanikla, změnila jméno nebo okres.
- **GOV – Genealogisches Ortsverzeichnis** (gov.genealogy.net): historická německá a česká jména obcí a farní příslušnost (Würbenthal = Vrbno pod Pradědem). Portál je chráněný
  kontrolou prohlížeče (Anubis) – otevři ho **v prohlížeči uživatele**, nástrojem nejde.
- **Online-OFB** (online-ofb.de): přepsané německé farní knihy včetně sudetských obcí (rodiny po rodinách). Pro německé předchozí obyvatele pohraničí; hledej obec v seznamu.
- **JewishGen** (jewishgen.org/databases): databáze židovských rodin z Čech, Moravy, Rakouska, Maďarska; část vyžaduje bezplatnou registraci.
- **Kroniky obcí a školní kroniky**: bývají digitalizované ve fondech archivů (v ARON `aron_search.py "Obec" "kronika"`, v Porta fontium a eBadatelně podle fondu). Obecní kronika
  často popisuje osídlení po 1945 (odkud kdo přišel) a rodiny po jménech.
- **Digitální badatelna Národního archivu** (na.gov.cz → Badatelna → Digitální badatelna) zahrnuje též Knihy židovských familiantů, Desky zemské, Monasterium (listiny),
  Translokační plány židovských obydlí, Sbírku staničních kronik (železničáři) a Politické procesy 50. let; ve VadeMeCum je prohledá `vademecum.py hledat`.

## Pražské policejní přihlášky 1850–1914 (Národní archiv) – `tools/policie_prihlasky.py`
- Karty pražských rodin: hlava rodiny, manželka s rokem a místem narození, děti s roky, adresy, někdy místo sňatku.
  Výborné, když rodina žila v Praze a nevíš farnost (pražské matriky nemají rejstříky).
- `python3 -I tools/policie_prihlasky.py Kolar [Jan] [1850] [1870]` – příjmení bez diakritiky (začátek jména), jméno a roky
  narození volitelně. Bez prohlížeče vrátí jen prvních 20 výsledků, proto hledej co nejúžeji.
  Kartu stáhni `policie_prihlasky.py karta <pořadí> pracovni/karta.jpg Kolar [Jan] [1850] [1870]` (stejné hledání; jde i pořadí
  nad 20) – vypíše citaci a trvalý odkaz (`index.php?action=link&ref=czarch:CZ-100000010:874&karton=K&folium=F`).
- **Nepokrývá Smíchov, Vinohrady, Žižkov, Karlín a další předměstí před 1922** (byla to samostatná města) – tak to bylo zjištěno při
  hledání; Národní archiv na své stránce uvádí, že policejní rajon od 1853 zahrnoval i Karlín, Libeň, Smíchov a další, takže u předměstí
  nehledej jistotu v žádném směru a zkus obě cesty. Náboženství karty neuvádějí.

## Matricula (Rakousko, Německo, Polsko, Itálie, Srbsko, Slovinsko; data.matricula-online.eu) – `tools/matricula.py`, `tools/matricula_*.sh`
- **`matricula.py` (bez prohlížeče, ověřeno)** najde farnost, knihu a číslo snímku: `oblasti [cesta]` (země a diecéze), `fary oesterreich/wien [slovo]`,
  `knihy oesterreich/wien/01-am-hof` (druh, roky, úložiště), `snimky oesterreich/wien/01-am-hof/01-01` (popisky snímků včetně rejstříků „Index“).
  Matricula nehledá podle obce ani jména – znáš-li farnost (z úmrtí, sňatku, od rodiny), ušetří to hodně času. **Obrázky ale chrání token počítaný
  JavaScriptem prohlížeče; nástroj ho nenapodobuje.** Snímek stáhne `node tools/matricula_snimek.js <cesta-knihy> <snímek> pracovni/x.jpg`: otevře knihu v pravém prohlížeči
  (Playwright: jednou `npm install playwright && npx playwright install chromium`), počká, až si stránka sama načte obrázek, a uloží ho (ověřeno na vídeňské knize, ~1,3 MB na snímek).
  Hlídá, aby číslo snímku nepřesáhlo počet snímků knihy (prohlížeč jinak tiše dá poslední snímek). Prohlížeč není řízen brzdou `slusne.py`: stahuj jen to, co čteš, a při blokaci nebo chybě nepokračuj. Bez Playwrightu: Claude in Chrome nebo ruční uložení.
- **Vídeň:** 567 farností pod `oesterreich/wien/<obvod>-<farnost>` (např. `01-am-hof`). Podle přednášky FamilySearch (2023) jsou oddací a úmrtní knihy
  online do 1938 a křty do 1922, mladší se postupně otevírají – ověř na portálu. Židovské matriky Vídně: Israelitische Kultusgemeinde a mikrofilmy ve
  Wiener Stadt- und Landesarchiv (WStLA). Bydliště před 1976: dotaz WStLA (online formulář). Hřbitovní databáze **friedhoefewien.at → Verstorbenensuche**
  (nástroj nevznikl: widget volá bránu api.wstw.at přes zabezpečenou proxy portálu a samotná brána vyžaduje přihlášení, takže bez obcházení autentizace to nejde; hledej v prohlížeči). Vídeňští Češi: rodina se často „ztratí“ ve Vídni – hledej křest dětí a sňatek ve farnosti bydliště.
- **Srbsko (Matricula):** část Banátu a Vojvodiny (např. `serbien/subotica`) – ověř, jestli je tam hledaná fara. **Polsko** (Slezsko, Opolsko) viz Geneteka níže.
- Bez přihlášení. Seznam knih: `…/de/oesterreich/<diecéze>/<farnost>/?page=N`; snímek knihy `…/<id>/?pg=<snímek>`
  (zároveň trvalý odkaz).
- URL obrázku obsahuje `csrf` a `ctrl` počítané JavaScriptem → je potřeba prohlížeč (Playwright / Claude in Chrome, v Cursoru prohlížeč agenta):
  otevři knihu, klikni na stránku (`.docview-pagelink`), URL obrázku vezmi z `performance.getEntriesByType('resource')`
  a stáhni `bash tools/matricula_dl.sh "<url>" pracovni/x.jpg`. Víc stránek: soubor řádků „<snímek> <url>“ → `matricula_batch.sh`.
- Rejstřík najdeš bez prohlížeče: HTML stránky knihy má seznam `labels` s popisky snímků („04-Index Taufe_0001“).
- Vojenské matriky (např. Štýrský Hradec) tam nejsou – jsou v Kriegsarchivu ve Vídni (offline).

## Slovensko, Maďarsko, Rumunsko (Banát, Sedmihradsko) – nevyzkoušeno, jen návod
Stav ověřený v říjnu 2026 ze zkušebního prostředí skillu: slovenské (archives.gov.sk), maďarské (adatbazisokonline.hu, Hungaricana, Arcanum) a rumunské
(arhivelenationale.ro) archivní servery byly **nedostupné nebo za Cloudflare (HTTP 403)**, proto nástroje nevznikly. Postup pro uživatele (přes jeho prohlížeč):
- **FamilySearch** (přihlášení zdarma; viz oddíl níže) je pro tyto země hlavní cesta: katalog podle místa → „Church Books / Anyakönyvek / Cirkevná matrika“.
  Slovensko: církevní matriky zhruba 1590–1895 (snímky online), jména často maďarsky/latinsky; **Maďarsko**: církevní matriky (rodné, oddací, úmrtní)
  do 1895, občanské matriky od 1895; **Rumunský Banát a Sedmihradsko**: farní matriky Banátu byly mikrofilmovány 1939–40 (rozsah zhruba 1760–1850), latinsky a německy.
- **Hranice a jména:** do 1918 byly Slovensko, Banát i Sedmihradsko v Uhrách – obce mají **maďarské názvy** (a německé, rumunské); hledej v matrikách pod tím, co platilo v době zápisu.
  Jména: Ferenc = František, József = Josef, János = Jan; příjmení Magyar je „Maďar“ (Madar).
- **Státní archivy** (Slovenský národný archív a štátne archívy; Magyar Nemzeti Levéltár; Arhivele Naționale – např. pobočka Timiș má občanské matriky
  1717–1951): většina knih není online, žádost o výpis podle obce a roku. Mladší matriky (do 100/75/30 let) jen na matričním úřadě.
- **Čeští reemigranti z Rumunska (Banát):** české obce v Banátu (Svatá Helena, Gerník, Eibentál, Bígr, Rovensko aj.) a jejich obyvatelé se po 1945 vraceli do
  Československa (zejména 1946–1950) a usazovali v pohraničí. K původu rodiny zapiš: obec v Banátu, vyznání, jméno rodiny v Banátu (často německy/česky pomaďarštěné). Cesta:
  rozhovor s rodinou → FamilySearch (farní matriky obce) → spisy o osídlení/reemigraci (viz „Po válce přistěhovaní“ výše).
- **Maďarsky/slovensky psané zápisy**: čti pomalu, tabulky mají rubriky (rodiče, kmotři, vyznání); Claude umí maďarštinu a slovenštinu, latinu a němčinu, ale u písma buď opatrný (označ nejistá místa „(?)“).

## Polsko – Szukaj w Archiwach a Geneteka
- **Szukaj w Archiwach** (szukajwarchiwach.gov.pl, polské státní archivy se skeny matrik): portál je chráněný systémem Imperva Incapsula (JavaScriptová kontrola
  prohlížeče), prostým HTTP nic nevrátí. Nástroj proto nevznikl; ochranu neobcházíme. Hledej v prohlížeči uživatele (jmenný index u části souborů, „Wyszukiwanie zaawansowane“).

## Polsko – Geneteka (geneteka.genealodzy.pl)
- Zdarma dobrovolnické indexy křtů, sňatků a úmrtí po farnostech; hledej ve webovém rozhraní (vojvodství → farnost →
  příjmení). Index je vodítko – skeny často online nejsou (farní nebo diecézní archiv), pak zápis žádej tam.
- **Farní příslušnost se měnila**: obec mohla patřit k sousední faře (Lipowa → Radziechowy do 1896) – hledej i tam.
- Nestahuj hromadně: PTG uvádí „linkujemy, nie pobieramy danych“ (odkazujeme, nestahujeme) a po desítkách rychlých dotazů
  server vrací nefiltrovaná data. Dotazy dávkuj, s pauzami, a výsledky si ověř.
- Jednotlivý dotaz jde i bez prohlížeče: `https://geneteka.genealodzy.pl/api/getAct.php?draw=1&start=0&length=10&bdm=B&rid=B&w=12sl&search_lastname=<příjmení>&search_name=&search_lastname2=&search_name2=&from_date=1850&to_date=1900&exac=1`
  (`bdm`/`rid` B křty, S sňatky, D úmrtí; `w` vojvodství, např. 12sl slezské, 08op opolské) → JSON. Past: `recordsTotal` > 0
  a prázdné `data` – zkus jen jedno příjmení bez křestního jména a užší roky. Stránkování opakuje řádky.
- Skeny některých polských far jsou i na Matricule (výše) nebo FamilySearch (níže).

## FamilySearch (přes uživatelův přihlášený prohlížeč)
- Přihlášení je potřeba i na hledání v indexech. České matriky tam skoro zindexované nejsou (Slovensko ano, hlavně křty).
- Jen když ho má uživatel otevřený a sám nabídne. Z kontextu stránky lze volat JSON API
  `https://www.familysearch.org/service/search/hr/v2/personas?q.surname=…&q.givenName=…&q.fatherGivenName=…&count=20`
  (`fetch(…, {credentials:'include'})`); výsledky v `entries[].content.gedcomx`.
- Užitečné na indexy matrik a hroby (BillionGraves, Find a Grave). Výsledek je vodítko – ověř v matrice.
- Neměň uživateli otevřené karty (po hledání vrať původní adresu). Stránky za Cloudflare neobcházej – ať je uživatel
  otevře sám a pošle snímek obrazovky.
- Snímky filmu (DGS): seznam přes `POST /search/filmdatainfo/image-data` s `{"type":"film-data","args":{"dgsNum":"00…","state":{"i":"0"},"locale":"cs"}}`
  (`images[]` = ARK). Snímek: `https://www.familysearch.org/service/records/storage/deepzoomcloud/dz/v1/<ARK 3:1:…>/$dist`
  (plné rozlišení), malé náhledy `…/image_files/8/0_0.jpg`. **Po ~1000 rychlých požadavcích přijde HTTP 429** a blokace
  na desítky minut – stahuj jen konkrétní snímky, nanejvýš pár za sekundu, hromadné procházení knih nedělej.
- **Slovensko** (sbírka „Slovakia Church and Synagogue Books 1592–1935“; bez účtu FamilySearch to nejde):
  1. **Fara:** katalog `https://www.familysearch.org/search/catalog/results?q.keywords=Farský úrad <obec>` (také
     „Grécko-katolícka …“, „Evanjelická …“). Najde i fary celého okolí – v závorce za farou je obec, pod kterou je
     katalog vede. Hledání podle místa (`q.place`) a maďarské názvy obcí často nenajdou nic nebo stejnojmennou obec v ČR.
  2. **Natočené roky:** v záznamu fary přečti tabulku filmů (`browser_evaluate`, jen text, bez odkazů):
     `[...document.querySelectorAll('tr')].map(r => [...r.cells].map(c => c.innerText.trim()).join(' | '))`
     → Poznámka (druhy a roky) | Film | **DGS**. Název záznamu přeceňuje: „Cirkevná matrika, 1762–1927“ má křty,
     sňatky i úmrtí jen do **1895** (do 1927 jen biřmování). Po ~1895 vedl stát civilní matriky – mladší zápisy jsou
     ve státním archivu nebo na matričním úřadě (na Slovensku 100 let i u úmrtí), ne online.
  3. **Index je neúplný** (hlavně křty) a jména zkomolená, u dvou křestních jmen bývá jen jedno; `q.anyPlace`
     výsledky nefiltruje, jen řadí. Hledej přes rodiče a bez křestního jména, jinak listuj snímky filmu (DGS výše;
     nejdřív rejstřík „Zoznam krstov A–Z“, bývá na začátku knihy).
  4. **1900–1940:** doklady od rodiny (rodné listy dětí uvádějí i prarodiče), náhrobky a evidence hrobů (Košice:
     gisplan.kosice.sk; cintoriny.sk jen část obcí). Rusíni vedení po 1950 jako pravoslavní mají starší zápisy
     v řeckokatolických knihách.
- **Snímek do projektu (Playwright):** nástroje dostanou od FamilySearch 403, snímek vydá jen přihlášený prohlížeč.
  Uživatel se jednou přihlásí v okně Playwrightu (přihlášení zůstane). ARK snímku je v adrese prohlížeče
  (`/ark:/61903/3:1:…`) i ve výsledcích hledání. Nejdřív `python3 -I tools/cache.py najdi <adresa nebo ark>
  --nahled pracovni/nahled.jpg` – je-li snímek už uložený, prohlížeč nepotřebuješ. Jinak `browser_evaluate`
  s `filename: "pracovni/fs.json"`:
  ```js
  async () => {
    const ark = '3:1:XXXX-XXXX-XXX';
    const adresa = `https://www.familysearch.org/service/records/storage/deepzoomcloud/dz/v1/${ark}/$dist`;
    const r = await fetch(adresa, {credentials: 'include'});
    if (!r.ok) return `HTTP ${r.status} – snímek nejde stáhnout (přihlášení? omezený snímek?)`;
    const b = await r.blob(), bm = await createImageBitmap(b);
    const data = await new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result); f.readAsDataURL(b); });
    return JSON.stringify({w: bm.width, h: bm.height, adresa, data});
  }
  ```
  a `python3 -I tools/cache.py uloz pracovni/fs.json pracovni/fs_<ark>.jpg --nahled pracovni/nahled.jpg` (snímek
  v plném rozlišení do mezipaměti i do `pracovni/`, json smaže). Dál `vyrez.py` jako u jiných archivů.
- **Bez Playwrightu (Claude in Chrome neumí ukládat do souboru):** ať uživatel snímek stáhne tlačítkem Download
  (nebo ho se souhlasem stáhneš ty) – soubor přijde do `~/Downloads` jako `<id snímku>.jpg`, chvíli může mít
  příponu `.tmp`. Přesuň **jen soubor s očekávaným názvem**, nikdy „nejnovější soubor ve Stažených“ (je tam i cizí).
  Žádné vlastní přijímače na localhostu ani jiné obcházení ochran prohlížeče.

## Hroby a hřbitovy
- Kde jsou předci pohřbeni, víš z rozhovoru s rodinou (Fáze 1). Fotky náhrobků (jména, data, rodná příjmení) jsou
  cenný pramen hlavně pro 20. století, kde matriky ještě nejsou přístupné.
- Evidence hrobových míst: správa hřbitova (kdo je v hrobě uložen, kdo platí nájem – často žijící potomek);
  řada měst má online vyhledávání hrobů. Mezinárodně BillionGraves a Find a Grave.

## Noviny a ročenky – `tools/anno.py`, `tools/anno_snap.py`, `tools/kramerius.py`
**Kdy se vyplatí:** státní a vrchnostenští úředníci, soudci, učitelé, faráři, důstojníci, vojenští lékaři, notáři,
poštmistři, starostové, podnikatelé – noviny otiskovaly jmenování, přeložení, vyznamenání, penze, konkurzy, oznámení
sňatků a parte (zhruba od 1860). Z toho plyne, **kde člověk kdy žil** → kde hledat křty dětí, sňatek, úmrtí.
A když osoba „chybí“ v očekávaných matrikách (stěhovala se se službou). **Spíš ne:** sedláci a řemeslníci na vsi.
- ANNO (rakouské noviny 1700–1950, i Prager Zeitung, Wiener Zeitung): `python3 -I tools/anno.py '"Johann Nowak"' 1860 1915 [stran] [--snip]`
  – jména **německy** („Johann Nowak“, „Wenzel Dworschak“). Výřez místa: `tools/anno_snap.py <docId> "<dotaz>" pracovni/x.jpg`.
  ALEX a annoshow jsou za Cloudflare – neobcházet. Ze zkušebního cloudového prostředí ANNO spojení resetuje (nástroj je v pořádku, jde o síť).
- Kramerius NK ČR (české noviny, ročenky, adresáře): `python3 -I tools/kramerius.py 'text_ocr:"Jan Novák" AND datum_begin:[1900 TO 1910]'`.
- Vojenské schematismy: fulltext na archive.org (např. `militrschematis13kriegoog` = 1850).
- **Vojáci 1. světové války – seznamy ztrát** (ANNO, plný text): `python3 -I tools/anno.py '"Příjmení Jméno"' 1914 1919 3 --snip --ztraty`
  (jen `vll` Verlustliste, `vlv` abecední rejstřík s číslem seznamu, `nvv` Nachrichten über Verwundete; jiné listy
  `ANNO_TITLE=ptb,wrz`). Záznam: hodnost, pluk, setnina, **domovská obec, ročník**, raněn/zajat/padl – např.
  „Hromadko Wenzel, Inft., IR. Nr. 98, 4. Marschkomp., Rokosnitz, 1881, Schuß …“. Pořadí je „Příjmení Jméno“, německy
  (Wenzel, Johann) a zkus i bez háčků; shodu potvrď obcí a ročníkem. Běžná příjmení mají tisíce výskytů – hledej
  vzácným příjmením nebo domovskou obcí v německém tvaru. Krajské noviny otiskovaly seznamy padlých okresu.
  Padlí na frontě v domovské matrice zemřelých často nejsou. Kartotéka padlých VÚA je jen v Digitální badatelně MO
  po registraci (stará databáze VÚA už neexistuje).
- **Rizika:** jména se opakují a fulltext šumí („Winter“ = i zima, „Novák“ = nový obyvatel). Ztotožni jen při shodě víc údajů (bydliště,
  funkce navazující na matriku, časová posloupnost). Zdroj je „J“ (jiný pramen) – vodítko a příběh, ne náhrada matriky.
- Výstřižky jsou skvělé na web: ulož do `dokumenty/noviny/`, přes `vyrez.py` a do `dokumenty.json`.
- Pořadí: nejdřív matriky; noviny, když chybí stopa kvůli stěhování, nebo když jde o úředníka/vojáka a chceme příběh.

## Ostatní portály – obecný postup
Nástroje pro ně hotové nejsou. Postupuj takto a výsledek zapiš do `STAV.md`, ať to příště víš:
1. Otevři portál v prohlížeči (Claude in Chrome / prohlížeč v Cursoru / Playwright, pokud jsou k dispozici; jinak požádej uživatele).
   Najdi fond „Sbírka matrik“ / „Matriky“ a svazek podle obce a let.
2. **Snímek:** většina prohlížečů má tlačítko ke stažení obrázku – ulož do `pracovni/`. Když ne, podívej se v síťovém
   provozu, odkud se načítají dlaždice/obrázky (IIIF, DeepZoom, Zoomify), a stáhni celý obrázek touto cestou – jednotlivě,
   jen snímky, které čteš, a jen když to archiv nezakazuje (`<portál>/robots.txt`, podmínky užití). Krajní možnost: požádej uživatele, ať snímek uloží a dá do `pracovni/`.
3. **Trvalý odkaz** na snímek (tlačítko „trvalý odkaz“/permalink, jinak URL svazku + číslo snímku) dej do `odkaz` v zápisu.
4. Svazek zapiš do `data/svazky.json` ručně: `"klic": {"archiv": "SOA Třeboň", "portal": "digi.ceskearchivy.cz",
   "svazek": "N Volary 1784–1820, sign. …", "popis": "obce…", "url": "<odkaz na svazek>"}`.
5. Dál stejně jako u ARON: `vyrez.py`, `ramecek.py`, přepis, osoby, deník.
6. Když se postup osvědčí, napiš pro portál vlastní malý nástroj podle `portafontium.py` (bez prohlížeče, jen když to archiv nezakazuje)
   a postup zapiš do `STAV.md`. Poznatek zapiš i do `poznamky_pro_skill.md` (pro správce skillu).

## Starší prameny (17.–18. století)
- **Soupis poddaných podle víry 1651** – celé rodiny s věkem, po krajích; edice Národního archivu jako PDF
  (nacr.cz, hledej „Soupis poddaných podle víry“ + kraj). Fulltext v PDF, příjmení často bez diakritiky / s jinou ortografií
  (Šaršoun → „Šaroun“, dlouhé ſ jako f). Ves je v rámci panství; poznamenej si stránku edice.
- **Berní rula 1654** – jen hospodáři s půdou; edice a rejstříky v knihovnách (Kramerius/DNNT).
- **Gruntovní (pozemkové) knihy** – převody domů z otce na syna; online jen část (SOA Plzeň téměř vše, SOA Praha část,
  ostatní spíš badatelna). Fond „Velkostatek <panství>“.
- **Další písemnosti vrchnosti (fond „Velkostatek <panství>“, do 1850)** – když matrika nestačí (původ přistěhovalce,
  vojáka, chybějící rodiče): soupisy poddaných (po letech, celé domácnosti s věkem), knihy svatebních smluv a kontraktů,
  sirotčí knihy a pozůstalostní spisy (dědici, jejich věk a bydliště), protokoly invalidů a propuštěných vojáků,
  výhostní (propouštěcí) listy, urbáře. Postup: najdi panství z matričního zápisu („poddaný panství X“) → kartu fondu
  v katalogu archivu (ARON / Digitální badatelna) → inventář otevři jako strom. Fond bývá i v **jiném** archivu než
  matriky; „Index ne“ v katalogu neznamená, že kniha nemá místní rejstřík (zkus začátek i konec knihy). Karta bez
  skenů neznamená, že kniha neexistuje → zapiš do `archivni_dotazy.md`. Stopu na vrchnostenský soud dávají i výzvy
  dědicům v novinách (ANNO, Prager Zeitung: „Edikt … Herrschaft X“).
- **Zemské desky** (Národní archiv; Morava MZA Brno) – evidence **deskových statků**: šlechta, svobodníci, majitelé
  deskových dvorů a některá města. Pro poddané sedláky a chalupníky v nich nic nebude (ti jsou v gruntovních knihách).
  Vyplatí se jen u předka-svobodníka nebo majitele statku; středověké a raně novověké zápisy částečně jako edice
  v Czech Medieval Sources (sources.cms.flu.cas.cz, kategorie „Desky zemské“). Originály jen v badatelně.
- **Mlýny a mlynáři – vodnimlyny.cz** (pozor: `databaze.vodnimlyny.cz` neexistuje, databáze je na
  `www.vodnimlyny.cz/mlyny/objekty/`). Karta mlýna má sekci **Historie** s držiteli mlýna v chronologickém sledu
  (často z gruntovních knih, urbářů, katastrů), prameny a fotky. Vyplatí se, když je předek mlynář nebo se narodil
  „ve mlýně“ / v čp. mlýna: potvrdí rod na mlýně přes generace, dá příběh a obrázky na web. Hledá se podle obce,
  katastru, toku i jména mlynáře (pole jsou dobrovolně vyplněná – „nenalezeno“ nic nedokazuje). Bez prohlížeče:
  GET `/mlyny/objekty/` (cookies), pak POST tamtéž s hlavičkou `X-Requested-With: XMLHttpRequest` a poli
  `_do=filter-form-submit`, `city=<Obec>` (nebo `miller=<Příjmení>`), `send=Filtrovat` → JSON, výsledky v
  `snippets["snippet--items"]` (bez té hlavičky vrátí nefiltrovaný seznam); přesný název obce dá
  `?do=citySuggestions&q=<Obec>`. Stránky „Prameny k poznávání vodních mlýnů“ na témže webu popisují, kde hledat dál
  (soupis mlýnů 1704, vodní knihy, kroniky mlynářských rodů). Údaje z karty ber jako odkaz na pramen, ne jako doklad –
  předka ověř v matrice / gruntovní knize.
- **Mapy stabilního katastru (1824–43)** – kde stál dům s číslem popisným: ags.cuzk.gov.cz/archiv (Archiv ČÚZK; stará adresa archivnimapy.cuzk.cz už nefunguje).
  Na **císařských otiscích** chybí u části listů barvy a čísla domů. Lepší jsou **indikační skici**: mají čísla domů
  a u pozemků jméno majitele („N. 13“ = patří k domu čp. 13). Dům bez pozemků mimo ves = domkář bez polí.
  Jméno majitele samotného domu bývá jen v písemném operátu (archiv, ne online). Výřezy map patří na web k rodině.
  - **Postup (jen v prohlížeči, služby jsou za tokenem – ten si stránka bere sama, nevypisuj ho):** na ags.cuzk.gov.cz/archiv
    najdi katastrální území, klikni do mapy na obec → „Indikační skici“ (nebo „Císařské povinné otisky“) → ID rastru
    (např. `HRA235018400`). Skica pak jde otevřít přímo: `https://ags.cuzk.gov.cz/archiv/openmap.html?typ=skicic&idrastru=<ID>`
    (list otisku `typ=cioc`); načítá se asi 20 s. Osada často nemá vlastní katastr (Polom → k. ú. Lhota u Dobrušky) –
    hledej podle sousední obce. Přibližuj kolečkem na bod, tažení myší mapu posouvá nevyzpytatelně.
  - **Morava:** odkaz vede do prohlížeče MZA (fond D 9, často dva listy: původní z 30. let a reambulace ze 70. let 19. stol.).
    MZA stahovací skripty zakazuje – jen přiblížit a snímek obrazovky (jako u matrik MZA). Listy Moravy nejsou georeferencované.
  - **Čtení:** v budově je **červeně číslo popisné** a **černě číslo stavební parcely** (pozemkové parcely mají čísla
    červená); záměna přečte celou ves obráceně. Při pochybnosti ověř na pár domech: vrstva pozemkového katastru
    (archiv_spojene_pk) s adresními body RÚIAN ukáže, na které parcele stojí dnešní čp. „N° 35 Příjmení“ u pozemku
    = patří k domu čp. 35.
    Žlutá stavba dřevěná, růžová zděná. Popisky bývají vzhůru nohama (výřez otoč o 180°). U měst bývá intravilán prázdný.
    Ulož jen snímkem obrazovky (stahování je placené) a na web dej výřez se zakroužkovaným domem.
- **Dnešní adresa domu** podle čísla popisného: RÚIAN (ČÚZK, vrstva AdresniMisto). Pozor, staré centrum mívá od 19. století
  stejná čp., ale předměstí a vesnice čísla přečíslovávaly. Hodí se na „procházku po stopách předků“.
  Stavbu podle obce a čísla popisného najde i nahlizenidokn.cuzk.gov.cz (ověření adresy z dokladu); vlastník je za
  CAPTCHou a je to údaj o žijícím člověku – nezjišťuj ho.

## Vězni koncentračních táborů, oběti, nuceně nasazení, vysídlení (2. světová válka a po ní)
**Postup:** nejdřív česká databáze (`vezni.py` – má i rodiště a transporty), pak Arolsen (nejširší), pak tábor, kde člověk zemřel.
Shoda jména není ztotožnění – jména se v táborových dokumentech píší různě (Novák/Nowak/Novak) a datum narození tam bývá chybné; ověř
datum a místo narození na kartě a v rodině. Údaje jsou citlivé – na web jen se souhlasem rodiny (`soukromi.md`).
- **Památník Terezín – databáze politicky a rasově pronásledovaných osob** – `tools/vezni.py`: `hledat --prijmeni Novák --jmeno Josef [--narozeni "15. 3. 1910"]`,
  `detail <odkaz>`. Čeští vězni v Buchenwaldu, Dachau, Flossenbürgu, Mauthausenu, Ravensbrücku, Malé pevnosti, na Pankráci, v ghettu a internačním táboře.
  Detail uvádí bydliště, kdo vězně předal, transporty a čísla, a **kde je originál** (často Národní archiv).
- **Arolsen Archives** – `tools/arolsen.py`: `hledat "Příjmení Jméno 1905"` (spojení „a zároveň“, hláskové varianty; portál dává po 1000 záznamech, další přes `--od 1000`),
  filtry `--misto-narozeni Praha`, `--rodne`, `--cislo <číslo vězně>`, `--narodnost Czech`, `--vyznani Jewish` (národnost a vyznání jen přesným názvem z portálu; při chybě nástroj vypíše nabídku),
  `--podrobne` (otec, matka, vyznání, povolání, místo věznění, poslední bydliště), `karta <id> pracovni/x.jpg`
  stáhne kartotéční kartu nebo dokument. Obsahuje kartotéky Dachau, Mauthausenu, Buchenwaldu, Flossenbürgu, Terezína, **část Osvětimi**, seznamy
  transportů, nuceně nasazené a poválečné **vysídlené osoby (DP)**. Datum narození je v databázi měsíc/den/rok (nástroj převádí). U Osvětimi
  (a dalších) chybějí v databázi zápisy, které se nedochovaly; nenalezení neznamená, že tam člověk nebyl.
- **Mauthausen – Raum der Namen** – `tools/mauthausen.py hledat "Novak"`: jen zemřelí v Mauthausenu a pobočkách (Gusen, Ebensee, Melk…), často s fotografiemi a životopisem.
- **Židé z českých zemí** – `tools/obeti.py` (holocaust.cz, Terezínská iniciativa): jméno, narození, poslední bydliště před deportací, transporty.
- **Osvětim**: databáze Muzea Auschwitz (victims.auschwitz.org) má na serveru neúplný certifikát, ze skillu proto nejde; ověř ji v prohlížeči.
  Pro české oběti: holocaust.cz, Památník Terezín (rodinný tábor Terezín v Birkenau) a Arolsen.
- **Dachau**: Gedenkstätte Dachau odpovídá na písemné dotazy o vězních (`kz-gedenkstaette-dachau.de` → Forschung und Sammlung → Anfrage zu Häftlingen);
  online kartotéka je v Arolsenu. **Další tábory** (Buchenwald, Flossenbürg, Ravensbrück, Sachsenhausen): Arolsen a stránky pamětníků jednotlivých táborů.
- **Vysídlení a odsun**: Arolsen (DP, nuceně nasazení – vyhledej v `arolsen.py`), Národní archiv (fondy o odsunu a o uprchlících z pohraničí 1938 – v katalogu
  na na.gov.cz), **Lastenausgleichsarchiv Bayreuth** a **Sudetendeutsches Archiv München** (kartotéky odsunutých, vyplácení náhrad – nevyzkoušeno,
  weby ze zkušebního prostředí nedostupné), **Paměť národa** (memoryofnations.eu – vzpomínky pamětníků na osídlování, odsun, tábory; nevyzkoušeno).
- **Popravení, vězni gestapa, odboj**: Národní archiv (fondy Policejní ředitelství, Gestapo, Mimořádný lidový soud), Památník Terezín (Malá pevnost), Ústav pro studium
  totalitních režimů (ustrcr.cz). Katalogy a kartotéky jsou jen částečně online – zapiš dotaz do `archivni_dotazy.md`.

## Příjmení dnes a DNA
- **Rozšíření příjmení dnes**: kdejsme.cz (počty nositelů po okresech). Rychle ukáže, jestli je příjmení vzácné a kde
  jsou jeho „hnízda“. Při hledání vzdálených příbuzných vyškrtni vlastní rodinu.
- **DNA** (jen když o to uživatel stojí, a jeho rozhodnutí): autosomální test (MyHeritage, Ancestry) najde bratrance
  do ~5. kolene. **Y-DNA** (FamilyTreeDNA, Y-37 až Big Y) se dědí po meči beze změny. Ověří, jestli dvě linie stejného
  příjmení mají společného předka, a u nemanželského dítěte může shoda s jiným příjmením ukázat otce. Kontakt se žijícími
  příbuznými vždy jen přes uživatele.
Všechno, co jde jen v badatelně, zapisuj do `data/archivni_dotazy.md` (archiv, fond, inventární číslo, co hledat).
