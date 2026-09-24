# SOLVER.PY

# -*- coding: utf-8 -*-

# IMPORTY

import argparse

import json

import os

import sys

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

# DEEPL

DEEPL_API_KEY = (

    os.environ.get("DEEPL_API_KEY") or config.get("deepl_api_key", "")

).strip()

# DeepL API Free / Pro

DEEPL_URL = (

    "https://api-free.deepl.com/v2/translate"

    if DEEPL_API_KEY.endswith(":fx")

    else "https://api.deepl.com/v2/translate"

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

    selektory = [

        "#wocaPoints",

        "#points",

        ".woca-points",

        ".points",

        "[class*='points']",

    ]

    for selektor in selektory:

        try:

            prvok = page.locator(selektor).first

            if prvok.count() > 0:

                text = prvok.inner_text(timeout=1000).strip()

                cisla = "".join(znak for znak in text if znak.isdigit())

                if cisla:

                    return int(cisla)

        except Exception:

            pass

    try:

        text_stranky = page.locator("body").inner_text(timeout=1000)

        import re



        zhody = re.findall(

            r"(?:WocaPoints|Woca\s*Points|Points)\D*(\d+)",

            text_stranky,

            flags=re.IGNORECASE,

        )

        if zhody:

            return int(zhody[0])

    except Exception:

        pass

    return None





# PREKLAD CEZ DEEPL

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





def preloz_cez_deepl(text, cielovy_jazyk):

    """

    Preloží text cez DeepL.



    Výsledok:

        (preklad, zistený_zdrojový_jazyk)

    """

    text = vycisti_preklad(text)

    if not text:

        return "", ""

    if not DEEPL_API_KEY:

        log("DeepL API kľúč nie je nastavený.")

        return "", ""

    try:

        odpoved = requests.post(

            DEEPL_URL,

            headers={

                "Authorization": (f"DeepL-Auth-Key {DEEPL_API_KEY}"),

                "Content-Type": ("application/x-www-form-urlencoded"),

            },

            data={"text": text, "target_lang": cielovy_jazyk},

            timeout=15,

        )

        if odpoved.status_code != 200:

            try:

                udaje_chyby = odpoved.json()

                sprava = udaje_chyby.get("message", odpoved.text)

            except Exception:

                sprava = odpoved.text

            log(f"DeepL chyba HTTP {odpoved.status_code}: {sprava}")

            return "", ""

        udaje = odpoved.json()

        preklady = udaje.get("translations", [])

        if not preklady:

            log("DeepL nevrátil žiadny preklad.")

            return "", ""

        zaznam = preklady[0]

        prelozeny = vycisti_preklad(zaznam.get("text", ""))

        zisteny_jazyk = zaznam.get("detected_source_language", "").strip().lower()

        if not preklad_je_platny(text, prelozeny):

            log(f"DeepL vrátil neplatný preklad: {text!r} -> {prelozeny!r}")

            return "", zisteny_jazyk

        return (prelozeny, zisteny_jazyk)

    except requests.RequestException as chyba:

        log(f"Sieťová chyba DeepL: {chyba}")

        return "", ""

    except Exception as chyba:

        log(f"Chyba DeepL: {chyba}")

        return "", ""





def automaticky_preloz_slovo(slovo):

    """

    Automatický preklad medzi slovenčinou

    a angličtinou cez DeepL.

    """

    slovo = vycisti_preklad(slovo)

    if not slovo:

        return ""

    # SLOVENČINA -> ANGLIČTINA

    preklad, zdrojovy_jazyk = preloz_cez_deepl(slovo, "EN")

    if preklad and zdrojovy_jazyk == "sk":

        log(f"DeepL: SK -> EN: {slovo} -> {preklad}")

        return preklad

    # ANGLIČTINA -> SLOVENČINA

    preklad, zdrojovy_jazyk = preloz_cez_deepl(slovo, "SK")

    if preklad and zdrojovy_jazyk == "en":

        log(f"DeepL: EN -> SK: {slovo} -> {preklad}")

        return preklad

    log(f"DeepL nedokázal určiť smer prekladu pre: {slovo!r}")

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

    # 6. Automatický preklad cez DeepL

    if AUTO_TRANSLATE:

        preklad = automaticky_preloz_slovo(slovo)

        if preklad:

            # Zachováva sa aj slovenská diakritika.

            SLOVNIK[slovo] = preklad

            uloz_slovnik()

            return preklad

    # 7. Manuálne zadanie

    try:

        odpoved = input(f"Preklad pre '{slovo}': ").strip()

        if odpoved:

            SLOVNIK[slovo] = odpoved

            uloz_slovnik()

            return odpoved

    except (EOFError, KeyboardInterrupt):

        return ""

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

        tlacidla = stranka.locator("button")

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

                    tlacidlo.click()

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

        vstupy = stranka.locator("input[type='text'], textarea")

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

        vstupy.first.fill(odpoved)

        tlacidla = stranka.locator("button")

        for i in range(tlacidla.count()):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                if text in ("potvrdiť", "odoslať", "submit", "confirm", "check"):

                    tlacidlo.click()

                    return True

            except Exception:

                pass

        return False

    except Exception:

        return False





# PREKLAD PADAJÚCEHO SLOVA

def spracuj_padajuce_slovo(stranka):

    try:

        prvok_slova = stranka.locator("#tfw_word").first

        if prvok_slova.count() == 0:

            return False

        slovo = prvok_slova.inner_text(timeout=500).strip()

        if not slovo:

            return False

        log("=== PREKLAD PADAJÚCEHO SLOVA ===")

        log(f"Slovo: {slovo}")

        odpoved = get_answer_auto_update(slovo)

        if not odpoved:

            log(f"Pre slovo '{slovo}' nebola nájdená odpoveď.")

            return False

        vstup = stranka.locator("#translateFallingWordAnswer").first

        if vstup.count() == 0:

            return False

        vstup.fill(odpoved)

        odoslat = stranka.locator("#translateFallingWordSubmitBtn").first

        if odoslat.count():

            odoslat.click()

            log(f"Odpoveď: {odpoved}")

            return True

        return False

    except Exception:

        return False





# VÝBER SLOVA

def spracuj_vyber_slova(stranka):

    try:

        text_stranky = stranka.locator("body").inner_text(timeout=500)

        dolny_text = text_stranky.lower()

        if "vyber slovo" not in dolny_text and "choose word" not in dolny_text:

            return False

        otazka_prvok = stranka.locator("#q_word").first

        if otazka_prvok.count() == 0:

            return False

        otazka = otazka_prvok.inner_text(timeout=500).strip()

        if not otazka:

            return False

        odpoved = get_answer_auto_update(otazka)

        if not odpoved:

            return False

        hladana_odpoved = normalize(odpoved)

        tlacidla = stranka.locator("button")

        for i in range(tlacidla.count()):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                if text == hladana_odpoved:

                    tlacidlo.click()

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

        # Pexeso zatiaľ rieši samotná WocaBee.

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

        prvok = stranka.locator("#q_word").first

        if prvok.count():

            otazka = prvok.inner_text(timeout=500).strip()

        if not otazka:

            return False

        odpoved = get_answer_auto_update(otazka)

        if not odpoved:

            return False

        vstupy.first.fill(odpoved)

        tlacidla = stranka.locator("button")

        for i in range(tlacidla.count()):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                if text in ("potvrdiť", "odoslať", "submit", "confirm", "check"):

                    tlacidlo.click()

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

        otazka_prvok = stranka.locator("#q_word").first

        if otazka_prvok.count() == 0:

            return False

        otazka = otazka_prvok.inner_text(timeout=500).strip()

        odpoved = get_answer_auto_update(otazka)

        if not odpoved:

            return False

        hladana_odpoved = normalize(odpoved)

        tlacidla = stranka.locator("button")

        for i in range(tlacidla.count()):

            try:

                tlacidlo = tlacidla.nth(i)

                text = normalize(tlacidlo.inner_text(timeout=300))

                if text == hladana_odpoved:

                    tlacidlo.click()

                    return True

            except Exception:

                pass

        return False

    except Exception:

        return False





# NESPÁVNE / AUTOMATICKÉ UČENIE

def spracuj_nespravne(stranka):

    try:

        text_stranky = stranka.locator("body").inner_text(timeout=500)

        dolny_text = text_stranky.lower()

        if (

            "nesprávne" not in dolny_text

            and "incorrect" not in dolny_text

            and "autolearn" not in dolny_text

        ):

            return False

        otazka = ""

        odpoved = ""

        for selektor in ["#q_word", "#question"]:

            try:

                prvok = stranka.locator(selektor).first

                if prvok.count():

                    otazka = prvok.inner_text(timeout=300).strip()

                    if otazka:

                        break

            except Exception:

                pass

        if not otazka:

            return False

        for selektor in ["#correctAnswer", ".correct-answer", "[class*='correct']"]:

            try:

                prvok = stranka.locator(selektor).first

                if prvok.count():

                    odpoved = prvok.inner_text(timeout=300).strip()

                    if odpoved:

                        break

            except Exception:

                pass

        if otazka and odpoved:

            SLOVNIK[otazka] = odpoved

            uloz_slovnik()

            return True

        return False

    except Exception:

        return False





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

        prvok_slova = stranka.locator("#q_word").first

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

        vstup.fill(odpoved)

        selektory_odoslania = [

            "#translateSubmitBtn",

            "#submit",

            "button[type='submit']",

        ]

        for selektor in selektory_odoslania:

            try:

                odoslat = stranka.locator(selektor).first

                if odoslat.count():

                    odoslat.click()

                    log(f"Preložené: {slovo} -> {odpoved}")

                    return True

            except Exception:

                pass

        tlacidla = stranka.locator("button")

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

                    tlacidlo.click()

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

        log(f"Nepodarilo sa načítať WocaBee: {chyba}")

        return False





# HLAVNÝ PROGRAM

def main():

    global DEBUG_PORT

    parser = argparse.ArgumentParser(description="WocaFuckOff riešič")

    parser.add_argument("--debug-port", default=DEBUG_PORT)

    argumenty = parser.parse_args()

    DEBUG_PORT = str(argumenty.debug_port).strip()

    log("")

    log("========================================")

    log("          WOCAFUCKOFF RIEŠIČ")

    log("========================================")

    log("")

    if DOUBLE_POINTS:

        log("Dvojité body sú aktivované.")

    if AUTO_TRANSLATE:

        if DEEPL_API_KEY:

            log("Automatický preklad cez DeepL je aktivovaný.")

        else:

            log(

                "Automatický preklad cez DeepL "

                "je aktivovaný, ale API kľúč "

                "nie je nastavený."

            )

    log(f"Adresa WocaBee: {URLBASE}")

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

            log("Riešič je pripravený.")

            posledne_body = LAST_POINTS

            while True:

                try:

                    # Aktualizácia stránky

                    ciel = najdi_cielovu_stranku(kontext)

                    if ciel is not None:

                        stranka = ciel

                    # Nesprávne / automatické učenie

                    if spracuj_nespravne(stranka):

                        time.sleep(0.1)

                        continue

                    # Jedno z viacerých

                    if spracuj_jedno_z_viacerych(stranka):

                        time.sleep(0.1)

                        continue

                    # Padajúce slovo

                    if spracuj_padajuce_slovo(stranka):

                        time.sleep(0.1)

                        continue

                    # Výber obrázka

                    if spracuj_vyber_obrazka(stranka):

                        time.sleep(0.1)

                        continue

                    # Popis obrázka

                    if spracuj_popis_obrazka(stranka):

                        time.sleep(0.1)

                        continue

                    # Pexeso

                    if spracuj_pexeso(stranka):

                        time.sleep(0.1)

                        continue

                    # Doplnenie slova

                    if spracuj_doplnenie_slova(stranka):

                        time.sleep(0.1)

                        continue

                    # Výber slova

                    if spracuj_vyber_slova(stranka):

                        time.sleep(0.1)

                        continue

                    # Písanie / prepis

                    if spracuj_pisanie(stranka):

                        time.sleep(0.1)

                        continue

                    # Hľadanie dvojice

                    # Táto funkcia zatiaľ nie je automatizovaná.

                    # Bežný preklad

                    if spracuj_bezny_preklad(stranka):

                        time.sleep(0.1)

                        continue

                    # Kontrola bodov

                    body = get_points(stranka)

                    if body is not None:

                        if body != posledne_body:

                            log(f"WocaPoints: {body}")

                            posledne_body = body

                            if body >= LAST_POINTS + ADDON_POINTS:

                                posli_ntfy(f"WocaFuckOff: {body} WocaPoints")

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

            try:

                if prehliadac is not None:

                    prehliadac.close()

            except Exception:

                pass





if __name__ == "__main__":

    sys.exit(main())
