# WocaFuckOff

> **Automatizácia Wocabee. Menej klikania. Viac času.**

WocaFuckOff je experimentálny nástroj vytvorený na automatizáciu práce s platformou **Wocabee**.

Projekt je momentálne **aktívne vo vývoji**. Funkcie, používateľské rozhranie aj vnútorná architektúra sa môžu priebežne meniť.

---

## Stav projektu

**WocaFuckOff je momentálne vo fáze vývoja (Development).**

Projekt ešte nie je označený ako finálna release verzia. Niektoré funkcie môžu byť nedokončené, experimentálne alebo sa môžu správať inak, než sa očakáva.

Aktuálna verzia slúži predovšetkým na:

* vývoj nových funkcií,
* testovanie automatizácie,
* ladenie solvera,
* testovanie používateľského rozhrania,
* overovanie komunikácie s Wocabee,
* experimentovanie s ďalšími komponentmi projektu.

**Používanie vývojovej verzie je na vlastné riziko.**

---

# Funkcie

WocaFuckOff je navrhnutý ako automatizačný nástroj s viacerými komponentmi.

### Automatizácia

Program je schopný automatizovať vybrané časti práce s Wocabee a pracovať s aktuálnymi údajmi priamo počas behu programu.

### Solver

Hlavnou súčasťou projektu je `solver.py`, ktorý zabezpečuje spracovanie a riešenie úloh.

Solver je samostatná časť projektu a počas vývoja sa priebežne rozširuje a upravuje.

### Grafické rozhranie

Používateľské rozhranie zabezpečuje `gui.py`.

GUI poskytuje hlavné ovládanie aplikácie a postupne sa rozširuje o ďalšie možnosti konfigurácie a automatizácie.

### Správa aplikácie

`management.py` obsahuje pomocné funkcie a logiku súvisiacu so správou programu.

### Konfigurácia

Nastavenia aplikácie sú uložené v:


config.toml


Konfigurácia umožňuje oddeliť nastavenia programu od jeho hlavnej logiky.

---

# Štruktúra projektu

```text
WocaFuckOff/
│
├── assets/
│   └── Grafické a ďalšie zdroje aplikácie
│
├── .gitignore
├── config.toml
├── gui.py
├── installer.py
├── LICENSE
├── main.py
├── management.py
├── picturelist.json
├── README.md
├── requirements.txt
├── solver.py
└── wordlist.json
```

### Hlavné súbory

| Súbor              | Úloha                            |
| ------------------ | -------------------------------- |
| `main.py`          | Hlavný vstupný bod aplikácie     |
| `gui.py`           | Grafické používateľské rozhranie |
| `solver.py`        | Solver a riešenie úloh           |
| `management.py`    | Pomocná a riadiaca logika        |
| `installer.py`     | Inštalačné/pomocné funkcie       |
| `config.toml`      | Konfigurácia aplikácie           |
| `wordlist.json`    | Dáta slovníka                    |
| `picturelist.json` | Dáta súvisiace s obrázkami       |
| `requirements.txt` | Python závislosti                |
| `assets/`          | Grafické a ostatné zdroje        |
| `LICENSE`          | Licencia projektu                |

---

# Spustenie

## Požiadavky

Pre vývojovú verziu je potrebný:

* **Python 3**
* nainštalované závislosti z `requirements.txt`

Závislosti je možné nainštalovať pomocou:

```bash
pip install -r requirements.txt
```

---

## Spustenie aplikácie

Aktuálne sa WocaFuckOff spúšťa priamo cez hlavný súbor:

```bash
python main.py
```

Prípadne vo Windows:

```bash
py main.py
```


### Dôležité

**`main.py` je aktuálny vstupný bod aplikácie.**

Samostatný `.exe` build zatiaľ nie je hlavný spôsob spúšťania projektu. Kompilácia do `.exe` môže byť pridaná neskôr počas vývoja.

---

# Vývoj

WocaFuckOff je momentálne **Development build**.

Projekt sa aktívne vyvíja a jednotlivé časti sa môžu meniť bez zachovania spätnej kompatibility.

Počas vývoja môžu byť pridané alebo upravené napríklad:

