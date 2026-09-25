# SOLVER.PY

# -*- coding: utf-8 -*-

# IMPORTY

import argparse

import json

import os

import sys
import re

import time

import traceback

import unicodedata

from pathlib import Path

import requests

import toml

from playwright.sync_api import sync_playwright



# VÝSTUP V UTF-8

try:

    sys.stdout.reconfigure(encoding="utf-8")

    sys.stderr.reconfigure(encoding="utf-8")

except Exception:

    pass

# CESTY A NASTAVENIA

BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "config.toml"

try:

    config = toml.load(CONFIG_FILE)

except Exception as chyba:

    print(f"CHYBA: Nepodarilo sa načítať config.toml: {chyba}", flush=True)

    config = {}

URLBASE = config.get("urlbase", "https://wocabee.app/app")

DEBUG_PORT = str(config.get("debug_port", "9222")).strip()

WORDLIST_FILE = config.get("wordlist_file", "wordlist.json")

PICTURE_FILE = config.get("picture_file", "picturelist.json")

PLACEHOLDER_WORDS = config.get("placeholder_words", ["", "translate", "check"])

CLASS_INDEX = int(config.get("class_index", 0))

HEADLESS = bool(config.get("headless", True))

DOUBLE_POINTS = bool(config.get("double_points", False))

ADDON_POINTS = int(config.get("addon_points", 1000))

LAST_POINTS = int(config.get("last_points", 0))

AUTO_TRANSLATE = bool(config.get("auto_translate", True))

NTFY_SERVER = str(config.get("ntfy_server", "")).strip()

NTFY_TOPIC = str(config.get("ntfy_topic", "")).strip()

NTFY_TOKEN = str(config.get("ntfy_token", "")).strip()

# AZURE TRANSLATOR

AZURE_TRANSLATOR_KEY = (

    os.environ.get("AZURE_TRANSLATOR_KEY")
    or config.get("azure_translator_key", "")

).strip()

AZURE_TRANSLATOR_REGION = (

    os.environ.get("AZURE_TRANSLATOR_REGION")
    or config.get("azure_translator_region", "northeurope")

).strip().lower()

AZURE_TRANSLATOR_URL = (

    "https://api.cognitive.microsofttranslator.com/translate"

)





# VYPISOVANIE SPRÁV

def log(sprava=""):

    print(sprava, flush=True)





# SLOVNÍK

VYCHODISKOVE_SLOVA = {

    "pracovny postup": "technique",

    "viditelny": "visible",

    "vazny": "serious",

    "seriozny": "serious",

    "vazny, seriozny": "serious",

    "vedecke laboratorium": "science laboratory",

    "krok": "step",

    "vyznam, zmysel": "significance",

    "burka": "storm",

}





def nacitaj_slovnik():

    cesta = BASE_DIR / WORDLIST_FILE

    if not cesta.exists():

        try:

            with open(cesta, "w", encoding="utf-8") as subor:

                json.dump(VYCHODISKOVE_SLOVA, subor, ensure_ascii=False, indent=2)

        except Exception as chyba:

            log(f"Nepodarilo sa vytvoriť slovník: {chyba}")

        return dict(VYCHODISKOVE_SLOVA)

    try:

        with open(cesta, "r", encoding="utf-8") as subor:

            udaje = json.load(subor)

        if isinstance(udaje, dict):

            return udaje

    except Exception as chyba:

        log(f"Nepodarilo sa načítať slovník: {chyba}")

    return dict(VYCHODISKOVE_SLOVA)





SLOVNIK = nacitaj_slovnik()





def uloz_slovnik():

    cesta = BASE_DIR / WORDLIST_FILE

    try:

        with open(cesta, "w", encoding="utf-8") as subor:

            json.dump(SLOVNIK, subor, ensure_ascii=False, indent=2)

        return True

    except Exception as chyba:

        log(f"Nepodarilo sa uložiť slovník: {chyba}")

        return False





# SLOVNÍK OBRÁZKOV

def nacitaj_obrazkovy_slovnik():

    cesta = BASE_DIR / PICTURE_FILE

    if not cesta.exists():

        return {}

    try:

        with open(cesta, "r", encoding="utf-8") as subor:

            udaje = json.load(subor)

        if isinstance(udaje, dict):

            return udaje

    except Exception as chyba:

        log(f"Nepodarilo sa načítať obrázkový slovník: {chyba}")

    return {}





