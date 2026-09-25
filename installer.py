# INSTALLER.PY
# -*- coding: utf-8 -*-
# IMPORTY
import ctypes
import random
import importlib.util
import subprocess
import sys
import tempfile
import threading
import urllib.request
import winreg
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

def overiť_playwright():
    # Import až po inštalácii Python balíkov.
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        # Bežný Chromium používa management pri spustení cez CDP.
        executable = Path(playwright.chromium.executable_path)
        if not executable.is_file():
            raise RuntimeError(f"Chromium neexistuje:\n{executable}")
        # Headless režim používa samostatný binárny súbor. Samotná
        # kontrola chromium.executable_path jeho dostupnosť neoverí.
        browser = playwright.chromium.launch(
            headless=True, timeout=15000, args=["--mute-audio"]
        )
        browser.close()


# POŽADOVANÉ ZÁVISLOSTI
POŽADOVANÉ_BALÍKY = {
    "PySide6": "PySide6",
    "playwright": "playwright",
    "requests": "requests",
    "toml": "toml",
}
# VISUAL C++ REDISTRIBUTABLE
VC_REDIST_X64_URL = "https://aka.ms/vc14/vc_redist.x64.exe"
VC_REDIST_X86_URL = "https://aka.ms/vc14/vc_redist.x86.exe"
# LOG VISUAL C++
VC_REDIST_LOG = Path(tempfile.gettempdir()) / "WocaFuckOff_vc_redist.log"
INSTALL_LOG = Path(tempfile.gettempdir()) / "WocaFuckOff_install.log"


def spustiť_inštalačný_príkaz(argumenty):
    # Výstup ostane dostupný na diagnostiku aj pri spustení cez pythonw.exe.
    with INSTALL_LOG.open("a", encoding="utf-8") as log:
        výsledok = subprocess.run(
            argumenty,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            check=False,
        )
    if výsledok.returncode != 0:
        raise RuntimeError(
            f"Inštalačný príkaz zlyhal (kód {výsledok.returncode}).\nLog: {INSTALL_LOG}"
        )


def python_pre_inštaláciu():
    executable = Path(sys.executable)
    if executable.name.lower() == "pythonw.exe":
        return str(executable.with_name("python.exe"))
    return str(executable)


def spustiť_gui():
    """Spustí GUI po úspešnom dokončení inštalácie."""
    základ = Path(__file__).resolve().parent
    gui_path = základ / "gui.py"
    if not gui_path.is_file():
        raise RuntimeError(f"GUI sa nenašlo:\n{gui_path}")

    python_gui = Path(sys.executable)
    if sys.platform == "win32" and python_gui.name.lower() == "python.exe":
        pythonw = python_gui.with_name("pythonw.exe")
        if pythonw.is_file():
            python_gui = pythonw

    subprocess.Popen(
        [str(python_gui), str(gui_path)],
        cwd=str(základ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=(
            subprocess.CREATE_NEW_PROCESS_GROUP
            if sys.platform == "win32"
            else 0
        ),
    )


# ARCHITEKTÚRA
def python_je_64_bit():
    return sys.maxsize > 2**32


# VÝBER URL
def visual_cpp_url():
    if python_je_64_bit():
        return VC_REDIST_X64_URL
    return VC_REDIST_X86_URL


# KONTROLA VISUAL C++ DLL
def visual_cpp_dll_funguje():
    if sys.platform != "win32":
        return True
    try:
        ctypes.WinDLL("msvcp140_1.dll")
        return True
    except OSError:
        return False


# KONTROLA VISUAL C++ REGISTRY
def visual_cpp_registry():
    if sys.platform != "win32":
        return True
    kľúčové_cesty = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\VisualStudio"
            r"\14.0\VC\Runtimes\x64",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Wow6432Node\Microsoft"
            r"\VisualStudio\14.0\VC\Runtimes\x64",
        ),
    ]
    for root, cesta in kľúčové_cesty:
        try:
            with winreg.OpenKey(root, cesta, 0, winreg.KEY_READ) as kľúč:
                installed = winreg.QueryValueEx(kľúč, "Installed")[0]
                if installed == 1:
                    return True
        except (FileNotFoundError, PermissionError, OSError):
            pass
    return False


# KONTROLA VISUAL C++
def visual_cpp_nainštalované():
    return visual_cpp_registry() and visual_cpp_dll_funguje()


# KONTROLA PYTHON ZÁVISLOSTÍ
def chýbajúce_závislosti():
    chýbajúce = []
    for modul, balík in POŽADOVANÉ_BALÍKY.items():
        if importlib.util.find_spec(modul) is None:
            chýbajúce.append(balík)
    return chýbajúce


# AKTUALIZÁCIA STAVU
def aktualizovať_stav(text):
    okno.after(0, lambda: stav_label.config(text=text))


