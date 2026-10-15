# WocaFuckOff 1.2

**Menej klikania. Viac času.**

WocaFuckOff je desktopová aplikácia pre Windows na automatizáciu precvičovania vo WocaBee. V jednom rozhraní spája výber balíčkov, spustenie riešenia, prehľad WocaPoints a nastavenia automatizácie.

## Čo aplikácia ponúka

- **Balíčky z WocaBee** — načítanie balíčkov, rozpoznanie dokončených a výber konkrétneho balíčka na precvičovanie.
- **Automatické riešenie** — práca s lokálnym slovníkom a obrázkovým slovníkom, voliteľne s AutoTranslate cez Microsoft Azure Translator.
- **Prehľad WocaPoints** — načítanie bodov po prihlásení a počas riešenia.
- **Nastaviteľné spúšťanie** — beh na pozadí alebo so zobrazeným prehliadačom a možnosť používať Double Points.
- **Prispôsobiteľné rozhranie** — farebné témy, plynulé posúvanie a prehľad udalostí.
- **Aktualizácie z GitHubu** — automatická aj ručná kontrola, s potvrdením pred stiahnutím a inštaláciou.
- **Voliteľné oznámenia** — odosielanie stavu cez vlastné nastavenie ntfy.

## Inštalácia

Potrebuješ Windows, internetové pripojenie a účet WocaBee.

1. Spusti `WocaFuckOff-Setup.exe`.
2. Dokonči inštaláciu a otvor WocaFuckOff.
3. Zadaj prihlasovacie údaje do WocaBee. Aplikácia ich pred uložením overí.
4. V menu **Balíčky** vyber balíček a na hlavnej obrazovke stlač **SPUSTIŤ**.

Inštalátor obsahuje aplikáciu aj Chromium. Pri použití hotového inštalátora nemusíš samostatne pripravovať Python ani vývojové knižnice.

> **Inštalácia aj aktualizácia resetujú lokálne dáta aplikácie.** Po úspešnej inštalácii sa vymaže priečinok `%LOCALAPPDATA%\WocaFuckOff`, vrátane uloženého prihlásenia, nastavení, slovníkov, cache a profilov prehliadača. Ak ich chceš zachovať, pred inštaláciou si tento priečinok zálohuj. Ďalšie spustenie vyžiada nové prihlásenie.

Aplikácia sa inštaluje do `%LOCALAPPDATA%\Programs\WocaFuckOff`.

## Novinky vo verzii 1.2

- Podpora nového kartového zobrazenia balíčkov WocaBee aj pôvodného tabuľkového rozhrania.
- Výber tlačidla **Precvičiť** podľa ID balíčka, ignorovanie skrytých kariet a rozpoznanie dokončených balíčkov podľa zelených hexagónov.
- Overovanie prihlásenia v samostatnom procese s indikátorom priebehu. Nesprávne údaje sa neuložia a formulár umožní ich opravu.
- Načítanie WocaPoints z nového rozhrania WocaBee.
- Upravené okná, animácie, bočné menu a inštalátor so zjednoteným vzhľadom.
- Kontrola veľkosti a SHA-256 stiahnutého inštalátora. Inštalácia aktualizácie sa pri prebiehajúcej automatizácii odloží.

## Nastavenia a AutoTranslate

V **Nastaveniach** môžeš zmeniť tému, zobrazenie prehliadača, Double Points, AutoTranslate, prihlasovacie údaje a automatickú kontrolu aktualizácií.

AutoTranslate vyžaduje API kľúč služby **Microsoft Azure Translator**. Aplikácia ho vyhľadáva v tomto poradí:

1. Premenná prostredia `AZURE_TRANSLATOR_KEY`.
2. Správca poverení Windows — `WocaFuckOff/AzureTranslator`.
3. Hodnota `azure_translator_key` v konfigurácii.
4. Predvolená hodnota v riešiacej časti aplikácie, ak je dostupná.

Predvolený región prekladača je `northeurope` a cieľový jazyk `sk`. Poverenie uložené v Správcovi poverení Windows zostáva mimo priečinka resetovaného inštalátorom.

## Dáta a súkromie

WocaFuckOff nevyžaduje vlastný účet a nemá vlastnú telemetriu ani cloudovú synchronizáciu. Prihlasovacie údaje, nastavenia, slovníky a história sa ukladajú lokálne do `%LOCALAPPDATA%\WocaFuckOff`.

Sieťové spojenia závisia od používaných funkcií:

| Služba | Účel |
| --- | --- |
| WocaBee | Overenie prihlásenia, načítanie triedy, balíčkov a bodov, precvičovanie. |
| Microsoft Azure Translator | Preklad textu pri zapnutom AutoTranslate. |
| GitHub | Kontrola a sťahovanie aktualizácií. |
| Nastavený server ntfy | Voliteľné odosielanie stavu. |

## Aktualizácie

Aplikácia kontroluje stabilné vydania repozitára `alf3x41/wocafuckoff`. Automatickú kontrolu po štarte možno vypnúť; ručná kontrola je dostupná v Nastaveniach. Rovnaká verzia sa ako aktualizácia neponúkne.

Stiahnutie a inštalácia vyžadujú potvrdenie. Pred spustením inštalátora sa overí jeho veľkosť a SHA-256.

Pre vydanie 1.2 sa používa tag `v1.2` a príloha `WocaFuckOff-Setup.exe`. Aktualizátor vyžaduje SHA-256 digest prílohy poskytovaný GitHubom. Prístup k súkromnému repozitáru podporuje cez lokálne poverenie `WocaFuckOff/GitHub`.

## Licencia a distribúcia

WocaFuckOff je proprietárna aplikácia distribuovaná iba ako hotový súbor `.exe`. Zdrojový kód nie je verejne sprístupnený. Používanie aplikácie upravujú [licenčné podmienky](LICENCE).

## Riešenie problémov

- **Prihlásenie zlyhá:** skontroluj údaje a pripojenie. Pri dočasnom zablokovaní prihlasovania počkaj a skús to znova.
- **Balíček sa nespustí:** obnov jeho výber v menu Balíčky a pozri si Udalosti. Pri chýbajúcom alebo nejednoznačnom ID aplikácia nevyberie náhradný balíček.
- **AutoTranslate nefunguje:** over API kľúč a región Azure Translator.
- **Aktualizácia sa neponúka:** over dostupnosť novšieho stabilného vydania a jeho inštalačnej prílohy s SHA-256 digestom.

Kompatibilita s novým zoznamom balíčkov bola overovaná na lokálnych HTML ukážkach. Toto overenie nezahŕňa celý priebeh precvičovania na živom účte WocaBee; zmeny jeho webového rozhrania môžu vyžadovať ďalšiu úpravu aplikácie.

---

© 2026 Alex Polák. Všetky práva vyhradené.