OBRAZKY = nacitaj_obrazkovy_slovnik()





def uloz_obrazkovy_slovnik():

    cesta = BASE_DIR / PICTURE_FILE

    try:

        with open(cesta, "w", encoding="utf-8") as subor:

            json.dump(OBRAZKY, subor, ensure_ascii=False, indent=2)

        return True

    except Exception as chyba:

        log(f"Nepodarilo sa uložiť obrázkový slovník: {chyba}")

        return False





# NORMALIZÁCIA TEXTU

def normalize(text):

    if text is None:

        return ""

    text = str(text).strip().lower()

    text = unicodedata.normalize("NFD", text)

    text = "".join(znak for znak in text if unicodedata.category(znak) != "Mn")

    return " ".join(text.split())





# WOCA POINTS

def get_points(page):
    try:
        counter = page.locator("#WocaPoints:visible").first
        if counter.count():
            digits = "".join(c for c in counter.inner_text(timeout=500) if c.isdigit())
            return int(digits) if digits else None
        # V menu čítame skóre v kontexte, nie ľubovoľné číslo v <b>.
        text = page.locator("body").inner_text(timeout=500)
        match = re.search(r"Tvoje\s+skóre:\s*([0-9][0-9\s.,]*)", text, re.IGNORECASE)
        if match:
            return int(re.sub(r"[^0-9]", "", match.group(1)))
    except Exception:
        pass
    return None



def vycisti_preklad(text):

    if not text:

        return ""

    text = str(text).strip()

    text = text.replace("\n", " ").strip()

    if len(text) >= 2:

        if text[0] == '"' and text[-1] == '"':

            text = text[1:-1].strip()

        elif text[0] == "'" and text[-1] == "'":

            text = text[1:-1].strip()

    return text





def preklad_je_platny(original, prelozeny):

    original = vycisti_preklad(original)

    prelozeny = vycisti_preklad(prelozeny)

    if not prelozeny:

        return False

    # Preklad nesmie byť úplne rovnaký ako pôvodné slovo.

    if prelozeny.casefold() == original.casefold():

        return False

    # Ochrana pred nezmyselne dlhou odpoveďou.

    if len(prelozeny) > 500:

        return False

    pocet_pismen = sum(znak.isalpha() for znak in prelozeny)

    if pocet_pismen < 2:

        return False

    if pocet_pismen < max(2, len(prelozeny) // 3):

        return False

    return True





# Jedna požiadavka na pozadí, bez rastúceho radu starých otázok.
from concurrent.futures import ThreadPoolExecutor

AZURE_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="azure")
AZURE_ULOHA = None
AZURE_CACHE = {}
AZURE_CHYBY = {}
AZURE_PAUSE = 0.0


