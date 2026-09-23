# ============================================================
# MANAGEMENT.PY
# ============================================================

# -*- coding: utf-8 -*-

import os
import sys
import signal
import subprocess
import socket
import time
import urllib.request
import urllib.error

import toml

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


# ============================================================
# UTF-8 VÝSTUP
# ============================================================

if sys.stdout is not None:
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="backslashreplace",
        line_buffering=True,
    )

if sys.stderr is not None:
    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="backslashreplace",
        line_buffering=True,
    )


# ============================================================
# CESTY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CONFIG_FILE = os.path.join(
    BASE_DIR,
    "config.toml",
)


# ============================================================
# LOG
# ============================================================

def log(*args):
    print(*args, flush=True)


# ============================================================
# CONFIG
# ============================================================

def load_config():
    if not os.path.exists(CONFIG_FILE):
        log(
            f"CHYBA: config.toml neexistuje: {CONFIG_FILE}"
        )
        return {}

    try:
        return toml.load(CONFIG_FILE)

    except Exception as error:
        log(
            f"CHYBA pri načítaní config.toml: {error}"
        )
        return {}


# ============================================================
# DEBUG PORT
# ============================================================

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
            return int(
                value.rsplit(":", 1)[1]
            )
        except Exception:
            pass

    try:
        return int(value)

    except Exception:
        return 9222


# ============================================================
# PORT
# ============================================================

def is_port_in_use(port):
    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    sock.settimeout(0.5)

    try:
        return (
            sock.connect_ex(
                ("127.0.0.1", port)
            )
            == 0
        )

    finally:
        sock.close()


# ============================================================
# ČAKANIE NA CDP
# ============================================================

def wait_for_cdp(port, timeout=15):
    url = (
        f"http://127.0.0.1:{port}"
        "/json/version"
    )

    log(
        f"Čakám na CDP: {url}"
    )

    started = time.time()

    while (
        time.time() - started
        < timeout
    ):
        try:
            with urllib.request.urlopen(
                url,
                timeout=1,
            ) as response:

                if response.status == 200:
                    log(
                        "CDP je pripravené."
                    )
                    return True

        except (
            urllib.error.URLError,
            ConnectionError,
            TimeoutError,
            OSError,
        ):
            pass

        time.sleep(0.25)

    log(
        "CHYBA: CDP sa do "
        f"{timeout} sekúnd nespustilo."
    )

    return False


# ============================================================
# SPUSTENIE CHROMIUM
# ============================================================

