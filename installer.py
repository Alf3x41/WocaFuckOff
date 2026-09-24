# INSTALLER.PY
# -*- coding: utf-8 -*-
# IMPORTY
import ctypes
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
        subprocess.check_call(
            [
                sys.executable,
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
    výsledok = subprocess.run(
        [sys.executable, "-m", "playwright", "install"], check=False
    )
    if výsledok.returncode != 0:
        raise RuntimeError("Playwright sa nepodarilo pripraviť.")
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


# HLAVNÉ OKNO INŠTALÁTORA
okno = tk.Tk()
okno.title("WocaFuckOff – Príprava")
okno.geometry("560x310")
okno.resizable(False, False)
okno.configure(bg="#101010")
# VYROVNANIE OKNA
okno.update_idletasks()
šírka = 560
výška = 310
obrazovka_šírka = okno.winfo_screenwidth()
obrazovka_výška = okno.winfo_screenheight()
x = (obrazovka_šírka - šírka) // 2
y = (obrazovka_výška - výška) // 2
okno.geometry(f"{šírka}x{výška}+{x}+{y}")
# HLAVNÝ KONTAJNER
hlavný_rám = tk.Frame(okno, bg="#101010")
hlavný_rám.pack(fill="both", expand=True, padx=40, pady=28)
# NADPIS
nadpis = tk.Label(
    hlavný_rám,
    text="WocaFuckOff",
    fg="#ffffff",
    bg="#101010",
    font=("Segoe UI", 28, "bold"),
)
nadpis.pack()
# PODNADPIS
podnadpis = tk.Label(
    hlavný_rám,
    text="Pripravujem aplikáciu na prvé spustenie",
    fg="#777777",
    bg="#101010",
    font=("Segoe UI", 11),
)
podnadpis.pack(pady=(2, 0))
# MEDZERA
tk.Frame(hlavný_rám, height=32, bg="#101010").pack()
# STAV
stav_label = tk.Label(
    hlavný_rám,
    text="Kontrolujem systémové súčasti...",
    fg="#aaaaaa",
    bg="#101010",
    font=("Segoe UI", 10),
)
stav_label.pack()
# PROGRESS BAR
štýl = ttk.Style()
štýl.theme_use("clam")
štýl.configure(
    "Woca.Horizontal.TProgressbar",
    troughcolor="#1c1c1c",
    background="#ffffff",
    bordercolor="#1c1c1c",
    lightcolor="#ffffff",
    darkcolor="#ffffff",
)
priebeh = ttk.Progressbar(
    hlavný_rám,
    style="Woca.Horizontal.TProgressbar",
    orient="horizontal",
    length=420,
    mode="determinate",
    maximum=100,
)
priebeh.pack(pady=(12, 0))
# DETAIL CHYBY
detail_label = tk.Label(
    hlavný_rám,
    text="",
    fg="#555555",
    bg="#101010",
    font=("Segoe UI", 8),
    wraplength=460,
)
detail_label.pack(pady=(10, 0))
# SPODNÁ ČASŤ
spodok = tk.Frame(hlavný_rám, bg="#101010")
spodok.pack(side="bottom", fill="x")
# COPYRIGHT
copyright_label = tk.Label(
    spodok,
    text="© 2026 Alex Polák. Všetky práva vyhradené.",
    fg="#555555",
    bg="#101010",
    font=("Segoe UI", 8),
)
copyright_label.pack(side="right")
# VÝCHODISKOVÝ EXIT CODE
EXIT_CODE = 1
# SPUSTENIE INŠTALÁCIE
vlákno = threading.Thread(target=nainštalovať, daemon=True)
vlákno.start()
# SPUSTENIE OKNA
okno.mainloop()
# UKONČENIE PROGRAMU
sys.exit(EXIT_CODE)