def preloz_cez_azure(text, cielovy_jazyk, zdrojovy_jazyk=None):
    """Vracia (preklad, zdroj). Pri explicitnom from Azure neposiela detekciu."""
    global AZURE_PAUSE
    text = vycisti_preklad(text)
    if not text or time.monotonic() < AZURE_PAUSE:
        return "", ""
    if not AZURE_TRANSLATOR_KEY:
        log("CHYBA[AZURE_KEY]: AutoTranslate nefunguje: chýba Azure API kľúč.")
        AZURE_PAUSE = float("inf")
        return "", ""
    ciel = cielovy_jazyk.lower()
    params = {"api-version": "3.0", "to": ciel}
    if zdrojovy_jazyk:
        params["from"] = zdrojovy_jazyk.lower()
    headers = {"Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
               "Content-Type": "application/json"}
    if AZURE_TRANSLATOR_REGION and AZURE_TRANSLATOR_REGION != "global":
        headers["Ocp-Apim-Subscription-Region"] = AZURE_TRANSLATOR_REGION
    try:
        odpoved = requests.post(AZURE_TRANSLATOR_URL, params=params, headers=headers,
                                json=[{"text": text}], timeout=(3, 7))
        if odpoved.status_code != 200:
            status = odpoved.status_code
            if status in (401, 403):
                AZURE_PAUSE = float("inf")
                log(f"CHYBA[AZURE_KEY]: AutoTranslate nefunguje: neplatný kľúč alebo región (HTTP {status}).")
            elif status == 429:
                try:
                    prestavka = max(5.0, float(odpoved.headers.get("Retry-After", "30")))
                except (ValueError, TypeError):
                    prestavka = 30.0
                AZURE_PAUSE = time.monotonic() + prestavka
                log(f"CHYBA[AZURE_LIMIT]: AutoTranslate prekročil Azure API limit; ďalší pokus o {prestavka:.0f} s.")
            else:
                try:
                    prestavka = max(5.0, float(odpoved.headers.get("Retry-After", "30")))
                except (ValueError, TypeError):
                    prestavka = 30.0
                AZURE_PAUSE = time.monotonic() + prestavka
                log(f"CHYBA[AZURE_API]: Azure API vrátilo HTTP {status}; ďalší pokus o {prestavka:.0f} s.")
            return "", ""
        data = odpoved.json()
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            raise ValueError("Neplatná odpoveď Azure")
        zaznam = data[0]
        detekcia = zaznam.get("detectedLanguage") or {}
        zdroj = zdrojovy_jazyk or detekcia.get("language", "")
        for preklad in zaznam.get("translations", []):
            if isinstance(preklad, dict) and preklad.get("to", "").lower() == ciel:
                vysledok = vycisti_preklad(preklad.get("text", ""))
                # Rovnaké a jednopísmenové slová môžu byť správne (hotel, a, I).
                if vysledok and len(vysledok) <= 500 and any(c.isalpha() for c in vysledok):
                    return vysledok, zdroj.lower()
        return "", zdroj.lower()
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        AZURE_PAUSE = time.monotonic() + 15
        log("CHYBA[AZURE_CONNECTION]: AutoTranslate sa nevie pripojiť k Azure API alebo endpointu; ďalší pokus o 15 s.")
        return "", ""


def azure_zvieraci_balik():
    """Kontext len z názvu skutočne vybraného balíka."""
    try:
        baliky = json.loads(config.get("packages_cache", "[]"))
        vybrany = str(config.get("selected_package_id", ""))
        for balik in baliky:
            if str(balik.get("id", "")) == vybrany:
                nazov = normalize(balik.get("name", ""))
                return any(slovo in nazov for slovo in ("bird", "vtak", "animal", "zvier"))
    except (ValueError, TypeError, AttributeError):
        pass
    return False


def azure_preloz_sync(slovo):
    # Najprv preklad do SK; detekcia samostatného slova môže označiť aj tretí jazyk.
    preklad, zdroj = preloz_cez_azure(slovo, "sk")
    if not preklad:
        return ""
    if zdroj == "sk":
        preklad, _ = preloz_cez_azure(slovo, "en", "sk")
        ciel = "en"
    else:
        ciel = "sk"
        if zdroj != "en":
            preklad, _ = preloz_cez_azure(slovo, "sk", "en")
        zdroj = "en"
        # Člen pomáha izolovaným podstatným menám: duck, hen; pri zvieracom
        # balíku aj turkey (moriak), ktoré by inak znamenalo krajinu.
        if (preklad and re.fullmatch(r"[A-Za-z]{2,40}", slovo)
                and (preklad.casefold() == slovo.casefold() or azure_zvieraci_balik())):
            s_kontextom, _ = preloz_cez_azure("the " + slovo, "sk", "en")
            if not s_kontextom:
                return ""
            if not s_kontextom.casefold().startswith("the "):
                preklad = s_kontextom
        if preklad and preklad.casefold() == slovo.casefold():
            opacne, _ = preloz_cez_azure(slovo, "en", "sk")
            if opacne and opacne.casefold() != slovo.casefold():
                preklad, zdroj, ciel = opacne, "sk", "en"
    if preklad:
        log(f"Azure Translator: {zdroj.upper()} -> {ciel.upper()}: {slovo} -> {preklad}")
    return preklad