def launch_chromium(p, headless, port):
    log("")
    log(
        "=== CHROMIUM ==="
    )

    executable = p.chromium.executable_path

    log(
        f"Chromium executable:"
    )

    log(
        executable
    )

    if not executable:
        raise RuntimeError(
            "Playwright neposkytol cestu k Chromium."
        )

    if not os.path.exists(executable):
        raise RuntimeError(
            "Chromium executable neexistuje:\n"
            f"{executable}"
        )

    # --------------------------------------------------------
    # Dočasný profil
    # --------------------------------------------------------

    profile_dir = os.path.join(
        BASE_DIR,
        ".wocafuckoff_chromium",
    )

    os.makedirs(
        profile_dir,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Argumenty
    # --------------------------------------------------------

    args = [
        executable,

        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",

        f"--user-data-dir={profile_dir}",

        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-popup-blocking",

        "--no-sandbox",
    ]

    if headless:
        args.append(
            "--headless=new"
        )

    log("")
    log(
        "Spúšťam Chromium ako samostatný proces..."
    )

    log(
        f"CDP port: {port}"
    )

    log(
        f"Headless: {headless}"
    )

    log(
        "Profil:"
    )

    log(
        profile_dir
    )

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    process = subprocess.Popen(
        args,
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=(
            subprocess.CREATE_NEW_PROCESS_GROUP
            if os.name == "nt"
            else 0
        ),
    )

    log(
        f"Chromium PID: {process.pid}"
    )

    # --------------------------------------------------------
    # CDP
    # --------------------------------------------------------

    if not wait_for_cdp(
        port,
        timeout=15,
    ):
        try:
            process.terminate()
        except Exception:
            pass

        raise RuntimeError(
            "Chromium sa spustilo, ale "
            "CDP port neodpovedá."
        )

    return process


# ============================================================
# PRIHLÁSENIE
# ============================================================

def login(page, username, password):
    log("")
    log(
        "=== PRIHLÁSENIE ==="
    )

    # --------------------------------------------------------
    # UŽ SME PRIHLÁSENÍ
    # --------------------------------------------------------

    if "/student" in page.url.lower():
        log(
            "Používateľ je už prihlásený."
        )

        log(
            f"Aktuálna URL: {page.url}"
        )

        return True

    # --------------------------------------------------------
    # LOGIN FORM
    # --------------------------------------------------------

    try:
        log(
            "Hľadám #login..."
        )

        page.wait_for_selector(
            "#login",
            timeout=10000,
        )

        page.fill(
            "#login",
            username,
        )

        log(
            "Username vyplnený."
        )

    except PlaywrightTimeoutError:
        log(
            "CHYBA: #login sa nenašiel."
        )
        return False

    except Exception as error:
        log(
            f"CHYBA username: {error}"
        )
        return False

    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------

    try:
        log(
            "Hľadám #password..."
        )

        page.wait_for_selector(
            "#password",
            timeout=10000,
        )

        page.fill(
            "#password",
            password,
        )

        log(
            "Password vyplnený."
        )

    except PlaywrightTimeoutError:
        log(
            "CHYBA: #password sa nenašiel."
        )
        return False

    except Exception as error:
        log(
            f"CHYBA password: {error}"
        )
        return False

    # --------------------------------------------------------
    # PRIHLÁSENIE
    # --------------------------------------------------------

    try:
        page.press(
            "#password",
            "Enter",
        )

        log(
            "Prihlasovacie údaje odoslané."
        )

    except Exception as error:
        log(
            f"CHYBA pri prihlasovaní: {error}"
        )
        return False

    # --------------------------------------------------------
    # ČAKANIE NA REDIRECT
    # --------------------------------------------------------

    log(
        "Čakám na prihlásenie..."
    )

    try:
        page.wait_for_url(
            "**/student/**",
            timeout=15000,
        )

        log(
            "Prihlásenie úspešné."
        )

    except PlaywrightTimeoutError:
        log(
            f"VAROVANIE: Redirect sa nepotvrdil. URL: {page.url}"
        )

        if "/student" not in page.url.lower():
            return False

    log(
        f"Aktuálna URL: {page.url}"
    )

    return True


# ============================================================
# TRIEDA
# ============================================================

def click_class_by_index(page, index):
    log("")
    log(
        "=== VÝBER TRIEDY ==="
    )

    log(
        f"Index triedy: {index}"
    )

    try:
        page.wait_for_selector(
            "#listOfClasses a",
            timeout=10000,
        )

        classes = page.locator(
            "#listOfClasses a"
        )

        count = classes.count()

        log(
            f"Nájdených tried: {count}"
        )

        if count == 0:
            log(
                "CHYBA: Žiadne triedy."
            )
            return False

        if index < 0 or index >= count:
            log(
                f"CHYBA: Index {index} "
                f"je mimo rozsahu 0-{count - 1}."
            )
            return False

        log(
            f"Klikám na triedu {index}..."
        )

        classes.nth(index).click(
            timeout=10000
        )

        page.wait_for_timeout(
            700
        )

        log(
            "Trieda vybraná."
        )

        return True

    except PlaywrightTimeoutError:
        log(
            "CHYBA: Triedy sa nenašli."
        )
        return False

    except Exception as error:
        log(
            f"CHYBA triedy: {error}"
        )
        return False


# ============================================================
# BALÍK
# ============================================================

def click_package_by_index(page, index):
    log("")
    log(
        "=== VÝBER BALÍKA ==="
    )

    log(
        f"Index balíka: {index}"
    )

    try:
        page.wait_for_selector(
            "tr.pTableRow",
            timeout=10000,
        )

        packages = page.locator(
            "tr.pTableRow"
        )

        count = packages.count()

        log(
            f"Nájdených balíkov: {count}"
        )

        if count == 0:
            log(
                "CHYBA: Žiadne balíky."
            )
            return False

        if index < 0 or index >= count:
            log(
                f"CHYBA: Index {index} "
                f"je mimo rozsahu 0-{count - 1}."
            )
            return False

        package = packages.nth(
            index
        )

        button = package.locator(
            "a .btn-primary"
        )

        log(
            "Čakám na tlačidlo balíka..."
        )

        button.wait_for(
            state="visible",
            timeout=10000,
        )

        log(
            "Klikám na balík..."
        )

        button.click(
            timeout=10000
        )

        page.wait_for_timeout(
            700
        )

        log(
            "Balík vybraný."
        )

        return True

    except PlaywrightTimeoutError:
        log(
            "CHYBA: Balík alebo tlačidlo "
            "sa nenašlo."
        )
        return False

    except Exception as error:
        log(
            f"CHYBA balíka: {error}"
        )
        return False


# ============================================================
# DOUBLE POINTS
# ============================================================

def enable_double_points(page):
    log("")
    log(
        "=== DOUBLE POINTS ==="
    )

    try:
        page.wait_for_selector(
            "#toggleWrapper",
            timeout=5000,
        )

        toggle = page.locator(
            "#levelToggle"
        )

        if toggle.is_checked():
            log(
                "Double points sú už aktivované."
            )
            return True

        log(
            "Aktivujem double points..."
        )

        slider = page.locator(
            "#toggleWrapper .slider"
        )

        slider.click(
            timeout=5000
        )

        page.wait_for_timeout(
            500
        )

        try:
            if toggle.is_checked():
                log(
                    "Double points aktivované."
                )
                return True
        except Exception:
            pass

        log(
            "Double points: kliknutie vykonané."
        )

        return True

    except Exception as error:
        log(
            f"VAROVANIE: Double points: {error}"
        )
        return False


# ============================================================
# SOLVER
# ============================================================

def start_solver():
    log("")
    log(
        "=== SOLVER ==="
    )

    solver_path = os.path.join(
        BASE_DIR,
        "solver.py",
    )

    if not os.path.exists(
        solver_path
    ):
        log(
            f"CHYBA: solver.py neexistuje: "
            f"{solver_path}"
        )
        return 1

    env = os.environ.copy()

    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    log(
        "Spúšťam solver.py..."
    )

    try:
        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                solver_path,
            ],
            cwd=BASE_DIR,
            env=env,
        )

        log(
            f"Solver PID: {process.pid}"
        )

        code = process.wait()

        log(
            f"Solver ukončený. Exit code: {code}"
        )

        return code

    except Exception as error:
        log(
            f"CHYBA solvera: {error}"
        )
        return 1


