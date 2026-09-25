# MANAGEMENT.PY
# -*- coding: utf-8 -*-
# IMPORTY
import os
import sys
import subprocess
import socket
import time
import urllib.request
import urllib.error
import re
import json
import hashlib
import toml
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# UTF-8
if sys.stdout is not None:
    sys.stdout.reconfigure(
        encoding="utf-8", errors="backslashreplace", line_buffering=True
    )
if sys.stderr is not None:
    sys.stderr.reconfigure(
        encoding="utf-8", errors="backslashreplace", line_buffering=True
    )
# CESTY
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.toml")
CHROMIUM_PROFILE_DIR = os.path.join(BASE_DIR, ".wocafuckoff_chromium")


# LOG
def log(*args):
    print(*args, flush=True)


# WOCAPOINTS
def report_wocapoints(page):
    """
    Načíta aktuálne WocaPoints priamo z HTML stránky.

    Wocabee môže mať na stránke napríklad:

        Tvoje skóre: <b>325</b> WocaPoints

    Do stdout vypíše:

        WOCAPOINTS: 325

    GUI tento riadok zachytí a aktualizuje WocaPoints.
    """
    log("")
    log("=== WOCAPOINTS ===")
    try:
        counter = page.locator("#WocaPoints:visible").first
        if counter.count():
            digits = re.sub(r"[^0-9]", "", counter.inner_text(timeout=500))
            if digits:
                points = int(digits)
                log(f"WOCAPOINTS: {points}")
                return points
    except Exception as error:
        log(f"WocaPoints počas riešenia nie sú dostupné: {error}")
    try:
        html = page.content()
    except Exception as error:
        log(f"VAROVANIE: Nepodarilo sa načítať HTML pre WocaPoints: {error}")
        return None
    # Presný HTML formát Wocabee
    match = re.search(
        r"Tvoje\s+skóre:\s*"
        r"<b>\s*"
        r"([0-9][0-9\s.,]*)"
        r"\s*</b>\s*"
        r"WocaPoints",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    # Fallback:
    # HTML môže obsahovať ďalšie tagy alebo inú medzeru.
    if not match:
        match = re.search(
            r"Tvoje\s+skóre:"
            r".*?"
            r"<b[^>]*>\s*"
            r"([0-9][0-9\s.,]*)"
            r"\s*</b>"
            r".*?"
            r"WocaPoints",
            html,
            re.IGNORECASE | re.DOTALL,
        )
    # Fallback cez viditeľný text stránky
    if not match:
        try:
            body_text = page.locator("body").inner_text(timeout=5000)
            match = re.search(
                r"Tvoje\s+skóre:\s*"
                r"([0-9][0-9\s.,]*)"
                r"\s*WocaPoints",
                body_text,
                re.IGNORECASE | re.DOTALL,
            )
        except Exception:
            pass
    if not match:
        log("WocaPoints sa v aktuálnej stránke nenašli.")
        return None
    raw_points = match.group(1)
    # Odstránenie medzier
    points_text = raw_points.replace(" ", "")
    # Pre WocaPoints nás zaujíma celé číslo.
    points_digits = re.sub(r"[^0-9]", "", points_text)
    if not points_digits:
        log(f"VAROVANIE: WocaPoints majú neplatnú hodnotu: {raw_points}")
        return None
    try:
        points = int(points_digits)
    except ValueError:
        log(f"VAROVANIE: WocaPoints sa nedali previesť na číslo: {raw_points}")
        return None
    # GUI dostane presne tento riadok.
    log(f"WOCAPOINTS: {points}")
    log(f"WocaPoints: {points}")
    return points


# CONFIG
def load_config():
    if not os.path.exists(CONFIG_FILE):
        log(f"CHYBA: config.toml neexistuje: {CONFIG_FILE}")
        return {}
    try:
        return toml.load(CONFIG_FILE)
    except Exception as error:
        log(f"CHYBA pri načítaní config.toml: {error}")
        return {}


def get_chromium_profile_dir(urlbase, username):
    """Return a stable, private Chromium profile path for one WocaBee account.

    A shared persistent profile can contain a valid login for a different account.
    In that case WocaBee skips the login form and the selected package belongs to a
    different class.  Keep browser sessions isolated without putting the username
    into the directory name.
    """
    normalized_url = str(urlbase).strip()
    if not normalized_url.startswith(("http://", "https://")):
        normalized_url = "https://" + normalized_url
    normalized_url = normalized_url.rstrip("/").casefold()
    normalized_username = str(username).strip().casefold()
    identity = f"{normalized_url}\0{normalized_username}".encode("utf-8")
    suffix = hashlib.sha256(identity).hexdigest()[:16]
    return f"{CHROMIUM_PROFILE_DIR}-{suffix}"


# CDP PORT
def get_debug_port(value):
    value = str(value).strip()
    if not value:
        return 9222
    try:
        from urllib.parse import urlparse

        if "://" in value:
            parsed = urlparse(value)
            if parsed.port:
                return parsed.port
    except Exception:
        pass
    if ":" in value:
        try:
            return int(value.rsplit(":", 1)[1])
        except Exception:
            pass
    try:
        return int(value)
    except Exception:
        return 9222


# KONTROLA PORTU
def is_port_in_use(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex(("127.0.0.1", port)) == 0
    finally:
        sock.close()


def terminate_port_processes(port):
    """Stop every process listening on a CDP port and verify it became free."""
    if not is_port_in_use(port):
        return True
    log(f"VAROVANIE: Port {port} je obsadený. Ukončujem procesy na tomto porte...")
    script = (
        f"$ids = Get-NetTCPConnection -LocalPort {int(port)} -State Listen "
        "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; "
        "$ids | ForEach-Object { Write-Output $_; Stop-Process -Id $_ -Force "
        "-ErrorAction SilentlyContinue }"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for pid in result.stdout.splitlines():
            if pid.strip().isdigit():
                log(f"INFO: Ukončený proces PID {pid.strip()} na porte {port}.")
        time.sleep(0.5)
        return not is_port_in_use(port)
    except (OSError, subprocess.SubprocessError):
        return False


# ČAKANIE NA CDP
def wait_for_cdp(port, timeout=15):
    url = f"http://127.0.0.1:{port}/json/version"
    log(f"Čakám na CDP: {url}")
    started = time.monotonic()
    while time.monotonic() - started < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    log("CDP je pripravené.")
                    return True
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            pass
        time.sleep(0.25)
    log(f"CHYBA: CDP sa do {timeout} sekúnd nespustilo.")
    return False


# SPUSTENIE CHROMIUM
def launch_chromium(p, headless, port, profile_dir):
    log("")
    log("=== CHROMIUM ===")
    executable = p.chromium.executable_path
    log("Chromium executable:")
    log(executable)
    if not executable:
        raise RuntimeError("Playwright neposkytol cestu k Chromium.")
    if not os.path.exists(executable):
        raise RuntimeError(f"Chromium executable neexistuje:\n{executable}")
    profile_dir = os.path.abspath(profile_dir)
    os.makedirs(profile_dir, exist_ok=True)
    args = [
        executable,
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--mute-audio",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-popup-blocking",
        "--no-sandbox",
    ]
    if headless:
        args.append("--headless=new")
    log("")
    log("Spúšťam Chromium ako samostatný proces...")
    log(f"CDP port: {port}")
    log(f"Headless: {headless}")
    log("Profil:")
    log(profile_dir)
    process = subprocess.Popen(
        args,
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
    )
    log(f"Chromium PID: {process.pid}")
    if not wait_for_cdp(port, timeout=15):
        try:
            process.terminate()
        except Exception:
            pass
        raise RuntimeError("Chromium sa spustilo, ale CDP port neodpovedá.")
    return process


# PRIHLÁSENIE
def login(page, username, password):
    log("")
    log("=== PRIHLÁSENIE ===")
    if "/student" in page.url.lower():
        log("Používateľ je už prihlásený.")
        log(f"Aktuálna URL: {page.url}")
        return True
    try:
        log("Hľadám #login...")
        page.wait_for_selector("#login", timeout=10000)
        page.fill("#login", username)
        log("Username vyplnený.")
    except PlaywrightTimeoutError:
        log("CHYBA[UI_CHANGED]: WocaBee zmenilo rozhranie alebo sa nenačítal prihlasovací formulár (#login).")
        return False
    except Exception as error:
        log(f"CHYBA username: {error}")
        return False
    try:
        log("Hľadám #password...")
        page.wait_for_selector("#password", timeout=10000)
        page.fill("#password", password)
        log("Password vyplnený.")
    except PlaywrightTimeoutError:
        log("CHYBA[UI_CHANGED]: WocaBee zmenilo rozhranie alebo chýba pole hesla (#password).")
        return False
    except Exception as error:
        log(f"CHYBA password: {error}")
        return False
    try:
        page.press("#password", "Enter")
        log("Prihlasovacie údaje odoslané.")
    except Exception as error:
        log(f"CHYBA pri prihlasovaní: {error}")
        return False
    log("Čakám na prihlásenie...")
    try:
        page.wait_for_url("**/student/**", timeout=15000)
        log("Prihlásenie úspešné.")
    except PlaywrightTimeoutError:
        log(f"VAROVANIE: Redirect sa nepotvrdil. URL: {page.url}")
        if "/student" not in page.url.lower():
            log("CHYBA[AUTH]: Nesprávne prihlasovacie meno alebo heslo.")
            return False
    log(f"Aktuálna URL: {page.url}")
    return True


# VÝBER TRIEDY
def click_class_by_index(page, index):
    log("")
    log("=== VÝBER TRIEDY ===")
    log(f"Index triedy: {index}")
    try:
        page.wait_for_selector("#listOfClasses a", timeout=10000)
        classes = page.locator("#listOfClasses a")
        count = classes.count()
        log(f"Nájdených tried: {count}")
        if count == 0:
            log("CHYBA: Žiadne triedy.")
            return False
        if index < 0 or index >= count:
            log(f"CHYBA: Index {index} je mimo rozsahu 0-{count - 1}.")
            return False
        log(f"Klikám na triedu {index}...")
        classes.nth(index).click(timeout=10000)
        page.wait_for_timeout(700)
        log("Trieda vybraná.")
        return True
    except PlaywrightTimeoutError:
        log("CHYBA[UI_CHANGED]: WocaBee opakovane nenašlo očakávaný zoznam tried.")
        return False
    except Exception as error:
        log(f"CHYBA triedy: {error}")
        return False


# NAČÍTANIE BALÍKOV
def get_packages(page):
    """
    Načíta všetky aktuálne balíky z Wocabee.

    Každý balík obsahuje:

        id
        index
        name
        deadline
        progress
        progress_values
        status
        practice_url
        pronunciation_url
        run_url
        has_practice
        has_pronunciation
        has_run
    """
    log("")
    log("=== NAČÍTANIE BALÍKOV ===")
    try:
        page.wait_for_selector("tr.pTableRow", timeout=10000)
    except PlaywrightTimeoutError:
        log("CHYBA[UI_CHANGED]: WocaBee opakovane nenašlo očakávanú tabuľku balíkov.")
        return []
    except Exception as error:
        log(f"CHYBA pri hľadaní balíkov: {error}")
        return []
    packages_locator = page.locator("tr.pTableRow")
    count = packages_locator.count()
    log(f"Nájdených balíkov: {count}")
    packages = []
    for index in range(count):
        try:
            package = packages_locator.nth(index)
            # NÁZOV
            name_locator = package.locator(".package-name")
            name = ""
            if name_locator.count() > 0:
                name = name_locator.first.inner_text().strip()
            # TERMÍN
            date_locator = package.locator(".package-date")
            deadline = ""
            if date_locator.count() > 0:
                deadline = date_locator.first.inner_text().strip()
                deadline = re.sub(r"\s+", " ", deadline)
            # PACKAGE ID
            package_id = None
            detail_link = package.locator("a.intro-icon")
            if detail_link.count() > 0:
                href = detail_link.first.get_attribute("href")
                if href:
                    match = re.search(r"[?&]package_id=(\d+)", href)
                    if match:
                        package_id = match.group(1)
            if package_id is None:
                run_button = package.locator("[id^='btnRun']")
                if run_button.count() > 0:
                    button_id = run_button.first.get_attribute("id")
                    if button_id:
                        match = re.search(r"btnRun(\d+)", button_id)
                        if match:
                            package_id = match.group(1)
            # PROGRESS
            progress_values = []
            circles = package.locator(".circles-wrapper > *")
            circle_count = circles.count()
            for circle_index in range(min(circle_count, 3)):
                circle = circles.nth(circle_index)
                class_name = circle.get_attribute("class") or ""
                class_name = class_name.lower()
                if "circle-todo" in class_name:
                    progress_values.append(0)
                elif "half-circle" in class_name:
                    progress_values.append(50)
                elif "progress-icon" in class_name and "circle-check" in class_name:
                    progress_values.append(100)
                else:
                    progress_values.append(0)
            while len(progress_values) < 3:
                progress_values.append(0)
            progress_values = progress_values[:3]
            progress_symbols = []
            for value in progress_values:
                if value >= 100:
                    progress_symbols.append("●")
                elif value >= 50:
                    progress_symbols.append("◐")
                else:
                    progress_symbols.append("○")
            progress = "".join(progress_symbols)
            # STATUS
            if all(value >= 100 for value in progress_values):
                status = "dokončené"
            elif any(value > 0 for value in progress_values):
                status = "rozpracované"
            else:
                status = "nezačaté"
            # PRECVIČIŤ
            practice_url = None
            practice_link = package.locator("a[href*='/practice/']")
            if practice_link.count() > 0:
                practice_url = practice_link.first.get_attribute("href")
            # VÝSLOVNOSŤ
            pronunciation_url = None
            pronunciation_link = package.locator("a[href*='/pronunciation/']")
            if pronunciation_link.count() > 0:
                pronunciation_url = pronunciation_link.first.get_attribute("href")
            # SPUSTIŤ BALÍK
            run_url = None
            run_link = package.locator("a:has(.fa-play-circle)")
            if run_link.count() > 0:
                run_url = run_link.first.get_attribute("href")
            # VÝSLEDNÝ OBJEKT
            package_data = {
                "id": package_id,
                "index": index,
                "name": name,
                "deadline": deadline,
                "progress": progress,
                "progress_values": progress_values,
                "status": status,
                "practice_url": practice_url,
                "pronunciation_url": pronunciation_url,
                "run_url": run_url,
                "has_practice": (practice_url is not None),
                "has_pronunciation": (pronunciation_url is not None),
                "has_run": (run_url is not None),
            }
            packages.append(package_data)
            log(f"[{index}] {name} | {deadline} | {progress} | ID: {package_id}")
        except Exception as error:
            log(f"VAROVANIE: Balík {index} sa nepodarilo načítať: {error}")
    log(f"Úspešne načítaných balíkov: {len(packages)}")
    return packages


# VÝSTUP BALÍKOV PRE GUI
def report_packages(page):
    """
    Načíta balíky a odošle ich GUI ako JSON.

    Formát:

        PACKAGES_JSON: [...]
    """
    packages = get_packages(page)
    try:
        payload = json.dumps(packages, ensure_ascii=False)
        log(f"PACKAGES_JSON: {payload}")
    except Exception as error:
        log(f"CHYBA pri serializácii balíkov: {error}")
        return False
    return True


# VÝBER BALÍKA
def click_package_by_id(page, selected_package_id):
    log("")
    log("=== VÝBER BALÍKA ===")
    log(f"ID balíka: {selected_package_id}")
    try:
        page.wait_for_selector("tr.pTableRow", timeout=10000)
        selected_package_id = str(selected_package_id or "").strip()
        if not selected_package_id:
            log("CHYBA: Najprv vyber balík v sekcii Balíčky.")
            return False
        # Resolve the saved ID against the current Wocabee list.
        current_packages = get_packages(page)
        matches = [
            p
            for p in current_packages
            if str(p.get("id") or "").strip() == selected_package_id
        ]
        if len(matches) != 1:
            log(
                "CHYBA: Vybraný balík nie je jednoznačne dostupný. Obnov zoznam a vyber balík znova."
            )
            return False
        package = page.locator("tr.pTableRow").nth(matches[0]["index"])
        button = package.locator("a .btn-primary")
        log("Čakám na tlačidlo balíka...")
        button.wait_for(state="visible", timeout=10000)
        log("Klikám na balík...")
        button.click(timeout=10000)
        page.wait_for_timeout(700)
        log("Balík vybraný.")
        return True
    except PlaywrightTimeoutError:
        log("CHYBA[UI_CHANGED]: WocaBee opakovane nenašlo očakávaný balík alebo tlačidlo.")
        return False
    except Exception as error:
        log(f"CHYBA balíka: {error}")
        return False


# DOUBLE POINTS
def enable_double_points(page):
    log("")
    log("=== DOUBLE POINTS ===")
    try:
        page.wait_for_selector("#toggleWrapper", timeout=5000)
        toggle = page.locator("#levelToggle")
        if toggle.is_checked():
            log("Double points sú už aktivované.")
            return True
        log("Aktivujem double points...")
        slider = page.locator("#toggleWrapper .slider")
        slider.click(timeout=5000)
        page.wait_for_timeout(500)
        try:
            if toggle.is_checked():
                log("Double points aktivované.")
                return True
        except Exception:
            pass
        log("Double points: kliknutie vykonané.")
        return True
    except Exception as error:
        log(f"VAROVANIE: Double points: {error}")
        return False


# SOLVER
def start_solver(auto_translate):
    log("")
    log("=== SOLVER ===")
    solver_path = os.path.join(BASE_DIR, "solver.py")
    if not os.path.exists(solver_path):
        log(f"CHYBA: solver.py neexistuje: {solver_path}")
        return 1
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    log("Spúšťam solver.py...")
    try:
        process = subprocess.Popen(
            [sys.executable, "-u", solver_path,
             "--auto-translate" if auto_translate else "--no-auto-translate"],
            cwd=BASE_DIR, env=env
        )
        log(f"Solver PID: {process.pid}")
        code = process.wait()
        log(f"Solver ukončený. Exit code: {code}")
        return code
    except Exception as error:
        log(f"CHYBA solvera: {error}")
        return 1


# VYPNUTIE CHROMIUM
def kill_chromium(profile_dir=None):
    log("")
    log("Vypínam Chromium...")
    profile_dir = os.path.abspath(profile_dir or CHROMIUM_PROFILE_DIR)
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                (
                    "Get-CimInstance Win32_Process | "
                    "Where-Object { "
                    "$_.Name -eq 'chrome.exe' -and "
                    "$_.CommandLine -like "
                    f"'*{profile_dir}*' "
                    "} | "
                    "Select-Object -ExpandProperty ProcessId"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        pids = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line.isdigit():
                continue
            pid = int(line)
            if pid > 0:
                pids.append(pid)
        if not pids:
            log("Chromium proces sa nenašiel.")
            return False
        for pid in pids:
            try:
                log(f"Ukončujem Chromium PID: {pid}")
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                )
            except Exception as error:
                log(f"VAROVANIE pri ukončovaní PID {pid}: {error}")
        return True
    except Exception as error:
        log(f"VAROVANIE: Chromium sa nepodarilo ukončiť: {error}")
        return False


# STOP MANAGEMENT
def stop_management():
    log("")
    log("=== STOP MANAGEMENTU ===")
    log("Požiadavka: Uložiť a ukončiť.")
    cfg = load_config()
    if not cfg:
        return 1
    debug_port = get_debug_port(cfg.get("debug_port", "http://localhost:9222"))
    profile_dir = get_chromium_profile_dir(
        cfg.get("urlbase", "https://wocabee.app/app"), cfg.get("username", "")
    )
    log(f"Pripájam sa na Chromium cez CDP: {debug_port}")
    p = None
    browser = None
    try:
        p = sync_playwright().start()
        browser = p.chromium.connect_over_cdp(
            f"http://127.0.0.1:{debug_port}", timeout=5000
        )
        log("Playwright pripojený cez CDP.")
        page = None
        for context in browser.contexts:
            for candidate in context.pages:
                try:
                    if not candidate.is_closed():
                        page = candidate
                        break
                except Exception:
                    continue
            if page is not None:
                break
        if page is None:
            log("CHYBA: Nebola nájdená žiadna otvorená stránka.")
            return 1
        log(f"Aktuálna URL: {page.url}")
        page.set_default_timeout(5000)
        page.set_default_navigation_timeout(5000)
        log("Hľadám tlačidlo #backBtn...")
        button = page.locator("#backBtn")
        try:
            button.wait_for(state="visible", timeout=5000)
        except PlaywrightTimeoutError:
            log("CHYBA: #backBtn sa do 5 sekúnd nenašlo.")
            return 1
        log("Tlačidlo #backBtn nájdené.")
        # ULOŽIŤ A UKONČIŤ
        log("Klikám na „Uložiť a odísť“...")
        try:
            button.evaluate("element => element.click()")
            log("ULOŽIŤ A UKONČIŤ - kliknuté.")
        except Exception as error:
            log(f"CHYBA pri kliknutí na #backBtn: {error}")
            return 1
        # 7 SEKÚND NA ULOŽENIE
        log("")
        log("Čakám 7 sekúnd na dokončenie uloženia...")
        time.sleep(7)
        log("7 sekúnd uplynulo.")
        return 0
    except Exception as error:
        log(f"CHYBA pri zastavovaní: {type(error).__name__}: {error}")
        return 1
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if p is not None:
            try:
                p.stop()
            except Exception:
                pass
        kill_chromium(profile_dir)
        log("Management ukončený.")


# PACKAGES MODE
def packages_mode():
    log("")
    log("============================================================")
    log(" WocaFuckOff™ PACKAGES")
    log("============================================================")
    log("Načítavam config.toml...")
    cfg = load_config()
    if not cfg:
        return 1
    p = None
    browser = None
    try:
        # CONFIG
        try:
            headless = os.environ.get("WOCAFO_PACKAGES_HEADLESS") == "1" or bool(
                cfg.get("headless", False)
            )
            username = str(cfg.get("username", ""))
            password = str(cfg.get("password", ""))
            class_index = int(cfg.get("class_index", 0))
            urlbase = str(cfg.get("urlbase", "https://wocabee.app/app"))
        except (TypeError, ValueError) as error:
            log(f"CHYBA v config.toml: {error}")
            return 1
        if not username or not password:
            log("CHYBA: Username alebo password chýba.")
            return 1
        if not urlbase.startswith(("http://", "https://")):
            urlbase = "https://" + urlbase
        log(f"URL: {urlbase}")
        log(f"Headless: {headless}")
        log(f"Class index: {class_index}")
        # PLAYWRIGHT
        log("")
        log("Spúšťam Playwright...")
        p = sync_playwright().start()
        log("Playwright pripravený.")
        # Package loading owns a separate temporary browser, without a CDP port.
        log("Spúšťam samostatný prehliadač pre načítanie balíkov...")
        browser = p.chromium.launch(headless=headless, args=["--mute-audio"])
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(10000)
        page.set_default_navigation_timeout(15000)
        # WOCABEE
        log("")
        log("Otváram Wocabee...")
        try:
            response = page.goto(urlbase, wait_until="domcontentloaded", timeout=15000)
            if response is not None and response.status >= 400:
                log(f"CHYBA[WOCABEE]: WocaBee vrátilo HTTP {response.status}.")
                return 1
        except PlaywrightTimeoutError:
            log("CHYBA[WOCABEE]: WocaBee sa do 15 sekúnd nenačítalo.")
            return 1
        log(f"Aktuálna URL: {page.url}")
        # PRIHLÁSENIE
        if not login(page, username, password):
            return 1
        # WOCAPOINTS
        report_wocapoints(page)
        # TRIEDA
        if not click_class_by_index(page, class_index):
            return 1
        # WOCAPOINTS - PO VÝBERE TRIEDY
        report_wocapoints(page)
        # BALÍKY
        if not report_packages(page):
            return 1
        return 0
    except KeyboardInterrupt:
        log("Načítanie balíkov prerušené.")
        return 130
    except Exception as error:
        log("")
        log("============================================================")
        log(" FATAL ERROR")
        log("============================================================")
        log(f"{type(error).__name__}: {error}")
        return 1
    finally:
        log("")
        log("Čistím prostredie...")
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if p is not None:
            try:
                p.stop()
            except Exception:
                pass
        log("Management ukončený.")


# MAIN
def main():
    log("")
    log("============================================================")
    log(" WocaFuckOff™ MANAGEMENT")
    log("============================================================")
    log("Načítavam config.toml...")
    cfg = load_config()
    if not cfg:
        return 1
    try:
        headless = bool(cfg.get("headless", False))
        username = str(cfg.get("username", ""))
        password = str(cfg.get("password", ""))
        double_points = bool(cfg.get("double_points", False))
        auto_translate = bool(cfg.get("auto_translate", True))
        class_index = int(cfg.get("class_index", 0))
        selected_package_id = str(cfg.get("selected_package_id", ""))
        urlbase = str(cfg.get("urlbase", "https://wocabee.app/app"))
        debug_port = get_debug_port(cfg.get("debug_port", "http://localhost:9222"))
    except (TypeError, ValueError) as error:
        log(f"CHYBA v config.toml: {error}")
        return 1
    if not username or not password:
        log("CHYBA: Username alebo password chýba.")
        return 1
    if not urlbase.startswith(("http://", "https://")):
        urlbase = "https://" + urlbase
    profile_dir = get_chromium_profile_dir(urlbase, username)
    log(f"URL: {urlbase}")
    log(f"Headless: {headless}")
    log(f"Class index: {class_index}")
    log(f"Selected package ID: {selected_package_id}")
    log(f"Double points: {double_points}")
    log(f"AutoTranslate: {'zapnutý' if auto_translate else 'vypnutý'}")
    log(f"CDP port: {debug_port}")
    if is_port_in_use(debug_port) and not terminate_port_processes(debug_port):
        log("")
        log(f"CHYBA[PORT]: Port {debug_port} je obsadený a proces sa nepodarilo ukončiť.")
        return 1
    p = None
    chromium_process = None
    browser = None
    try:
        # PLAYWRIGHT
        log("")
        log("Spúšťam Playwright...")
        p = sync_playwright().start()
        log("Playwright pripravený.")
        # CHROMIUM
        chromium_process = launch_chromium(p, headless, debug_port, profile_dir)
        log("")
        log("Pripájam Playwright na Chromium cez CDP...")
        browser = p.chromium.connect_over_cdp(
            f"http://127.0.0.1:{debug_port}", timeout=10000
        )
        log("Playwright pripojený cez CDP.")
        # CONTEXT
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
        else:
            context = browser.new_context()
        # PAGE
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = context.new_page()
        page.set_default_timeout(10000)
        page.set_default_navigation_timeout(15000)
        # WOCABEE
        log("")
        log("Otváram Wocabee...")
        try:
            response = page.goto(urlbase, wait_until="domcontentloaded", timeout=15000)
            if response is not None and response.status >= 400:
                log(f"CHYBA[WOCABEE]: WocaBee vrátilo HTTP {response.status}.")
                return 1
        except PlaywrightTimeoutError:
            log("CHYBA[WOCABEE]: WocaBee sa do 15 sekúnd nenačítalo.")
            return 1
        log(f"Aktuálna URL: {page.url}")
        # PRIHLÁSENIE
        if not login(page, username, password):
            return 1
        # WOCAPOINTS - PO PRIHLÁSENÍ
        report_wocapoints(page)
        # TRIEDA
        if not click_class_by_index(page, class_index):
            return 1
        # WOCAPOINTS - PO VÝBERE TRIEDY
        report_wocapoints(page)
        # BALÍK
        if not click_package_by_id(page, selected_package_id):
            return 1
        # WOCAPOINTS - PO VÝBERE BALÍKA
        report_wocapoints(page)
        # DOUBLE POINTS
        if double_points:
            enable_double_points(page)
        # SOLVER
        return start_solver(auto_translate)
    except KeyboardInterrupt:
        log("Management prerušený.")
        return 130
    except Exception as error:
        log("")
        log("============================================================")
        log(" FATAL ERROR")
        log("============================================================")
        log(f"{type(error).__name__}: {error}")
        return 1
    finally:
        log("")
        log("Čistím prostredie...")
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if p is not None:
            try:
                p.stop()
            except Exception:
                pass
        if chromium_process is not None:
            try:
                if chromium_process.poll() is None:
                    chromium_process.terminate()
                    chromium_process.wait(timeout=5)
            except Exception:
                try:
                    chromium_process.kill()
                except Exception:
                    pass
        log("Management ukončený.")


# SPUSTENIE
if __name__ == "__main__":
    if "--stop" in sys.argv:
        sys.exit(stop_management())
    elif "--packages" in sys.argv:
        sys.exit(packages_mode())
    else:
        sys.exit(main())