def automaticky_preloz_slovo(slovo):
    global AZURE_ULOHA
    slovo = vycisti_preklad(slovo)
    if not slovo:
        return ""
    if AZURE_ULOHA is not None and AZURE_ULOHA[1].done():
        povodne, future = AZURE_ULOHA
        try:
            preklad = future.result()
        except Exception:
            log("Azure: preklad sa nepodaril; pokračujem v sledovaní úloh.")
            preklad = ""
        if preklad:
            AZURE_CACHE[povodne] = preklad
        else:
            AZURE_CHYBY[povodne] = time.monotonic() + 30
        AZURE_ULOHA = None
    if slovo in AZURE_CACHE:
        return AZURE_CACHE[slovo]
    if time.monotonic() < max(AZURE_PAUSE, AZURE_CHYBY.get(slovo, 0)):
        return ""
    if AZURE_ULOHA is None:
        AZURE_ULOHA = (slovo, AZURE_EXECUTOR.submit(azure_preloz_sync, slovo))
    return ""





# HĽADANIE ODPOVEDE

def get_answer_auto_update(slovo):

    slovo = vycisti_preklad(slovo)

    if not slovo:

        return ""

    normalizovane_slovo = normalize(slovo)

    # 1. Presná zhoda v slovníku

    if slovo in SLOVNIK:

        return SLOVNIK[slovo]

    # 2. Zhoda bez diakritiky

    for otazka, odpoved in SLOVNIK.items():

        if normalize(otazka) == normalizovane_slovo:

            return odpoved

    # 3. Obrázkový slovník

    if slovo in OBRAZKY:

        return OBRAZKY[slovo]

    for otazka, odpoved in OBRAZKY.items():

        if normalize(otazka) == normalizovane_slovo:

            return odpoved

    # 4. Obrátené vyhľadávanie

    for otazka, odpoved in SLOVNIK.items():

        if normalize(odpoved) == normalizovane_slovo:

            return otazka

    # 5. Varianty oddelené čiarkou

    for otazka, odpoved in SLOVNIK.items():

        casti_otazky = [normalize(cast) for cast in str(otazka).split(",")]

        casti_odpovede = [normalize(cast) for cast in str(odpoved).split(",")]

        if normalizovane_slovo in casti_otazky:

            return odpoved

        if normalizovane_slovo in casti_odpovede:

            return otazka

    # Návrhy Azure sú iba v pamäťovej cache; opravy z úloh majú prednosť.
    if AUTO_TRANSLATE:
        return automaticky_preloz_slovo(slovo)

    # GUI nemá interaktívny stdin. input() by tu zastavil celý riešič.
    return ""





# NTFY OZNÁMENIA

def posli_ntfy(sprava):

    if not NTFY_SERVER or not NTFY_TOPIC:

        return

    try:

        url = NTFY_SERVER.rstrip("/") + "/" + NTFY_TOPIC

        hlavicky = {}

        if NTFY_TOKEN:

            hlavicky["Authorization"] = f"Bearer {NTFY_TOKEN}"

        requests.post(

            url, data=str(sprava).encode("utf-8"), headers=hlavicky, timeout=10

        )

    except Exception as chyba:

        log(f"Chyba NTFY: {chyba}")





# HĽADANIE KARTY WOCA BEE

def najdi_cielovu_stranku(kontext):

    for stranka in kontext.pages:

        try:

            url = stranka.url.lower()

            if "wocabee.app" in url:

                return stranka

        except Exception:

            pass

    if kontext.pages:

        return kontext.pages[0]

    return None





# VÝBER OBRÁZKA

def spracuj_vyber_obrazka(stranka):

    try:

        tlacidla = stranka.locator("button:visible")

        pocet = tlacidla.count()

        if pocet == 0:

            return False

        text_stranky = stranka.locator("body").inner_text(timeout=500)

        dolny_text = text_stranky.lower()

        if "vyber obrázok" not in dolny_text and "choose picture" not in dolny_text:

            return False

        log("=== VÝBER OBRÁZKA ===")

        otazka = ""

        for selektor in ["#q_word", "#question", ".question", "[class*='question']"]:

            try:

                prvok = stranka.locator(selektor).first

                if prvok.count() > 0:

                    otazka = prvok.inner_text(timeout=500).strip()

                    if otazka:

                        break

            except Exception:

                pass

        if not otazka:

            return False

        odpoved = get_answer_auto_update(otazka)

        if not odpoved:

            return False

        hladana_odpoved = normalize(odpoved)

        for i in range(pocet):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                aria = normalize(tlacidlo.get_attribute("aria-label") or "")

                title = normalize(tlacidlo.get_attribute("title") or "")

                spojeny_text = text + " " + aria + " " + title

                if hladana_odpoved in spojeny_text:

                    tlacidlo.click(timeout=1000)

                    log(f"Vybraný obrázok: {odpoved}")

                    return True

            except Exception:

                pass

        return False

    except Exception:

        return False