# ============================================================
# STOP
# ============================================================

def stop_management():
    log(
        "Zastavujem management..."
    )

    try:
        os.kill(
            os.getpid(),
            signal.SIGTERM,
        )
    except Exception:
        sys.exit(0)


# ============================================================
# MAIN
# ============================================================

def main():
    log("")
    log(
        "============================================================"
    )
    log(
        " WocaFuckOff™ MANAGEMENT"
    )
    log(
        "============================================================"
    )

    # --------------------------------------------------------
    # CONFIG
    # --------------------------------------------------------

    log(
        "Načítavam config.toml..."
    )

    cfg = load_config()

    if not cfg:
        return 1

    headless = bool(
        cfg.get(
            "headless",
            False,
        )
    )

    username = str(
        cfg.get(
            "username",
            "",
        )
    )

    password = str(
        cfg.get(
            "password",
            "",
        )
    )

    double_points = bool(
        cfg.get(
            "double_points",
            False,
        )
    )

    class_index = int(
        cfg.get(
            "class_index",
            0,
        )
    )

    package_index = int(
        cfg.get(
            "package_index",
            0,
        )
    )

    urlbase = str(
        cfg.get(
            "urlbase",
            "https://wocabee.app/app",
        )
    )

    debug_port = get_debug_port(
        cfg.get(
            "debug_port",
            "http://localhost:9222",
        )
    )

    if not username or not password:
        log(
            "CHYBA: Username alebo password chýba."
        )
        return 1

    if not urlbase.startswith(
        (
            "http://",
            "https://",
        )
    ):
        urlbase = (
            "https://" + urlbase
        )

    log(
        f"URL: {urlbase}"
    )

    log(
        f"Headless: {headless}"
    )

    log(
        f"Class index: {class_index}"
    )

    log(
        f"Package index: {package_index}"
    )

    log(
        f"Double points: {double_points}"
    )

    log(
        f"CDP port: {debug_port}"
    )

    # --------------------------------------------------------
    # PORT
    # --------------------------------------------------------

    if is_port_in_use(
        debug_port
    ):
        log("")
        log(
            f"CHYBA: Port {debug_port} "
            "je už používaný."
        )
        return 1

    # --------------------------------------------------------
    # PLAYWRIGHT
    # --------------------------------------------------------

    p = None
    chromium_process = None
    browser = None

    try:
        log("")
        log(
            "Spúšťam Playwright..."
        )

        p = sync_playwright().start()

        log(
            "Playwright pripravený."
        )

        # ----------------------------------------------------
        # CHROMIUM
        # ----------------------------------------------------

        chromium_process = launch_chromium(
            p,
            headless,
            debug_port,
        )

        # ----------------------------------------------------
        # CONNECT OVER CDP
        # ----------------------------------------------------

        log("")
        log(
            "Pripájam Playwright na Chromium cez CDP..."
        )

        browser = p.chromium.connect_over_cdp(
            f"http://127.0.0.1:{debug_port}",
            timeout=10000,
        )

        log(
            "Playwright pripojený cez CDP."
        )

        # ----------------------------------------------------
        # CONTEXT
        # ----------------------------------------------------

        contexts = browser.contexts

        if contexts:
            context = contexts[0]
        else:
            context = browser.new_context()

        pages = context.pages

        if pages:
            page = pages[0]
        else:
            page = context.new_page()

        page.set_default_timeout(
            10000
        )

        page.set_default_navigation_timeout(
            15000
        )

        # ----------------------------------------------------
        # WOCABEE
        # ----------------------------------------------------

        log("")
        log(
            "Otváram WocaBee..."
        )

        try:
            page.goto(
                urlbase,
                wait_until="domcontentloaded",
                timeout=15000,
            )

        except PlaywrightTimeoutError:
            log(
                "VAROVANIE: WocaBee prekročilo "
                "15 s timeout."
            )

        log(
            f"Aktuálna URL: {page.url}"
        )

        # ----------------------------------------------------
        # LOGIN
        # ----------------------------------------------------

        if not login(
            page,
            username,
            password,
        ):
            return 1

        # ----------------------------------------------------
        # TRIEDA
        # ----------------------------------------------------

        if not click_class_by_index(
            page,
            class_index,
        ):
            return 1

        # ----------------------------------------------------
        # BALÍK
        # ----------------------------------------------------

        if not click_package_by_index(
            page,
            package_index,
        ):
            return 1

        # ----------------------------------------------------
        # DOUBLE POINTS
        # ----------------------------------------------------

        if double_points:
            enable_double_points(
                page
            )

        # ----------------------------------------------------
        # SOLVER
        # ----------------------------------------------------

        return start_solver()

    except KeyboardInterrupt:
        log(
            "Management prerušený."
        )
        return 130

    except Exception as error:
        log("")
        log(
            "============================================================"
        )
        log(
            " FATAL ERROR"
        )
        log(
            "============================================================"
        )
        log(
            f"{type(error).__name__}: {error}"
        )
        return 1

    finally:
        log("")
        log(
            "Čistím prostredie..."
        )

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
                    chromium_process.wait(
                        timeout=5
                    )
            except Exception:
                try:
                    chromium_process.kill()
                except Exception:
                    pass

        log(
            "Management ukončený."
        )


# ============================================================
# SPUSTENIE
# ============================================================

if __name__ == "__main__":
    if "--stop" in sys.argv:
        stop_management()
    else:
        sys.exit(
            main()
        )