* nové možnosti automatizácie,
* nové typy úloh,
* vylepšenia solvera,
* automatický preklad,
* nové nastavenia,
* úpravy GUI,
* lepšie spracovanie chýb,
* optimalizácia výkonu,
* stabilnejšia práca s Wocabee,
* ďalšie pomocné funkcie.

---

# Architektúra

Projekt je rozdelený na viacero samostatných komponentov.

```text
                 WocaFuckOff
                      │
                      ▼
                   main.py
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        gui.py    management.py  solver.py
          │                       │
          ▼                       ▼
       Ovládanie              Spracovanie
       aplikácie               úloh
          │                       │
          └───────────┬───────────┘
                      ▼
                  Wocabee
```

Takéto rozdelenie umožňuje vyvíjať jednotlivé časti projektu nezávisle od seba a zároveň zachovať prehľadnú štruktúru zdrojového kódu.

---

# Konfigurácia

Konfiguračné údaje sa nachádzajú v:

```text
config.toml
```

Konfiguračný súbor je oddelený od zdrojového kódu, aby bolo možné meniť nastavenia bez potreby upravovať hlavné Python súbory.

Počas vývoja sa môže formát konfigurácie meniť.

---

# Protokolovanie

Počas vývoja môže aplikácia vytvárať logovacie údaje určené na diagnostiku a ladenie.

Vývojové logy nie sú považované za nevyhnutnú súčasť zdrojového kódu a môžu byť odstránené alebo znovu vytvorené pri ďalšom spustení aplikácie.

---

# Bezpečnosť a údaje

WocaFuckOff je vývojový projekt.

Pri testovaní je potrebné počítať s tým, že:

* aplikácia nemusí vždy správne spracovať neočakávané údaje,
* experimentálne funkcie môžu obsahovať chyby,
* zmeny na strane Wocabee môžu ovplyvniť funkčnosť programu,
* vývojová verzia nemusí poskytovať rovnakú stabilitu ako budúca release verzia.

Nepoužívajte citlivé údaje v konfiguračných súboroch ani ich nezverejňujte v repozitári.

---

# Licencia

Tento projekt je distribuovaný pod licenciou uvedenou v súbore:

```text
LICENSE
```

Pred použitím, úpravou alebo distribúciou projektu si prečítajte podmienky tejto licencie.

---

# Disclaimer

WocaFuckOff je **nezávislý komunitný/vývojový projekt**.

Projekt nie je oficiálnym produktom spoločnosti Wocabee ani jej prevádzkovateľa, pokiaľ nie je výslovne uvedené inak.

Názvy a ochranné známky tretích strán patria ich príslušným vlastníkom.

---

# Roadmap

Projekt je stále vo vývoji. Plánované zmeny sa môžu meniť podľa priebehu vývoja.

### Aktuálne priority

* [x] Základ aplikácie
* [x] Hlavný vstup cez `main.py`
* [x] Základ GUI
* [x] Základ solvera
* [x] Konfiguračný systém
* [x] Práca s dátami
* [ ] Ďalšie rozšírenie solvera
* [ ] Ďalšie vylepšenia GUI
* [ ] Stabilizácia aplikácie
* [ ] Rozšírenie automatizácie
* [ ] Finálne testovanie
* [ ] Release build
* [ ] `.exe` distribúcia

---

# Vývojový stav

```text
┌──────────────────────────────────────┐
│          WocaFuckOff                 │
│                                      │
│          DEVELOPMENT                 │
│                                      │
│     Aktívne vo vývoji                │
│     Nie je finálna release verzia    │
│                                      │
└──────────────────────────────────────┘
```

Ak narazíte na chybu, neočakávané správanie alebo nefunkčnú časť aplikácie, môže ísť o známu vlastnosť vývojovej verzie.

---

# Autorstvo

WocaFuckOff vzniká ako samostatný vývojový projekt.

Jednotlivé časti projektu môžu mať odlišný pôvod a autorstvo. Informácie o licenciách a autoroch jednotlivých komponentov sa nachádzajú v príslušných súboroch projektu.

---

## Začiatok

Ak chcete projekt spustiť, stačí:

```bash
pip install -r requirements.txt
python main.py
```

**WocaFuckOff sa momentálne vyvíja. Finálna verzia, stabilný release a `.exe` distribúcia budú riešené neskôr.**