# POPIS OBRÁZKA

def spracuj_popis_obrazka(stranka):

    try:

        vstupy = stranka.locator("input[type='text']:visible, textarea:visible")

        if vstupy.count() == 0:

            return False

        text_stranky = stranka.locator("body").inner_text(timeout=500)

        dolny_text = text_stranky.lower()

        if (

            "popíš obrázok" not in dolny_text

            and "describe picture" not in dolny_text

            and "describe the picture" not in dolny_text

        ):

            return False

        log("=== POPIS OBRÁZKA ===")

        obrazok = stranka.locator("img").first

        if obrazok.count() == 0:

            return False

        alt = obrazok.get_attribute("alt") or ""

        title = obrazok.get_attribute("title") or ""

        slovo = alt.strip() or title.strip()

        if not slovo:

            return False

        odpoved = get_answer_auto_update(slovo)

        if not odpoved:

            return False

        vstupy.first.fill(odpoved, timeout=1000)

        tlacidla = stranka.locator("button:visible")

        for i in range(tlacidla.count()):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                if text in ("potvrdiť", "odoslať", "submit", "confirm", "check"):

                    tlacidlo.click(timeout=1000)

                    return True

            except Exception:

                pass

        return False

    except Exception:

        return False





# PREKLAD PADAJÚCEHO SLOVA

def spracuj_padajuce_slovo(stranka):
    try:
        kontajner = stranka.locator("#translateFallingWord").first
        if not kontajner.is_visible():
            return False
        prvok_slova = kontajner.locator("#tfw_word").first
        vstup = kontajner.locator("#translateFallingWordAnswer").first
        odoslat = kontajner.locator("#translateFallingWordSubmitBtn").first
        if not prvok_slova.is_visible() or not vstup.is_visible():
            return False
        slovo = prvok_slova.inner_text(timeout=500).strip()
        if not slovo or normalize(slovo) in {normalize(w) for w in PLACEHOLDER_WORDS}:
            return False
        odpoved = get_answer_auto_update(slovo)
        if not odpoved:
            return True
        if not prvok_slova.is_visible() or prvok_slova.inner_text(timeout=500).strip() != slovo:
            return True
        # Stránka aktivuje kontrolu cez udalosti klávesnice, nielen input.
        vstup.fill("", timeout=1000)
        vstup.press_sequentially(odpoved, delay=30, timeout=5000)
        if not prvok_slova.is_visible() or prvok_slova.inner_text(timeout=500).strip() != slovo:
            return True
        if not odoslat.is_enabled():
            return True
        odoslat.click(timeout=500)
        log(f"Padajúce slovo: {slovo} -> {odpoved}")
        return True
    except Exception as chyba:
        log(f"Padajúce slovo sa nepodarilo odoslať: {chyba}")
        return False


# VÝBER SLOVA

def spracuj_vyber_slova(stranka):

    try:

        text_stranky = stranka.locator("body").inner_text(timeout=500)

        dolny_text = text_stranky.lower()

        if "vyber slovo" not in dolny_text and "choose word" not in dolny_text:

            return False

        otazka_prvok = stranka.locator("#q_word:visible").first

        if otazka_prvok.count() == 0:

            return False

        otazka = otazka_prvok.inner_text(timeout=500).strip()

        if not otazka:

            return False

        odpoved = get_answer_auto_update(otazka)

        if not odpoved:

            return False

        hladana_odpoved = normalize(odpoved)

        tlacidla = stranka.locator("button:visible")

        for i in range(tlacidla.count()):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                if text == hladana_odpoved:

                    tlacidlo.click(timeout=1000)

                    log(f"Vybrané slovo: {odpoved}")

                    return True

            except Exception:

                pass

        return False

    except Exception:

        return False





# PEXESO

def spracuj_pexeso(stranka):

    try:

        karty = stranka.locator("[class*='pexeso'], [class*='memory'], [class*='card']")

        if karty.count() == 0:

            return False

        # Pexeso zatiaľ rieši samotná Wocabee.

        return False

    except Exception:

        return False





# DOPLNENIE SLOVA

