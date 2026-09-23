# ============================================================
# SPÚŠŤAČ APLIKÁCIE WOCAFUCKOFF™
# © 2026 Alex Polák
# ============================================================

import ctypes
import importlib.util
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


# ============================================================
# CESTY APLIKÁCIA
# ============================================================

PRIEČINOK_APLIKÁCIE = Path(__file__).resolve().parent

INŠTALÁTOR = PRIEČINOK_APLIKÁCIE / "installer.py"
GUI = PRIEČINOK_APLIKÁCIE / "gui.py"


# ============================================================
# POŽADOVANÉ ZÁVISLOSTI
# ============================================================

POŽADOVANÉ_ZÁVISLOSTI = {
    "PySide6": "PySide6",
    "playwright": "playwright",
    "requests": "requests",
    "toml": "toml",
}


# ============================================================
# KONTROLA VISUAL C++
# ============================================================

def visual_cpp_nainštalované():

    if sys.platform != "win32":
        return True

    try:
        ctypes.WinDLL("msvcp140_1.dll")
        return True

    except OSError:
        return False


# ============================================================
# KONTROLA PYTHON ZÁVISLOSTÍ
# ============================================================

def chýbajúce_závislosti():

    chýbajúce = []

    for modul, balík in POŽADOVANÉ_ZÁVISLOSTI.items():

        try:
            dostupný = importlib.util.find_spec(modul) is not None
        except (ImportError, ValueError):
            dostupný = False

        if not dostupný:
            chýbajúce.append(balík)

    return chýbajúce


# ============================================================
# KONTROLA PRIPRAVENOSTI
# ============================================================

def je_všetko_pripravené():

    if not visual_cpp_nainštalované():
        return False

    if chýbajúce_závislosti():
        return False

    try:
        import PySide6
        return True

    except Exception:
        return False


# ============================================================
# SPUSTENIE INŠTALÁTORA
# ============================================================

def spustiť_inštalátor():

    if not INŠTALÁTOR.exists():
        return False, -1

    try:

        výsledok = subprocess.run(
            [
                sys.executable,
                str(INŠTALÁTOR)
            ],
            cwd=str(PRIEČINOK_APLIKÁCIE),
            check=False
        )

        return (
            výsledok.returncode == 0,
            výsledok.returncode
        )

    except Exception:
        return False, -1


# ============================================================
# ZOBRAZENIE CHYBY
# ============================================================

def zobraziť_chybu(exit_code=None):

    root = tk.Tk()
    root.withdraw()

    problémy = []

    if not visual_cpp_nainštalované():
        problémy.append(
            "Microsoft Visual C++ Redistributable"
        )

    chýbajúce = chýbajúce_závislosti()

    if chýbajúce:
        problémy.append(
            "Chýbajúce Python balíky: "
            + ", ".join(chýbajúce)
        )

    správa = (
        "WocaFuckOff sa nepodarilo pripraviť.\n\n"
    )

    if problémy:
        správa += (
            "Problém:\n- "
            + "\n- ".join(problémy)
            + "\n\n"
        )

    if exit_code is not None:
        správa += (
            f"Kód inštalátora: {exit_code}\n\n"
        )

    správa += (
        "Skontroluj inštaláciu a skús aplikáciu "
        "spustiť znova."
    )

    messagebox.showerror(
        "WocaFuckOff – Chyba",
        správa
    )

    root.destroy()


# ============================================================
# SPUSTENIE HLAVNÉHO PROGRAMU
# ============================================================

def spustiť_hlavný_program():

    if not GUI.exists():

        zobraziť_chybu()

        return

    try:

        subprocess.Popen(
            [
                sys.executable,
                str(GUI)
            ],
            cwd=str(PRIEČINOK_APLIKÁCIE)
        )

    except Exception:

        zobraziť_chybu()


# ============================================================
# HLAVNÁ FUNKCIA
# ============================================================

def main():

    # --------------------------------------------------------
    # APLIKÁCIA JE UŽ PRIPRAVENÁ
    # --------------------------------------------------------

    if je_všetko_pripravené():

        spustiť_hlavný_program()

        return

    # --------------------------------------------------------
    # SPUSTENIE INŠTALÁTORA
    # --------------------------------------------------------

    úspech, exit_code = spustiť_inštalátor()

    if not úspech:

        zobraziť_chybu(exit_code)

        return

    # --------------------------------------------------------
    # KONTROLA PO INŠTALÁCII
    # --------------------------------------------------------

    if not je_všetko_pripravené():

        zobraziť_chybu()

        return

    # --------------------------------------------------------
    # SPUSTENIE APLIKÁCIE
    # --------------------------------------------------------

    spustiť_hlavný_program()


# ============================================================
# SPUSTENIE
# ============================================================

if __name__ == "__main__":
    main()