# AKTUALIZÁCIA PRIEBEHU
def aktualizovať_priebeh(hodnota):
    okno.after(0, lambda: priebeh.config(value=hodnota))


# STIAHNUTIE VISUAL C++
def stiahnuť_visual_cpp():
    cieľ = Path(tempfile.gettempdir()) / "WocaFuckOff_vc_redist.x64.exe"
    aktualizovať_stav("Sťahujem Microsoft Visual C++ Runtime...")
    požiadavka = urllib.request.Request(
        visual_cpp_url(), headers={"User-Agent": "WocaFuckOff/1.0"}
    )
    with urllib.request.urlopen(požiadavka, timeout=120) as odpoveď:
        celková_veľkosť = odpoveď.headers.get("Content-Length")
        if celková_veľkosť:
            celková_veľkosť = int(celková_veľkosť)
        else:
            celková_veľkosť = 0
        stiahnuté = 0
        with open(cieľ, "wb") as súbor:
            while True:
                dáta = odpoveď.read(64 * 1024)
                if not dáta:
                    break
                súbor.write(dáta)
                stiahnuté += len(dáta)
                if celková_veľkosť:
                    percentá = int((stiahnuté / celková_veľkosť) * 20)
                    aktualizovať_priebeh(min(percentá, 20))
    return cieľ


# SPUSTENIE AKO SPRÁVCA
def spustiť_ako_správca(cesta, parametre):
    powershell_príkaz = (
        "$proces = Start-Process "
        f"-FilePath '{str(cesta).replace("'", "''")}' "
        f"-ArgumentList '{parametre.replace("'", "''")}' "
        "-Verb RunAs "
        "-WindowStyle Hidden "
        "-Wait "
        "-PassThru; "
        "exit $proces.ExitCode"
    )
    výsledok = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            powershell_príkaz,
        ],
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return výsledok.returncode


# INŠTALÁCIA VISUAL C++
def nainštalovať_visual_cpp():
    if visual_cpp_nainštalované():
        aktualizovať_stav("Microsoft Visual C++ je pripravený.")
        aktualizovať_priebeh(30)
        return
    aktualizovať_stav("Microsoft Visual C++ chýba.")
    inštalátor = None
    try:
        inštalátor = stiahnuť_visual_cpp()
        aktualizovať_stav("Inštalujem Microsoft Visual C++ Runtime...")
        parametre = f'/install /quiet /norestart /log "{VC_REDIST_LOG}"'
        exit_code = spustiť_ako_správca(inštalátor, parametre)
        # KONTROLA PO INŠTALÁCII
        aktualizovať_stav("Overujem Microsoft Visual C++...")
        if visual_cpp_nainštalované():
            aktualizovať_priebeh(30)
            return
        # INŠTALÁCIA ZLYHALA
        raise RuntimeError(
            "Microsoft Visual C++ sa "
            "nepodarilo nainštalovať.\n\n"
            f"Kód installeru: {exit_code}\n\n"
            f"Log:\n{VC_REDIST_LOG}"
        )
    except Exception:
        raise
    finally:
        # EXE NECHÁME PRE DEBUGOVANIE
        pass


# INŠTALÁCIA PYTHON BALÍKOV
def nainštalovať_python_balíky():
    chýbajúce = chýbajúce_závislosti()
    if not chýbajúce:
        aktualizovať_priebeh(75)
        return
    počet = len(chýbajúce)
    for index, balík in enumerate(chýbajúce, 1):
        aktualizovať_stav(f"Inštalujem {balík}...")
        spustiť_inštalačný_príkaz(
            [
                python_pre_inštaláciu(),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                balík,
            ]
        )
        percentá = 30 + int((index / počet) * 45)
        aktualizovať_priebeh(percentá)


# OVERENIE PYSIDE6
def overiť_pyside6():
    try:
        from PySide6 import QtWidgets

        return QtWidgets.QApplication is not None
    except Exception:
        return False


# INŠTALÁCIA PLAYWRIGHT
def nainštalovať_playwright():
    aktualizovať_stav("Pripravujem Playwright...")
    spustiť_inštalačný_príkaz(
        [python_pre_inštaláciu(), "-m", "playwright", "install", "chromium"]
    )
    aktualizovať_stav("Overujem spustenie Chromium...")
    overiť_playwright()
    aktualizovať_priebeh(100)


# HLAVNÁ INŠTALAČNÁ FUNKCIA
def nainštalovať():
    try:
        # 1. VISUAL C++
        nainštalovať_visual_cpp()
        # 2. PYTHON BALÍKY
        nainštalovať_python_balíky()
        # 3. PYSIDE6
        aktualizovať_stav("Overujem PySide6...")
        if not overiť_pyside6():
            raise RuntimeError("PySide6 sa nepodarilo načítať.")
        # 4. PLAYWRIGHT
        nainštalovať_playwright()
        # 5. HOTOVO
        aktualizovať_stav("Všetko je pripravené.")
        aktualizovať_priebeh(100)
        okno.after(800, dokončiť_inštaláciu)
    except Exception as chyba:
        okno.after(0, lambda chyba=chyba: zobraziť_chybu(chyba))