def spracuj_doplnenie_slova(stranka):

    try:

        vstupy = stranka.locator("input[type='text']")

        if vstupy.count() == 0:

            return False

        text_stranky = stranka.locator("body").inner_text(timeout=500)

        dolny_text = text_stranky.lower()

        if (

            "doplň slovo" not in dolny_text

            and "complete word" not in dolny_text

            and "complete the word" not in dolny_text

        ):

            return False

        otazka = ""

        prvok = stranka.locator("#q_word:visible").first

        if prvok.count():

            otazka = prvok.inner_text(timeout=500).strip()

        if not otazka:

            return False

        odpoved = get_answer_auto_update(otazka)

        if not odpoved:

            return False

        vstupy.first.fill(odpoved, timeout=1000)

        tlacidla = stranka.locator("button:visible")

        for i in range(tlacidla.count()):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                if text in ("potvrdiť", "odoslať", "submit", "confirm", "check"):

                    tlacidlo.click(timeout=1000)

                    return True

            except Exception:

                pass

        return False

    except Exception:

        return False





# JEDNO Z VIACERÝCH

def spracuj_jedno_z_viacerych(stranka):

    try:

        text_stranky = stranka.locator("body").inner_text(timeout=500)

        dolny_text = text_stranky.lower()

        if "one out of many" not in dolny_text and "jedno z" not in dolny_text:

            return False

        otazka_prvok = stranka.locator("#q_word:visible").first

        if otazka_prvok.count() == 0:

            return False

        otazka = otazka_prvok.inner_text(timeout=500).strip()

        odpoved = get_answer_auto_update(otazka)

        if not odpoved:

            return False

        hladana_odpoved = normalize(odpoved)

        tlacidla = stranka.locator("button:visible")

        for i in range(tlacidla.count()):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                if text == hladana_odpoved:

                    tlacidlo.click(timeout=1000)

                    return True

            except Exception:

                pass

        return False

    except Exception:

        return False





# NESPÁVNE / AUTOMATICKÉ UČENIE

def spracuj_nespravne(stranka):
    panel = stranka.locator("#incorrect").first
    dalsie = stranka.locator("#incorrect-next-button").first
    if not panel.is_visible() and not dalsie.is_visible():
        return False
    # Učenie nesmie zablokovať pokračovanie, ani keď chýba text opravy.
    try:
        otazka_prvok = panel.locator(".correctWordQuestion").first
        odpoved_prvok = panel.locator(".correctWordAnswer").first
        if otazka_prvok.count() and odpoved_prvok.count():
            otazka = otazka_prvok.inner_text(timeout=500).strip()
            odpoved = odpoved_prvok.inner_text(timeout=500).strip()
            if otazka and odpoved and SLOVNIK.get(otazka) != odpoved:
                SLOVNIK[otazka] = odpoved
                uloz_slovnik()
                log(f"Uložená oprava: {otazka} -> {odpoved}")
    except Exception as chyba:
        log(f"Opravu odpovede sa nepodarilo uložiť: {chyba}")
    try:
        dalsie.click(timeout=3000)
        dalsie.wait_for(state="hidden", timeout=3000)
        log("Nesprávna odpoveď: pokračujem na ďalšiu úlohu.")
    except Exception as chyba:
        log(f"Nepodarilo sa pokračovať po nesprávnej odpovedi: {chyba}")
    # Kým je zobrazená oprava, ostatné riešiče nesmú vypĺňať starú úlohu.
    return True


# PREPISOVANIE

def spracuj_pisanie(stranka):

    try:

        text_stranky = stranka.locator("body").inner_text(timeout=500)

        dolny_text = text_stranky.lower()

        if (

            "transcribe" not in dolny_text

            and "prepíš" not in dolny_text

            and "prepis" not in dolny_text

        ):

            return False

        # Tento typ úlohy zatiaľ preskočíme.

        return False

    except Exception:

        return False





# BEŽNÝ PREKLAD

