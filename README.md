WocaFuckOff 1.4

**Menej klikania. Viac času.**

WocaFuckOff je desktopová aplikácia pre Windows na automatizáciu precvičovania vo Wocabee. V jednom rozhraní spája výber balíčkov, spustenie riešenia, prehľad WocaPoints a nastavenia automatizácie.

## Čo aplikácia ponúka

- **Balíčky z Wocabee** — načítanie balíčkov, rozpoznanie dokončených a výber konkrétneho balíčka na precvičovanie.
- **Automatické riešenie** — práca s lokálnym slovníkom a obrázkovým slovníkom, voliteľne s pripravenou funkciou AutoTranslate cez API autora.
- **Prehľad WocaPoints** — načítanie bodov po prihlásení a počas riešenia.
- **Nastaviteľné spúšťanie** — beh na pozadí alebo so zobrazeným prehliadačom a možnosť používať Double Points.
- **Prispôsobiteľné rozhranie** — farebné témy, plynulé posúvanie a prehľad udalostí.
- **Aktualizácie z GitHubu** — automatická aj ručná kontrola, s potvrdením pred stiahnutím a inštaláciou.
- **Voliteľné oznámenia** — odosielanie stavu cez vlastné nastavenie ntfy.

## Inštalácia

Potrebuješ 64-bitový Windows, internetové pripojenie a účet Wocabee.

1. Spusti `WocaFuckOff-Setup.exe`.
2. Dokonči inštaláciu a otvor WocaFuckOff.
3. Zadaj prihlasovacie údaje do Wocabee. Aplikácia ich pred uložením overí.
4. V ľavom menu otvor **Balíčky**, vyber balíček a na hlavnej obrazovke stlač **SPUSTIŤ**.

Inštalátor obsahuje aplikáciu aj Chromium. Pri použití hotového inštalátora nemusíš samostatne pripravovať Python ani vývojové knižnice.

> **Inštalácia aj aktualizácia zachovávajú lokálne dáta aplikácie**, vrátane prihlásenia, nastavení, slovníkov, cache a profilov prehliadača v `%LOCALAPPDATA%\WocaFuckOff`.

Aplikácia sa inštaluje do `%LOCALAPPDATA%\Programs\WocaFuckOff`.

## Novinky vo verzii 1.4

- **Aktualizácia jedným potvrdením:** pri novej verzii stačí kliknúť na **Nainštalovať**. Aplikácia aktualizáciu stiahne, overí a nainštaluje potichu.
- **Zachovanie dát:** inštalátor už nemaže prihlásenie, nastavenia, slovníky, cache ani profily prehliadača. Tichá aktualizácia zachová aj vybraný jazyk.
- **Viditeľný priebeh:** počas sťahovania a inštalácie sa zobrazuje existujúce animované načítavacie koliesko. Po úspešnej aktualizácii sa aplikácia automaticky znovu spustí.
- **Bezpečné odovzdanie inštalácie:** pomocný proces počká na ukončenie aplikácie a uvoľnenie jej súborov. Overenie veľkosti a SHA-256 zostáva zachované; pri chybe sa zobrazí upozornenie.
- **Opravené číslo verzie v inštalátore:** číslo 1.4 sa vykresľuje spolu s bodkou ako jeden text, bez neprirodzených medzier.
- **Zjednotený Cancel:** tlačidlo zrušenia vo výbere jazyka má rovnakú farbu povrchu ako Cancel na hlavnej obrazovke inštalátora.
- **Zrušenie inštalácie v jednom okne:** potvrdenie sa zobrazí priamo v pôvodnom okne; nevytvára druhé prekrývajúce sa okno. Tlačidlo Continue a kláves Escape vrátia používateľa späť.
- **Modernejšie bočné menu:** zaoblené tlačidlá, zjednotené rozostupy, zarovnané ikony a názvy, zvýraznenie pri prejdení myšou, stlačení aj ovládaní klávesnicou.
- **Verzia 1.4** v aplikácii, inštalátore a vlastnostiach EXE; aktualizovaný popis aktualizácií v Nastaveniach.

Podrobnosti a pokyny k prechodu zo starších verzií: [poznámky k vydaniu 1.4](RELEASE_1.4.md).

## Nastavenia a AutoTranslate

### Jazyk rozhrania

Inštalátor pri prvom spustení predvolí jazyk podľa zobrazovacieho jazyka Windows. Pod tlačidlami zobrazuje jeho konkrétny názov; kliknutím otvoríš ponuku jazykov. Voľba sa odovzdá aplikácii a dá sa neskôr zmeniť v **Nastavenia → Jazyk** bez reštartu a bez zastavenia automatizácie. Ani jedna ponuka nezobrazuje položku „System default“.