# DOKONČENIE INŠTALÁCIE
def dokončiť_inštaláciu():
    global EXIT_CODE
    EXIT_CODE = 0
    okno.destroy()


# ZOBRAZENIE CHYBY
def zobraziť_chybu(chyba):
    global EXIT_CODE
    EXIT_CODE = 1
    stav_label.config(text="Inštaláciu sa nepodarilo dokončiť.")
    priebeh.config(value=0)
    detail_label.config(text=str(chyba))
    messagebox.showerror("WocaFuckOff – Chyba", f"Inštalácia zlyhala:\n\n{chyba}")
    okno.destroy()


class TextNaPlatne:
    """Text nad šumom s rovnakým rozhraním config ako pôvodný Label."""

    def __init__(self, platno, x, y, **options):
        self.platno = platno
        self.item = platno.create_text(x, y, **options)

    def config(self, **options):
        self.platno.itemconfigure(self.item, **options)


def vytvoriť_okno():
    global okno, stav_label, priebeh, detail_label
    okno = tk.Tk()
    okno.title("WocaFuckOff – Príprava")
    okno.prázdna_ikona = tk.PhotoImage(width=16, height=16)
    okno.iconphoto(True, okno.prázdna_ikona)
    okno.resizable(False, False)
    šírka, výška = 560, 350
    x = (okno.winfo_screenwidth() - šírka) // 2
    y = (okno.winfo_screenheight() - výška) // 2
    okno.geometry(f"{šírka}x{výška}+{x}+{y}")
    platno = tk.Canvas(okno, width=šírka, height=výška, highlightthickness=0, bg="#111318")
    platno.pack(fill="both", expand=True)
    # Textúra nevyžaduje Pillow ani ďalšiu inštalovanú knižnicu.
    rng = random.Random(42)
    dlaždica = [rng.randrange(0, 8) for _ in range(64 * 64)]
    pixely = bytearray()
    for y in range(výška):
        for x in range(šírka):
            alfa = dlaždica[(y % 64) * 64 + x % 64]
            pixely.extend(round(základ + (255 - základ) * alfa / 255) for základ in (17, 19, 24))
    data = f"P6\n{šírka} {výška}\n255\n".encode("ascii") + bytes(pixely)
    platno.textura = tk.PhotoImage(data=data, format="PPM")
    platno.create_image(0, 0, image=platno.textura, anchor="nw")
    platno.create_text(280, 58, text="WocaFuckOff", fill="#e0e6ef", font=("Segoe UI", 28, "bold"))
    platno.create_text(280, 96, text="Pripravujem aplikáciu na prvé spustenie", fill="#999999", font=("Segoe UI", 11))
    stav_label = TextNaPlatne(platno, 280, 156, text="Kontrolujem systémové súčasti...", fill="#cccccc", font=("Segoe UI", 10), width=480)
    štýl = ttk.Style()
    štýl.theme_use("clam")
    štýl.configure(
        "Woca.Horizontal.TProgressbar", troughcolor="#1d2129", background="#e0e6ef",
        bordercolor="#303743", lightcolor="#e0e6ef", darkcolor="#e0e6ef",
    )
    priebeh = ttk.Progressbar(platno, style="Woca.Horizontal.TProgressbar", orient="horizontal", length=420, mode="determinate", maximum=100)
    platno.create_window(280, 190, window=priebeh, width=420, height=8)
    platno.create_text(
        280, 230,
        text="Inštalácia závislostí môže trvať niekoľko minút.\nPriebeh sa počas niektorých krokov nemusí meniť.\nPočkajte, prosím, na dokončenie a nezatvárajte toto okno.",
        fill="#a0a8b5", font=("Segoe UI", 9), width=480, justify="center",
    )
    detail_label = TextNaPlatne(platno, 280, 284, text="", fill="#999999", font=("Segoe UI", 8), width=460)
    platno.create_text(530, 326, anchor="e", text="© 2026 Alex Polák. Všetky práva vyhradené.", fill="#777777", font=("Segoe UI", 8))


# HLAVNÉ OKNO INŠTALÁTORA
if __name__ == "__main__":
    vytvoriť_okno()
    EXIT_CODE = 1
    vlákno = threading.Thread(target=nainštalovať, daemon=True)
    vlákno.start()
    okno.mainloop()
    if EXIT_CODE == 0:
        try:
            spustiť_gui()
        except Exception as chyba:
            EXIT_CODE = 1
            messagebox.showerror(
                "WocaFuckOff – Chyba",
                f"Inštalácia bola dokončená, ale GUI sa nepodarilo spustiť:\n\n{chyba}",
            )
    sys.exit(EXIT_CODE)