def spracuj_bezny_preklad(stranka):

    try:

        prvok_slova = stranka.locator("#q_word:visible").first

        if prvok_slova.count() == 0:

            return False

        slovo = prvok_slova.inner_text(timeout=500).strip()

        if not slovo:

            return False

        selektory_vstupu = [

            "#translateAnswer",

            "#answer",

            "input[type='text']",

            "textarea",

        ]

        vstup = None

        for selektor in selektory_vstupu:

            try:

                prvok = stranka.locator(selektor).first

                if prvok.count():

                    vstup = prvok

                    break

            except Exception:

                pass

        if vstup is None:

            return False

        odpoved = get_answer_auto_update(slovo)

        if not odpoved:

            return False

        vstup.fill(odpoved, timeout=1000)

        selektory_odoslania = [

            "#translateSubmitBtn",

            "#submit",

            "button[type='submit']",

        ]

        for selektor in selektory_odoslania:

            try:

                odoslat = stranka.locator(selektor).first

                if odoslat.count():

                    odoslat.click(timeout=1000)

                    log(f"Preložené: {slovo} -> {odpoved}")

                    return True

            except Exception:

                pass

        tlacidla = stranka.locator("button:visible")

        for i in range(tlacidla.count()):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                if text in (

                    "potvrdiť",

                    "odoslať",

                    "submit",

                    "check",

                    "kontrola",

                    "skontrolovať",

                ):

                    tlacidlo.click(timeout=1000)

                    log(f"Preložené: {slovo} -> {odpoved}")

                    return True

            except Exception:

                pass

        return False

    except Exception:

        return False





# PRIPOJENIE K PREHLIADAČU

def normalizuj_cdp_adresu(hodnota):

    hodnota = str(hodnota or "").strip()

    if not hodnota:

        hodnota = "9222"

    if hodnota.startswith(("http://", "https://", "ws://", "wss://")):

        return hodnota

    if hodnota.isdigit():

        return f"http://127.0.0.1:{hodnota}"

    if ":" in hodnota:

        return f"http://{hodnota}"

    raise ValueError(f"Neplatná CDP adresa alebo port: {hodnota!r}")


def pripoj_prehladavac(playwright):

    prehliadac = None

    kontext = None

    stranka = None

    try:

        cdp_adresa = normalizuj_cdp_adresu(DEBUG_PORT)

        log(f"Pripájam sa k prehliadaču cez {cdp_adresa}...")

        prehliadac = playwright.chromium.connect_over_cdp(cdp_adresa)

        if prehliadac.contexts:

            kontext = prehliadac.contexts[0]

        else:

            kontext = prehliadac.new_context()

        stranka = najdi_cielovu_stranku(kontext)

        if stranka is None:

            stranka = kontext.new_page()

        log(f"Pripojené: {stranka.url}")

        return (prehliadac, kontext, stranka)

    except Exception as chyba:

        log(f"Nepodarilo sa pripojiť k prehliadaču: {chyba}")

        return (None, None, None)





# KONTROLA STRÁNKY

def zabezpec_stranku(stranka):

    try:

        if not stranka.url or stranka.url == "about:blank":

            stranka.goto(URLBASE, wait_until="domcontentloaded", timeout=30000)

            return True

        return True

    except Exception as chyba:

        log(f"Nepodarilo sa načítať Wocabee: {chyba}")

        return False





# HLAVNÝ PROGRAM