Podporované jazyky: slovenčina, angličtina, čeština, nemčina, francúzština, španielčina, taliančina, portugalčina, poľština, maďarčina, ukrajinčina, ruština, zjednodušená čínština, japončina, kórejčina, turečtina, arabčina a hindčina. Pri nepodporovanom systémovom jazyku sa použije angličtina. Arabčina používa rozloženie sprava doľava.

Prekladové súbory sú pribalené a fungujú bez internetu. Kontroly overujú úplné pokrytie katalógov, neprázdne texty a zachovanie premenných aj formátovania. Dlhšie texty vychádzajú zo strojových prekladov; úplná odborná jazyková korektúra všetkých jazykov nebola vykonaná. Názvy vlastných balíčkov, prihlasovacie údaje a jazyk precvičovania sa pri prepnutí rozhrania nemenia.

V **Nastaveniach** môžeš zmeniť tému, zobrazenie prehliadača, Double Points, AutoTranslate, prihlasovacie údaje a automatickú kontrolu aktualizácií.

AutoTranslate je už integrovaný a pripravený na používanie cez API autora. Napojenie je šifrované a používateľ nemusí zadávať vlastný API kľúč ani nastavovať prekladovú službu. Funkciu stačí zapnúť v Nastaveniach.

## Dáta a súkromie

WocaFuckOff nevyžaduje vlastný účet a nemá vlastnú telemetriu ani cloudovú synchronizáciu. Prihlasovacie údaje, nastavenia, slovníky a história sa ukladajú lokálne do `%LOCALAPPDATA%\WocaFuckOff`.

Sieťové spojenia závisia od používaných funkcií:

| Služba | Účel |
| --- | --- |
| Wocabee | Overenie prihlásenia, načítanie triedy, balíčkov a bodov, precvičovanie. |
| API autora (AutoTranslate) | Spracovanie prekladaného textu pri zapnutom AutoTranslate. |
| GitHub | Kontrola a sťahovanie aktualizácií. |
| Nastavený server ntfy | Voliteľné odosielanie stavu. |

## Aktualizácie

Aplikácia kontroluje stabilné vydania repozitára `alf3x41/wocafuckoff`. Automatickú kontrolu po štarte možno vypnúť; ručná kontrola je dostupná v Nastaveniach. Rovnaká verzia sa ako aktualizácia neponúkne.

Po oznámení novej verzie stačí kliknúť na **Nainštalovať**. Počas sťahovania a tichej inštalácie sa zobrazuje načítavacie koliesko. Pred spustením inštalátora sa overí jeho veľkosť a SHA-256. Aplikácia sa po úspešnej aktualizácii automaticky spustí; uložené dáta zostanú zachované.

Pre vydanie 1.4 sa používa tag `v1.4` a príloha `WocaFuckOff-Setup.exe`. Aktualizátor vyžaduje SHA-256 digest prílohy poskytovaný GitHubom. Prístup k súkromnému repozitáru podporuje cez lokálne poverenie `WocaFuckOff/GitHub`.

## Licencia a distribúcia

WocaFuckOff je proprietárna aplikácia distribuovaná iba ako hotový súbor `.exe`. Zdrojový kód nie je verejne sprístupnený. Používanie aplikácie upravujú [licenčné podmienky](LICENCE).

## Riešenie problémov

- **Prihlásenie zlyhá:** skontroluj údaje a pripojenie. Pri dočasnom zablokovaní prihlasovania počkaj a skús to znova.
- **Balíček sa nespustí:** otvor **Balíčky** v ľavom menu, obnov jeho výber a pozri si Udalosti. Pri chýbajúcom alebo nejednoznačnom ID aplikácia nevyberie náhradný balíček.
- **AutoTranslate nefunguje:** skontroluj, či je funkcia zapnutá, internetové pripojenie a hlásenia v Udalostiach. Pri nedostupnosti API skús preklad neskôr.
- **Aktualizácia sa neponúka:** over dostupnosť novšieho stabilného vydania a jeho inštalačnej prílohy s SHA-256 digestom.
- **Staršia verzia hlási neplatnú adresu inštalátora:** stiahni inštalátor 1.4 ručne z GitHub Releases. Chybu spôsobovala kontrola veľkých a malých písmen v názve repozitára; starý aktualizátor ju nedokáže sám obísť.

Kompatibilita s novým zoznamom balíčkov bola overovaná na lokálnych HTML ukážkach. Toto overenie nezahŕňa celý priebeh precvičovania na živom účte Wocabee; zmeny jeho webového rozhrania môžu vyžadovať ďalšiu úpravu aplikácie.

---

© 2026 Alex Polák. Všetky práva vyhradené.