def main():

    global DEBUG_PORT, AUTO_TRANSLATE

    parser = argparse.ArgumentParser(description="WocaFuckOff riešič")

    parser.add_argument("--debug-port", default=DEBUG_PORT)
    parser.add_argument(
        "--auto-translate", action=argparse.BooleanOptionalAction, default=AUTO_TRANSLATE
    )

    argumenty = parser.parse_args()

    DEBUG_PORT = str(argumenty.debug_port).strip()
    AUTO_TRANSLATE = argumenty.auto_translate

    log("")

    log("========================================")

    log("          WOCAFUCKOFF RIEŠIČ")

    log("========================================")

    log("")

    if DOUBLE_POINTS:

        log("Dvojité body sú aktivované.")

    if not AUTO_TRANSLATE:
        log("AutoTranslate je vypnutý.")
    if AUTO_TRANSLATE:

        if AZURE_TRANSLATOR_KEY:

            log("Automatický preklad cez Azure Translator je aktivovaný.")

        else:

            log(

                "Automatický preklad cez Azure Translator "

                "je aktivovaný, ale API kľúč "

                "nie je nastavený."

            )

    log(f"Adresa Wocabee: {URLBASE}")

    log(f"Súbor slovníka: {WORDLIST_FILE}")

    log(f"Počet uložených slov: {len(SLOVNIK)}")

    log("")

    with sync_playwright() as playwright:

        prehliadac = None

        kontext = None

        stranka = None

        try:

            (prehliadac, kontext, stranka) = pripoj_prehladavac(playwright)

            if stranka is None:

                log("Nepodarilo sa pripojiť k prehliadaču.")

                return 1

            if not zabezpec_stranku(stranka):

                return 1

            stranka.set_default_timeout(1500)
            log("Riešič je pripravený.")

            posledne_body = None
            posledny_najdeny_prvok = time.monotonic()

            while True:

                try:

                    # Aktualizácia stránky

                    ciel = najdi_cielovu_stranku(kontext)

                    if ciel is not None:

                        stranka = ciel

                    # Kontrola bodov

                    body = get_points(stranka)

                    if body is not None:

                        if body != posledne_body:

                            log(f"WocaPoints: {body}")

                            posledne_body = body

                            if body >= LAST_POINTS + ADDON_POINTS:

                                posli_ntfy(f"WocaFuckOff: {body} WocaPoints")


                    # Nesprávne / automatické učenie

                    if spracuj_nespravne(stranka):
                        posledny_najdeny_prvok = time.monotonic()

                        time.sleep(0.1)

                        continue

                    # Aktívna časovaná úloha má prednosť. Počas jej prechodu
                    # nesmú všeobecné riešiče čakať na skryté staré formuláre.
                    if stranka.locator("#translateFallingWord").first.is_visible():
                        spracuj_padajuce_slovo(stranka)
                        posledny_najdeny_prvok = time.monotonic()
                        time.sleep(0.1)
                        continue

                    # Jedno z viacerých
                    if spracuj_jedno_z_viacerych(stranka):
                        posledny_najdeny_prvok = time.monotonic()
                        time.sleep(0.1)
                        continue

                    # Výber obrázka

                    if spracuj_vyber_obrazka(stranka):
                        posledny_najdeny_prvok = time.monotonic()

                        time.sleep(0.1)

                        continue

                    # Popis obrázka

                    if spracuj_popis_obrazka(stranka):
                        posledny_najdeny_prvok = time.monotonic()

                        time.sleep(0.1)

                        continue

                    # Pexeso

                    if spracuj_pexeso(stranka):
                        posledny_najdeny_prvok = time.monotonic()

                        time.sleep(0.1)

                        continue

                    # Doplnenie slova

                    if spracuj_doplnenie_slova(stranka):
                        posledny_najdeny_prvok = time.monotonic()

                        time.sleep(0.1)

                        continue

                    # Výber slova

                    if spracuj_vyber_slova(stranka):
                        posledny_najdeny_prvok = time.monotonic()

                        time.sleep(0.1)

                        continue

                    # Písanie / prepis

                    if spracuj_pisanie(stranka):
                        posledny_najdeny_prvok = time.monotonic()

                        time.sleep(0.1)

                        continue

                    # Hľadanie dvojice

                    # Táto funkcia zatiaľ nie je automatizovaná.

                    # Bežný preklad

                    if spracuj_bezny_preklad(stranka):
                        posledny_najdeny_prvok = time.monotonic()

                        time.sleep(0.1)

                        continue

                    if (
                        "/practice/" in stranka.url.lower()
                        and time.monotonic() - posledny_najdeny_prvok >= 30
                    ):
                        log(
                            "CHYBA[UI_CHANGED]: WocaBee zrejme zmenilo rozhranie; "
                            "riešič 30 sekúnd nenašiel žiadny očakávaný prvok."
                        )
                        return 2
                    time.sleep(0.1)

                except KeyboardInterrupt:

                    raise

                except Exception as chyba:

                    log(f"Chyba v hlavnej slučke: {chyba}")

                    traceback.print_exc()

                    time.sleep(1)

        except KeyboardInterrupt:

            log("")

            log("Riešič bol zastavený používateľom.")

            return 0

        except Exception as chyba:

            log("")

            log(f"KRITICKÁ CHYBA: {chyba}")

            traceback.print_exc()

            return 1

        finally:

            AZURE_EXECUTOR.shutdown(wait=False, cancel_futures=True)

            try:

                if prehliadac is not None:

                    prehliadac.close()

            except Exception:

                pass





if __name__ == "__main__":

    sys.exit(main())
