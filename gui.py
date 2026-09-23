# ============================================================
# GUI.PY
# WocaFuckOff™
# ============================================================

# -*- coding: utf-8 -*-

import sys
import random
import subprocess
import json
import re
import toml

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    QProcess,
)

from PySide6.QtGui import QPainter, QPen

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QProgressBar,
    QGraphicsOpacityEffect,
    QDialog,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QFormLayout,
    QScrollArea,
    QPlainTextEdit,
    QMessageBox,
)


# ============================================================
# QSPINBOX BEZ SCROLLU
# ============================================================

class NoScrollSpinBox(QSpinBox):

    def wheelEvent(self, event):
        event.ignore()


# ============================================================
# TLAČIDLO MENU
# ============================================================

class MenuButton(QPushButton):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.is_open = False

        self.setFixedSize(
            48,
            48
        )

        self.setObjectName(
            "menuButton"
        )

    def set_open(self, state):

        self.is_open = state

        self.update()

    def paintEvent(self, event):

        super().paintEvent(event)

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        pen = QPen(Qt.white)

        pen.setWidth(2)

        pen.setCapStyle(
            Qt.RoundCap
        )

        painter.setPen(pen)

        center_x = self.width() // 2
        center_y = self.height() // 2

        if not self.is_open:

            painter.drawLine(
                center_x - 9,
                center_y - 7,
                center_x + 9,
                center_y - 7
            )

            painter.drawLine(
                center_x - 9,
                center_y,
                center_x + 9,
                center_y
            )

            painter.drawLine(
                center_x - 9,
                center_y + 7,
                center_x + 9,
                center_y + 7
            )

        else:

            painter.drawLine(
                center_x - 8,
                center_y - 8,
                center_x + 8,
                center_y + 8
            )

            painter.drawLine(
                center_x + 8,
                center_y - 8,
                center_x - 8,
                center_y + 8
            )


# ============================================================
# HLAVNÁ APLIKÁCIA
# ============================================================

class WocaFuckOff(QMainWindow):

    # ========================================================
    # SPUSTENIE APLIKÁCIE
    # ========================================================

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "WocaFuckOff"
        )

        self.setFixedSize(
            900,
            600
        )

        self.menu_open = False

        self.management_process = None
        self.management_output_buffer = ""
        self.management_stopping = False

        self.stop_process = None
        self.stop_output_buffer = ""

        # ====================================================
        # EVENT LOG
        # ====================================================

        self.event_log = []

        try:

            self.get_events_path().write_text(
                "",
                encoding="utf-8"
            )

        except Exception:

            pass

        self.events_dialog = None
        self.events_text = None

        self.events_timer = QTimer(self)

        self.events_timer.setInterval(
            500
        )

        self.events_timer.timeout.connect(
            self.refresh_events_view
        )

        self.events_timer.start()

        self.add_event(
            "Aplikácia spustená"
        )

        self.account_name = "—"
        self.points_value = None

        self.build_boot_screen()

    # ========================================================
    # CESTY
    # ========================================================

    def get_base_path(self):

        return (
            Path(sys.executable).resolve().parent
            if getattr(self, "frozen", False)
            else Path(__file__).resolve().parent
        )

    def get_config_path(self):

        return (
            self.get_base_path()
            / "config.toml"
        )

    # ========================================================
    # BOOTOVACIA OBRAZOVKA
    # ========================================================

    def build_boot_screen(self):

        self.boot_widget = QWidget()

        self.boot_widget.setObjectName(
            "bootWidget"
        )

        self.setCentralWidget(
            self.boot_widget
        )

        boot_layout = QVBoxLayout(
            self.boot_widget
        )

        boot_layout.setContentsMargins(
            40,
            40,
            40,
            40
        )

        boot_layout.addStretch()

        self.boot_title = QLabel(
            "WocaFuckOff"
        )

        self.boot_title.setObjectName(
            "bootTitle"
        )

        self.boot_title.setAlignment(
            Qt.AlignCenter
        )

        boot_layout.addWidget(
            self.boot_title
        )

        self.boot_subtitle = QLabel(
            "Automatizácia Wocabee"
        )

        self.boot_subtitle.setObjectName(
            "bootSubtitle"
        )

        self.boot_subtitle.setAlignment(
            Qt.AlignCenter
        )

        boot_layout.addWidget(
            self.boot_subtitle
        )

        boot_layout.addSpacing(
            45
        )

        self.boot_status = QLabel(
            "Spúšťam WocaFuckOff..."
        )

        self.boot_status.setObjectName(
            "bootStatus"
        )

        self.boot_status.setAlignment(
            Qt.AlignCenter
        )

        boot_layout.addWidget(
            self.boot_status
        )

        boot_layout.addSpacing(
            12
        )

        self.progress = QProgressBar()

        self.progress.setObjectName(
            "bootProgress"
        )

        self.progress.setRange(
            0,
            100
        )

        self.progress.setValue(
            0
        )

        self.progress.setTextVisible(
            False
        )

        self.progress.setFixedHeight(
            6
        )

        boot_layout.addWidget(
            self.progress
        )

        boot_layout.addStretch()

        self.apply_boot_styles()

        self.boot_opacity = QGraphicsOpacityEffect()

        self.boot_widget.setGraphicsEffect(
            self.boot_opacity
        )

        self.boot_opacity.setOpacity(
            0
        )

        self.boot_fade = QPropertyAnimation(
            self.boot_opacity,
            b"opacity"
        )

        self.boot_fade.setDuration(
            700
        )

        self.boot_fade.setStartValue(
            0
        )

        self.boot_fade.setEndValue(
            1
        )

        self.boot_fade.setEasingCurve(
            QEasingCurve.OutCubic
        )

        self.boot_fade.start()

        self.progress_animation = QPropertyAnimation(
            self.progress,
            b"value"
        )

        self.progress_animation.setDuration(
            6000
        )

        self.progress_animation.setStartValue(
            0
        )

        self.progress_animation.setEndValue(
            100
        )

        self.progress_animation.setEasingCurve(
            QEasingCurve.InOutCubic
        )

        self.progress_animation.start()

        QTimer.singleShot(
            1400,
            lambda: self.boot_status.setText(
                "Inicializujem komponenty..."
            )
        )

        QTimer.singleShot(
            2600,
            lambda: self.boot_status.setText(
                "Načítavam automatizáciu..."
            )
        )

        QTimer.singleShot(
            4000,
            lambda: self.boot_status.setText(
                "Overujem pripravenosť systému..."
            )
        )

        QTimer.singleShot(
            5000,
            lambda: self.boot_status.setText(
                "Dokončujem inicializáciu..."
            )
        )

        QTimer.singleShot(
            6000,
            lambda: self.boot_status.setText(
                "Systém je pripravený."
            )
        )

        QTimer.singleShot(
            6000,
            self.show_main_ui
        )

    # ========================================================
    # ZOBRAZENIE HLAVNÉHO ROZHRANIA
    # ========================================================

    def show_main_ui(self):

        self.build_ui()

        self.main_opacity = QGraphicsOpacityEffect()

        self.centralWidget().setGraphicsEffect(
            self.main_opacity
        )

        self.main_opacity.setOpacity(
            0
        )

        self.main_fade = QPropertyAnimation(
            self.main_opacity,
            b"opacity"
        )

        self.main_fade.setDuration(
            700
        )

        self.main_fade.setStartValue(
            0
        )

        self.main_fade.setEndValue(
            1
        )

        self.main_fade.setEasingCurve(
            QEasingCurve.OutCubic
        )

        self.main_fade.start()

    # ========================================================
    # HLAVNÉ ROZHRANIE
    # ========================================================

    def build_ui(self):

        central = QWidget()

        central.setObjectName(
            "central"
        )

        self.setCentralWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            32,
            28,
            32,
            28
        )

        main_layout.setSpacing(
            20
        )

        header = QHBoxLayout()

        self.menu_button = MenuButton()

        self.menu_button.clicked.connect(
            self.toggle_menu
        )

        title_layout = QVBoxLayout()

        title_layout.setSpacing(
            0
        )

        title = QLabel(
            "WocaFuckOff"
        )

        title.setObjectName(
            "title"
        )

        subtitle = QLabel(
            "Automatizácia Wocabee"
        )

        subtitle.setObjectName(
            "subtitle"
        )

        title_layout.addWidget(
            title
        )

        title_layout.addWidget(
            subtitle
        )

        header.addWidget(
            self.menu_button
        )

        header.addLayout(
            title_layout
        )

        header.addStretch()

        main_layout.addLayout(
            header
        )

        main_layout.addStretch()

        messages = [
            "Ty nič nerob.",
            "Nechaj to na mňa.",
            "Automatizácia aktivovaná.",
            "Dnes to za teba spravím ja.",
            "Mozog môže oddychovať.",
            "Práca? Nechaj ju mne.",
            "Ty len sleduj.",
            "O zvyšok sa postarám.",
            "Nemusíš nič robiť.",
            "Stačí ma spustiť.",
            "Ty si svoje už spravil.",
            "Odteraz makám ja.",
            "Tvoja práca je hotová.",
            "Klikanie preberám ja.",
            "Čakanie? To zvládnem.",
            "Woca nechaj na mňa.",
            "Ty oddychuj. Ja pracujem.",
            "Automatika preberá kontrolu.",
            "Všetko pripravené.",
            "Som pripravený. Ty môžeš byť tiež.",
            "Nechaj ma pracovať.",
        ]

        welcome = QLabel(
            random.choice(messages)
        )

        welcome.setObjectName(
            "welcome"
        )

        welcome.setAlignment(
            Qt.AlignCenter
        )

        main_layout.addWidget(
            welcome
        )

        # ====================================================
        # STAV ÚČTU A BODY
        # ====================================================

        info_row = QHBoxLayout()

        info_row.setSpacing(
            14
        )

        account_card = QFrame()

        account_card.setObjectName(
            "infoCard"
        )

        account_layout = QVBoxLayout(
            account_card
        )

        account_layout.setContentsMargins(
            18,
            12,
            18,
            12
        )

        account_layout.setSpacing(
            2
        )

        account_title = QLabel(
            "Účet"
        )

        account_title.setObjectName(
            "infoTitle"
        )

        self.account_label = QLabel(
            "●  Nepripojený"
        )

        self.account_label.setObjectName(
            "infoValue"
        )

        account_layout.addWidget(
            account_title
        )

        account_layout.addWidget(
            self.account_label
        )

        points_card = QFrame()

        points_card.setObjectName(
            "infoCard"
        )

        points_layout = QVBoxLayout(
            points_card
        )

        points_layout.setContentsMargins(
            18,
            12,
            18,
            12
        )

        points_layout.setSpacing(
            2
        )

        points_title = QLabel(
            "Body"
        )

        points_title.setObjectName(
            "infoTitle"
        )

        self.points_label = QLabel(
            "—"
        )

        self.points_label.setObjectName(
            "pointsValue"
        )

        points_layout.addWidget(
            points_title
        )

        points_layout.addWidget(
            self.points_label
        )

        info_row.addWidget(
            account_card,
            1
        )

        info_row.addWidget(
            points_card,
            1
        )

        main_layout.addLayout(
            info_row
        )

        start_button = QPushButton(
            "▶   SPUSTIŤ"
        )

        start_button.setObjectName(
            "startButton"
        )

        start_button.setFixedSize(
            280,
            70
        )

        start_container = QHBoxLayout()

        start_container.addStretch()

        start_container.addWidget(
            start_button
        )

        start_container.addStretch()

        main_layout.addLayout(
            start_container
        )

        self.start_button = start_button

        self.start_button.clicked.connect(
            self.toggle_management
        )

        self.status_label = QLabel(
            "●  Pripravené"
        )

        self.status_label.setObjectName(
            "status"
        )

        self.status_label.setAlignment(
            Qt.AlignCenter
        )

        main_layout.addWidget(
            self.status_label
        )

        main_layout.addStretch()

        copyright = QLabel(
            "© 2026 Alex Polák. Všetky práva vyhradené."
        )

        copyright.setObjectName(
            "copyright"
        )

        copyright.setAlignment(
            Qt.AlignRight
            | Qt.AlignBottom
        )

        main_layout.addWidget(
            copyright
        )

        self.flyout = QFrame(self)

        self.flyout.setObjectName(
            "flyout"
        )

        self.flyout.setFixedWidth(
            240
        )

        self.flyout.setGeometry(
            -250,
            0,
            240,
            self.height()
        )

        self.flyout.show()

        self.flyout.raise_()

        flyout_layout = QVBoxLayout(
            self.flyout
        )

        flyout_layout.setContentsMargins(
            10,
            28,
            18,
            20
        )

        flyout_layout.setSpacing(
            8
        )

        close_layout = QHBoxLayout()

        close_layout.setContentsMargins(
            22,
            0,
            0,
            0
        )

        close_layout.setSpacing(
            12
        )

        self.close_button = QPushButton(
            "✕"
        )

        self.close_button.setObjectName(
            "closeButton"
        )

        self.close_button.setFixedSize(
            48,
            48
        )

        self.close_button.clicked.connect(
            self.toggle_menu
        )

        close_layout.addWidget(
            self.close_button
        )

        flyout_title = QLabel(
            "Menu"
        )

        flyout_title.setObjectName(
            "flyoutTitle"
        )

        flyout_title.setAlignment(
            Qt.AlignLeft
            | Qt.AlignVCenter
        )

        close_layout.addWidget(
            flyout_title
        )

        close_layout.addStretch()

        flyout_layout.addLayout(
            close_layout
        )

        menu_items = [
            "📦   Balíčky",
            "⚙️   Nastavenia",
            "📋   Udalosti",
            "ℹ️   O aplikácii",
        ]

        flyout_layout.addSpacing(
            96
        )

        for text in menu_items:

            emoji, label = text.split(
                "   ",
                1
            )

            button = QPushButton()

            button.setObjectName(
                "flyoutButton"
            )

            button.setFixedHeight(
                48
            )

            if label == "O aplikácii":

                button.clicked.connect(
                    self.show_about
                )

            if label == "Nastavenia":

                button.clicked.connect(
                    self.show_settings
                )

            if label == "Udalosti":

                button.clicked.connect(
                    self.show_events
                )

            button_layout = QHBoxLayout(
                button
            )

            button_layout.setContentsMargins(
                0,
                0,
                0,
                0
            )

            button_layout.setSpacing(
                6
            )

            button_layout.setAlignment(
                Qt.AlignCenter
            )

            emoji_label = QLabel(
                emoji
            )

            emoji_label.setFixedWidth(
                28
            )

            emoji_label.setAlignment(
                Qt.AlignCenter
            )

            emoji_label.setAttribute(
                Qt.WA_TransparentForMouseEvents
            )

            text_label = QLabel(
                label
            )

            text_label.setObjectName(
                "flyoutItemText"
            )

            text_label.setAlignment(
                Qt.AlignLeft
                | Qt.AlignVCenter
            )

            text_label.setAttribute(
                Qt.WA_TransparentForMouseEvents
            )

            button_layout.addWidget(
                emoji_label
            )

            button_layout.addWidget(
                text_label
            )

            flyout_layout.addWidget(
                button
            )

        flyout_layout.addStretch()

        self.load_account_preview()

        self.apply_styles()

    # ========================================================
    # ÚČET + POSLEDNÉ ZAPAMÄTANÉ BODY
    # ========================================================

    def load_account_preview(self):

        try:

            config_path = self.get_config_path()

            if not config_path.exists():

                self.account_name = "—"

                self.account_label.setText(
                    "●  Nepripojený"
                )

                self.points_value = None

                self.points_label.setText(
                    "—"
                )

                return

            config = toml.load(
                config_path
            )

            username = str(
                config.get(
                    "username",
                    ""
                )
            ).strip()

            if username:

                self.account_name = username

                self.account_label.setText(
                    f"●  {username} · Pripojený"
                )

            else:

                self.account_name = "—"

                self.account_label.setText(
                    "●  Nepripojený"
                )

            last_points = config.get(
                "last_points",
                None
            )

            try:

                if last_points is not None:

                    self.points_value = int(
                        last_points
                    )

                    self.points_label.setText(
                        f"{self.points_value:,}".replace(
                            ",",
                            " "
                        )
                    )

                else:

                    self.points_value = None

                    self.points_label.setText(
                        "—"
                    )

            except (
                ValueError,
                TypeError
            ):

                self.points_value = None

                self.points_label.setText(
                    "—"
                )

        except Exception:

            self.account_name = "—"

            self.account_label.setText(
                "●  Nepripojený"
            )

            self.points_value = None

            self.points_label.setText(
                "—"
            )

    # ========================================================
    # ULOŽENIE POSLEDNÝCH BODOV
    # ========================================================

    def save_last_points(self, points):

        try:

            config_path = self.get_config_path()

            if not config_path.exists():

                return

            lines = config_path.read_text(
                encoding="utf-8"
            ).splitlines()

            updated = False

            for index, line in enumerate(lines):

                stripped = line.strip()

                if (
                    stripped.startswith("last_points")
                    and "=" in stripped
                    and not stripped.startswith("#")
                ):

                    prefix = line.split(
                        "=",
                        1
                    )[0]

                    lines[index] = (
                        prefix
                        + " = "
                        + str(points)
                    )

                    updated = True

                    break

            if not updated:

                if lines and lines[-1].strip():

                    lines.append("")

                lines.append(
                    f"last_points = {points}"
                )

            config_path.write_text(
                "\n".join(lines)
                + "\n",
                encoding="utf-8"
            )

        except Exception as error:

            self.add_event(
                f"CHYBA: Nepodarilo sa uložiť last_points: {error}"
            )

    # ========================================================
    # ZÁZNAM UDALOSTÍ
    # ========================================================

    def get_events_path(self):

        return (
            self.get_base_path()
            / "events.log"
        )

    def add_event(self, message):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        event = (
            f"[ {timestamp} ]  {message}"
        )

        self.event_log.append(
            event
        )

        if len(self.event_log) > 200:

            self.event_log = self.event_log[-200:]

        try:

            with self.get_events_path().open(
                "a",
                encoding="utf-8"
            ) as file:

                file.write(
                    event + "\n"
                )

        except Exception:

            pass

        self.refresh_events_view()

    def refresh_events_view(self):

        if self.events_text is None:

            return

        if self.event_log:

            events_content = "\n".join(
                reversed(
                    self.event_log
                )
            )

        else:

            events_content = (
                "Zatiaľ neboli zaznamenané žiadne udalosti."
            )

        self.events_text.setPlainText(
            events_content
        )

    def clear_events_view(self, *_):

        self.events_dialog = None

        self.events_text = None

    # ========================================================
    # SPUSTIŤ / ZASTAVIŤ
    # ========================================================

    def toggle_management(self):

        if (
            self.management_process is not None
            and self.management_process.state()
            != QProcess.NotRunning
        ):

            self.stop_management()

        else:

            self.start_management()

    # ========================================================
    # SPUSTENIE MANAGEMENTU
    # ========================================================

    def start_management(self):

        if (
            self.management_process is not None
            and self.management_process.state()
            != QProcess.NotRunning
        ):

            return

        base_path = self.get_base_path()

        management_path = (
            base_path
            / "management.py"
        )

        if not management_path.exists():

            self.status_label.setText(
                "●  Chýba management.py"
            )

            self.add_event(
                "CHYBA: management.py sa nenašiel."
            )

            QMessageBox.critical(
                self,
                "WocaFuckOff",
                "Súbor management.py sa nenašiel.\n\n"
                "Skontroluj, či je v priečinku aplikácie."
            )

            return

        self.management_stopping = False

        self.management_output_buffer = ""

        self.start_button.setEnabled(
            True
        )

        self.start_button.setText(
            "■   ZASTAVIŤ"
        )

        self.status_label.setText(
            "●  Spúšťam management..."
        )

        self.add_event(
            "Spúšťam management.py"
        )

        self.management_process = QProcess(
            self
        )

        self.management_process.setWorkingDirectory(
            str(base_path)
        )

        environment = (
            self.management_process
            .processEnvironment()
        )

        environment.insert(
            "PYTHONUNBUFFERED",
            "1"
        )

        self.management_process.setProcessEnvironment(
            environment
        )

        self.management_process.readyReadStandardOutput.connect(
            self.management_stdout
        )

        self.management_process.readyReadStandardError.connect(
            self.management_stderr
        )

        self.management_process.finished.connect(
            self.management_finished
        )

        self.management_process.errorOccurred.connect(
            self.management_error
        )

        self.management_process.start(
            sys.executable,
            [
                str(management_path)
            ]
        )

    # ========================================================
    # STOP - ULOŽIŤ A UKONČIŤ
    # ========================================================

    def stop_management(self):

        if (
            self.management_process is None
            or self.management_process.state()
            == QProcess.NotRunning
        ):

            return

        self.management_stopping = True

        self.add_event(
            "Požiadavka: Uložiť a ukončiť."
        )

        self.status_label.setText(
            "●  Ukladám a ukončujem..."
        )

        self.start_button.setEnabled(
            False
        )

        self.start_button.setText(
            "■   UKONČUJEM..."
        )

        base_path = self.get_base_path()

        management_path = (
            base_path
            / "management.py"
        )

        self.stop_output_buffer = ""

        self.stop_process = QProcess(
            self
        )

        self.stop_process.setWorkingDirectory(
            str(base_path)
        )

        environment = (
            self.stop_process
            .processEnvironment()
        )

        environment.insert(
            "PYTHONUNBUFFERED",
            "1"
        )

        self.stop_process.setProcessEnvironment(
            environment
        )

        self.stop_process.readyReadStandardOutput.connect(
            self.stop_stdout
        )

        self.stop_process.readyReadStandardError.connect(
            self.stop_stderr
        )

        self.stop_process.finished.connect(
            self.stop_finished
        )

        self.stop_process.start(
            sys.executable,
            [
                str(management_path),
                "--stop"
            ]
        )

    # ========================================================
    # STOP STDOUT
    # ========================================================

    def stop_stdout(self):

        if self.stop_process is None:

            return

        raw_data = (
            self.stop_process
            .readAllStandardOutput()
            .data()
        )

        if not raw_data:

            return

        try:

            data = raw_data.decode(
                "utf-8"
            )

        except UnicodeDecodeError:

            data = raw_data.decode(
                "cp1250",
                errors="replace"
            )

        for line in data.splitlines():

            line = line.strip()

            if not line:

                continue

            self.add_event(
                line
            )

            self.update_account_and_points(
                line
            )

    # ========================================================
    # STOP STDERR
    # ========================================================

    def stop_stderr(self):

        if self.stop_process is None:

            return

        raw_data = (
            self.stop_process
            .readAllStandardError()
            .data()
        )

        if not raw_data:

            return

        try:

            data = raw_data.decode(
                "utf-8"
            )

        except UnicodeDecodeError:

            data = raw_data.decode(
                "cp1250",
                errors="replace"
            )

        for line in data.splitlines():

            line = line.strip()

            if not line:

                continue

            self.add_event(
                f"CHYBA STOP: {line}"
            )

    # ========================================================
    # STOP FINISH
    # ========================================================

    def stop_finished(
        self,
        exit_code,
        exit_status
    ):

        self.add_event(
            f"Stop proces skončil | Exit code: {exit_code}"
        )

        self.stop_process = None

        if exit_code == 0:

            self.status_label.setText(
                "●  Uložené a ukončené"
            )

            self.start_button.setText(
                "▶   SPUSTIŤ"
            )

        else:

            self.status_label.setText(
                "●  Nepodarilo sa uložiť a ukončiť"
            )

            self.start_button.setText(
                "▶   SPUSTIŤ ZNOVA"
            )

        self.start_button.setEnabled(
            True
        )

        self.management_stopping = False

        self.load_account_preview()

    # ========================================================
    # VÝSTUP MANAGEMENTU
    # ========================================================

    def management_stdout(self):

        if self.management_process is None:

            return

        raw_data = (
            self.management_process
            .readAllStandardOutput()
            .data()
        )

        if not raw_data:

            return

        try:

            data = raw_data.decode(
                "utf-8"
            )

        except UnicodeDecodeError:

            data = raw_data.decode(
                "cp1250",
                errors="replace"
            )

        self.management_output_buffer += data

        lines = (
            self.management_output_buffer
            .split("\n")
        )

        self.management_output_buffer = (
            lines.pop()
        )

        for line in lines:

            line = line.strip()

            if not line:

                continue

            self.add_event(
                line
            )

            self.update_account_and_points(
                line
            )

            self.update_management_status(
                line
            )

    # ========================================================
    # CHYBOVÝ VÝSTUP
    # ========================================================

    def management_stderr(self):

        if self.management_process is None:

            return

        raw_data = (
            self.management_process
            .readAllStandardError()
            .data()
        )

        if not raw_data:

            return

        try:

            data = raw_data.decode(
                "utf-8"
            )

        except UnicodeDecodeError:

            data = raw_data.decode(
                "cp1250",
                errors="replace"
            )

        for line in data.splitlines():

            line = line.strip()

            if not line:

                continue

            self.add_event(
                f"CHYBA: {line}"
            )

            self.status_label.setText(
                "●  Chyba"
            )

    # ========================================================
    # AKTUALIZÁCIA STAVU
    # ========================================================

    def update_management_status(
        self,
        line
    ):

        text = line.lower()

        if (
            "attached to tab" in text
            or "opened new browser" in text
        ):

            self.status_label.setText(
                "●  Prehliadač pripojený"
            )

        elif "clicking class" in text:

            self.status_label.setText(
                "●  Vyberám triedu..."
            )

        elif "clicking package" in text:

            self.status_label.setText(
                "●  Vyberám balíček..."
            )

        elif (
            "double points enabled" in text
            or "double points already enabled" in text
        ):

            self.status_label.setText(
                "●  Double points pripravené"
            )

        elif (
            "solver spustený" in text
            or "solver exited" in text
            or "answered:" in text
            or "question:" in text
            or "auto-learned:" in text
        ):

            self.status_label.setText(
                "●  Solver pracuje..."
            )

        elif (
            "bot has stopped" in text
            or "bot finished" in text
        ):

            self.status_label.setText(
                "●  Dokončené"
            )

    # ========================================================
    # AKTUALIZÁCIA ÚČTU A BODOV
    # ========================================================

    def update_account_and_points(
        self,
        line
    ):

        point_match = re.search(
            r"(?:POINTS|WOCAPOINTS|WOCAPOINT|BODY|BODOV)\s*[:=]\s*([0-9][0-9\s.,]*)",
            line,
            re.IGNORECASE
        )

        if not point_match:

            point_match = re.search(
                r"([0-9][0-9\s.,]*)\s*(?:points|wocapoints|bodov)\b",
                line,
                re.IGNORECASE
            )

        if point_match:

            raw_points = point_match.group(1)

            raw_points = re.sub(
                r"[^0-9]",
                "",
                raw_points
            )

            if not raw_points:

                return

            try:

                points = int(
                    raw_points
                )

            except (
                ValueError,
                TypeError
            ):

                return

            self.points_value = points

            self.points_label.setText(
                f"{points:,}".replace(
                    ",",
                    " "
                )
            )

            self.save_last_points(
                points
            )

    # ========================================================
    # DOKONČENIE MANAGEMENTU
    # ========================================================

    def management_finished(self, exit_code, exit_status):

        if self.management_stopping:
            self.status_label.setText(
                "●  Zastavené"
            )

            self.start_button.setText(
                "▶   SPUSTIŤ"
            )

        elif exit_code == 0:
            self.status_label.setText(
                "●  Dokončené"
            )

            self.start_button.setText(
                "▶   SPUSTIŤ ZNOVA"
            )

        else:
            self.status_label.setText(
                "●  Skončilo s chybou"
            )

            self.start_button.setText(
                "▶   SPUSTIŤ ZNOVA"
            )

        self.start_button.setEnabled(True)

        self.management_process = None

        self.management_stopping = False

    # ========================================================
    # CHYBA PROCESU
    # ========================================================

    def management_error(
        self,
        error
    ):

        if self.management_stopping:

            return

        self.add_event(
            f"QProcess chyba: {error}"
        )

        self.status_label.setText(
            "●  Nepodarilo sa spustiť"
        )

        self.start_button.setText(
            "▶   SPUSTIŤ"
        )

        self.start_button.setEnabled(
            True
        )

        self.management_process = None

    # ========================================================
    # O APLIKÁCII
    # ========================================================

    def show_about(self):

        dialog = QDialog(self)

        dialog.setWindowTitle(
            "O aplikácii"
        )

        dialog.setFixedSize(
            420,
            380
        )

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        layout.setSpacing(
            10
        )

        title = QLabel(
            "O aplikácii"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet("""
            color: #ffffff;
            font-size: 28px;
            font-weight: 700;
        """)

        subtitle = QLabel(
            "Informácie o aplikácii"
        )

        subtitle.setAlignment(
            Qt.AlignCenter
        )

        subtitle.setStyleSheet("""
            color: #888888;
            font-size: 13px;
        """)

        separator1 = QFrame()

        separator1.setFrameShape(
            QFrame.HLine
        )

        separator1.setStyleSheet("""
            color: #303030;
        """)

        app_name = QLabel(
            "WocaFuckOff"
        )

        app_name.setAlignment(
            Qt.AlignCenter
        )

        app_name.setStyleSheet("""
            color: #ffffff;
            font-size: 19px;
            font-weight: 600;
        """)

        version = QLabel(
            "Verzia 1.0"
        )

        version.setAlignment(
            Qt.AlignCenter
        )

        version.setStyleSheet("""
            color: #888888;
            font-size: 12px;
        """)

        description = QLabel(
            "Automatizácia pre Wocabee."
        )

        description.setAlignment(
            Qt.AlignCenter
        )

        description.setWordWrap(
            True
        )

        description.setStyleSheet("""
            color: #cccccc;
            font-size: 13px;
        """)

        copyright_label = QLabel(
            "© 2026 Alex Polák. Všetky práva vyhradené."
        )

        copyright_label.setAlignment(
            Qt.AlignCenter
        )

        copyright_label.setStyleSheet("""
            color: #666666;
            font-size: 10px;
        """)

        separator2 = QFrame()

        separator2.setFrameShape(
            QFrame.HLine
        )

        separator2.setStyleSheet("""
            color: #303030;
        """)

        close_button = QPushButton(
            "Zavrieť"
        )

        close_button.setFixedHeight(
            42
        )

        close_button.clicked.connect(
            dialog.accept
        )

        layout.addStretch()

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            separator1
        )

        layout.addSpacing(
            18
        )

        layout.addWidget(
            app_name
        )

        layout.addWidget(
            version
        )

        layout.addSpacing(
            12
        )

        layout.addWidget(
            description
        )

        layout.addSpacing(
            20
        )

        layout.addWidget(
            copyright_label
        )

        layout.addSpacing(
            12
        )

        layout.addWidget(
            separator2
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            close_button
        )

        layout.addStretch()

        dialog.setStyleSheet("""
            QDialog {
                background: #181818;
            }

            QPushButton {
                background: #ffffff;
                color: #111111;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #dddddd;
            }

            QPushButton:pressed {
                background: #bbbbbb;
            }
        """)

        dialog.exec()

    # ========================================================
    # NASTAVENIA
    # ========================================================

    def show_settings(self):

        config_path = self.get_config_path()

        if not config_path.exists():

            QMessageBox.critical(
                self,
                "Nastavenia",
                "Konfiguračný súbor config.toml sa nenašiel.\n\n"
                "Umiestnite ho do priečinka aplikácie."
            )

            return

        try:

            config = toml.load(
                config_path
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Nastavenia",
                "config.toml sa nepodarilo načítať.\n\n"
                f"{error}"
            )

            return

        dialog = QDialog(self)

        dialog.setWindowTitle(
            "Nastavenia"
        )

        dialog.setFixedSize(
            700,
            620
        )

        root = QVBoxLayout(
            dialog
        )

        root.setContentsMargins(
            28,
            24,
            28,
            24
        )

        root.setSpacing(
            14
        )

        # ====================================================
        # HLAVIČKA
        # ====================================================

        title = QLabel(
            "Nastavenia"
        )

        title.setObjectName(
            "settingsTitle"
        )

        subtitle = QLabel(
            "Konfigurácia WocaFuckOff"
        )

        subtitle.setObjectName(
            "settingsSubtitle"
        )

        root.addWidget(
            title
        )

        root.addWidget(
            subtitle
        )

        separator = QFrame()

        separator.setFrameShape(
            QFrame.HLine
        )

        separator.setObjectName(
            "settingsSeparator"
        )

        root.addWidget(
            separator
        )

        # ====================================================
        # SCROLL
        # ====================================================

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        content = QWidget()

        content.setObjectName(
            "settingsContent"
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            2,
            2,
            8,
            2
        )

        content_layout.setSpacing(
            10
        )

        # ====================================================
        # POMOCNÉ FUNKCIE
        # ====================================================

        def make_card(
            title_text,
            description_text=""
        ):

            card = QFrame()

            card.setObjectName(
                "settingsCard"
            )

            layout = QVBoxLayout(
                card
            )

            layout.setContentsMargins(
                16,
                14,
                16,
                16
            )

            layout.setSpacing(
                8
            )

            heading = QLabel(
                title_text
            )

            heading.setObjectName(
                "settingsSectionTitle"
            )

            layout.addWidget(
                heading
            )

            if description_text:

                description = QLabel(
                    description_text
                )

                description.setObjectName(
                    "settingsSectionDescription"
                )

                description.setWordWrap(
                    True
                )

                layout.addWidget(
                    description
                )

            return card, layout

        def make_label(
            text,
            hint=None
        ):

            holder = QWidget()

            holder_layout = QVBoxLayout(
                holder
            )

            holder_layout.setContentsMargins(
                0,
                0,
                0,
                0
            )

            holder_layout.setSpacing(
                1
            )

            label = QLabel(
                text
            )

            label.setObjectName(
                "fieldLabel"
            )

            holder_layout.addWidget(
                label
            )

            if hint:

                small = QLabel(
                    hint
                )

                small.setObjectName(
                    "fieldHint"
                )

                small.setWordWrap(
                    True
                )

                holder_layout.addWidget(
                    small
                )

            return holder

        def make_line(
            value="",
            password=False,
            placeholder=""
        ):

            widget = QLineEdit()

            widget.setText(
                str(value)
            )

            widget.setMinimumHeight(
                34
            )

            if placeholder:

                widget.setPlaceholderText(
                    placeholder
                )

            if password:

                widget.setEchoMode(
                    QLineEdit.Password
                )

            return widget

        fields = {}

        # ====================================================
        # AUTOMATIZÁCIA
        # ====================================================

        card, card_layout = make_card(
            "Automatizácia",
            "Základné nastavenia spustenia."
        )

        fields["headless"] = QCheckBox(
            "Spustiť bez zobrazenia prehliadača"
        )

        fields["headless"].setChecked(
            bool(
                config.get(
                    "headless",
                    False
                )
            )
        )

        fields["double_points"] = QCheckBox(
            "Používať double points"
        )

        fields["double_points"].setChecked(
            bool(
                config.get(
                    "double_points",
                    False
                )
            )
        )

        card_layout.addWidget(
            fields["headless"]
        )

        card_layout.addWidget(
            fields["double_points"]
        )

        content_layout.addWidget(
            card
        )

        # ====================================================
        # PRIHLÁSENIE
        # ====================================================

        card, card_layout = make_card(
            "Prihlásenie",
            "Prihlasovacie údaje pre automatické prihlásenie."
        )

        form = QFormLayout()

        form.setLabelAlignment(
            Qt.AlignLeft
            | Qt.AlignVCenter
        )

        form.setHorizontalSpacing(
            14
        )

        form.setVerticalSpacing(
            10
        )

        fields["username"] = make_line(
            config.get(
                "username",
                ""
            ),
            placeholder="username"
        )

        fields["password"] = make_line(
            config.get(
                "password",
                ""
            ),
            password=True,
            placeholder="••••••••"
        )

        form.addRow(
            make_label(
                "Username"
            ),
            fields["username"]
        )

        form.addRow(
            make_label(
                "Password"
            ),
            fields["password"]
        )

        card_layout.addLayout(
            form
        )

        content_layout.addWidget(
            card
        )

        # ====================================================
        # POKROČILÉ NASTAVENIA
        # ====================================================

        advanced_button = QPushButton(
            "▶   Pokročilé nastavenia"
        )

        advanced_button.setObjectName(
            "advancedButton"
        )

        advanced_button.setCheckable(
            True
        )

        advanced_button.setChecked(
            False
        )

        content_layout.addWidget(
            advanced_button
        )

        advanced_content = QWidget()

        advanced_content.setObjectName(
            "advancedContent"
        )

        advanced_layout = QVBoxLayout(
            advanced_content
        )

        advanced_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        advanced_layout.setSpacing(
            10
        )

        advanced_content.setVisible(
            False
        )

        # ====================================================
        # POKROČILÉ - WOCABEE
        # ====================================================

        card, card_layout = make_card(
            "Wocabee",
            "Technické nastavenia pripojenia."
        )

        form = QFormLayout()

        form.setLabelAlignment(
            Qt.AlignLeft
            | Qt.AlignVCenter
        )

        form.setHorizontalSpacing(
            14
        )

        form.setVerticalSpacing(
            10
        )

        fields["urlbase"] = make_line(
            config.get(
                "urlbase",
                ""
            ),
            placeholder="https://wocabee.app/app"
        )

        fields["debug_port"] = make_line(
            config.get(
                "debug_port",
                ""
            ),
            placeholder="http://localhost:9222"
        )

        form.addRow(
            make_label(
                "URL aplikácie",
                "Cieľová Wocabee adresa"
            ),
            fields["urlbase"]
        )

        form.addRow(
            make_label(
                "Debug CDP",
                "Chromium DevTools Protocol"
            ),
            fields["debug_port"]
        )

        card_layout.addLayout(
            form
        )

        advanced_layout.addWidget(
            card
        )

        # ====================================================
        # POKROČILÉ - SÚBORY
        # ====================================================

        card, card_layout = make_card(
            "Súbory",
            "Technické dátové súbory používané solverom."
        )

        form = QFormLayout()

        form.setLabelAlignment(
            Qt.AlignLeft
            | Qt.AlignVCenter
        )

        form.setHorizontalSpacing(
            14
        )

        form.setVerticalSpacing(
            10
        )

        fields["wordlist_file"] = make_line(
            config.get(
                "wordlist_file",
                "wordlist.json"
            ),
            placeholder="wordlist.json"
        )

        fields["picture_file"] = make_line(
            config.get(
                "picture_file",
                "picturelist.json"
            ),
            placeholder="picturelist.json"
        )

        form.addRow(
            make_label(
                "Wordlist",
                "JSON súbor so slovami"
            ),
            fields["wordlist_file"]
        )

        form.addRow(
            make_label(
                "Obrázky",
                "JSON súbor s mapovaním obrázkov"
            ),
            fields["picture_file"]
        )

        card_layout.addLayout(
            form
        )

        advanced_layout.addWidget(
            card
        )

        # ====================================================
        # POKROČILÉ - AUTOMATIZÁCIA
        # ====================================================

        card, card_layout = make_card(
            "Automatizácia",
            "Technické indexy a pomocné nastavenia."
        )

        form = QFormLayout()

        form.setLabelAlignment(
            Qt.AlignLeft
            | Qt.AlignVCenter
        )

        form.setHorizontalSpacing(
            14
        )

        form.setVerticalSpacing(
            10
        )

        placeholder_config = config.get(
            "placeholder_words",
            []
        )

        fields["placeholder_words"] = make_line(
            ", ".join(
                str(x)
                for x in placeholder_config
            )
            if isinstance(
                placeholder_config,
                list
            )
            else str(
                placeholder_config
            ),
            placeholder="translate, check"
        )

        fields["class_index"] = NoScrollSpinBox()

        fields["class_index"].setRange(
            0,
            999999
        )

        fields["class_index"].setValue(
            int(
                config.get(
                    "class_index",
                    0
                )
            )
        )

        fields["class_index"].setMinimumHeight(
            34
        )

        fields["package_index"] = NoScrollSpinBox()

        fields["package_index"].setRange(
            0,
            999999
        )

        fields["package_index"].setValue(
            int(
                config.get(
                    "package_index",
                    0
                )
            )
        )

        fields["package_index"].setMinimumHeight(
            34
        )

        form.addRow(
            make_label(
                "Ignorované slová",
                "Oddelené čiarkou"
            ),
            fields["placeholder_words"]
        )

        form.addRow(
            make_label(
                "Trieda",
                "Index triedy"
            ),
            fields["class_index"]
        )

        form.addRow(
            make_label(
                "Balík",
                "Index balíka"
            ),
            fields["package_index"]
        )

        card_layout.addLayout(
            form
        )

        advanced_layout.addWidget(
            card
        )

        # ====================================================
        # POKROČILÉ - NTFY
        # ====================================================

        card, card_layout = make_card(
            "NTFY",
            "Technická konfigurácia notifikácií."
        )

        form = QFormLayout()

        form.setLabelAlignment(
            Qt.AlignLeft
            | Qt.AlignVCenter
        )

        form.setHorizontalSpacing(
            14
        )

        form.setVerticalSpacing(
            10
        )

        fields["ntfy_server"] = make_line(
            config.get(
                "ntfy_server",
                ""
            ),
            placeholder="https://example.ntfy.server"
        )

        fields["ntfy_topic"] = make_line(
            config.get(
                "ntfy_topic",
                ""
            ),
            placeholder="wocabee-bot"
        )

        fields["ntfy_token"] = make_line(
            config.get(
                "ntfy_token",
                ""
            ),
            password=True,
            placeholder="secret token"
        )

        form.addRow(
            make_label(
                "Server"
            ),
            fields["ntfy_server"]
        )

        form.addRow(
            make_label(
                "Topic"
            ),
            fields["ntfy_topic"]
        )

        form.addRow(
            make_label(
                "Token"
            ),
            fields["ntfy_token"]
        )

        card_layout.addLayout(
            form
        )

        advanced_layout.addWidget(
            card
        )

        advanced_layout.addStretch()

        content_layout.addWidget(
            advanced_content
        )

        content_layout.addStretch()

        # ====================================================
        # ROZBALENIE POKROČILÝCH NASTAVENÍ
        # ====================================================

        def toggle_advanced():

            is_open = (
                advanced_button.isChecked()
            )

            advanced_content.setVisible(
                is_open
            )

            if is_open:

                advanced_button.setText(
                    "▼   Pokročilé nastavenia"
                )

            else:

                advanced_button.setText(
                    "▶   Pokročilé nastavenia"
                )

        advanced_button.toggled.connect(
            toggle_advanced
        )

        scroll.setWidget(
            content
        )

        root.addWidget(
            scroll,
            1
        )

        # ====================================================
        # TLAČIDLÁ
        # ====================================================

        buttons = QHBoxLayout()

        buttons.setSpacing(
            8
        )

        close_button = QPushButton(
            "Zavrieť"
        )

        close_button.setObjectName(
            "settingsSecondaryButton"
        )

        close_button.setMinimumHeight(
            40
        )

        close_button.clicked.connect(
            dialog.reject
        )

        save_button = QPushButton(
            "Uložiť"
        )

        save_button.setObjectName(
            "settingsPrimaryButton"
        )

        save_button.setMinimumHeight(
            40
        )

        buttons.addWidget(
            close_button
        )

        buttons.addWidget(
            save_button
        )

        root.addLayout(
            buttons
        )

        # ====================================================
        # TOML
        # ====================================================

        def toml_value(value):

            if isinstance(
                value,
                bool
            ):

                return (
                    "true"
                    if value
                    else "false"
                )

            if isinstance(
                value,
                int
            ):

                return str(
                    value
                )

            if isinstance(
                value,
                list
            ):

                return (
                    "["
                    + ", ".join(
                        toml_value(
                            item
                        )
                        for item in value
                    )
                    + "]"
                )

            return json.dumps(
                str(value),
                ensure_ascii=False
            )

        def save_value(
            path,
            values
        ):

            lines = path.read_text(
                encoding="utf-8"
            ).splitlines()

            found_keys = set()

            for index, line in enumerate(
                lines
            ):

                stripped = line.lstrip()

                if (
                    not stripped
                    or stripped.startswith("#")
                    or "=" not in line
                ):

                    continue

                key = line.split(
                    "=",
                    1
                )[0].strip()

                if (
                    key not in values
                    or key in found_keys
                ):

                    continue

                prefix = line.split(
                    "=",
                    1
                )[0]

                lines[index] = (
                    prefix
                    + " = "
                    + toml_value(
                        values[key]
                    )
                )

                found_keys.add(
                    key
                )

            for key, value in values.items():

                if key not in found_keys:

                    lines.append(
                        f"{key} = {toml_value(value)}"
                    )

            path.write_text(
                "\n".join(lines)
                + "\n",
                encoding="utf-8"
            )

        # ====================================================
        # ULOŽENIE
        # ====================================================

        def save_settings():

            placeholder_words = [
                word.strip()
                for word in fields[
                    "placeholder_words"
                ].text().split(",")
                if word.strip()
            ]

            values = {

                "urlbase":
                    fields[
                        "urlbase"
                    ].text().strip(),

                "debug_port":
                    fields[
                        "debug_port"
                    ].text().strip(),

                "wordlist_file":
                    fields[
                        "wordlist_file"
                    ].text().strip(),

                "picture_file":
                    fields[
                        "picture_file"
                    ].text().strip(),

                "placeholder_words":
                    placeholder_words,

                "class_index":
                    fields[
                        "class_index"
                    ].value(),

                "package_index":
                    fields[
                        "package_index"
                    ].value(),

                "headless":
                    fields[
                        "headless"
                    ].isChecked(),

                "double_points":
                    fields[
                        "double_points"
                    ].isChecked(),

                "username":
                    fields[
                        "username"
                    ].text(),

                "password":
                    fields[
                        "password"
                    ].text(),

                "ntfy_server":
                    fields[
                        "ntfy_server"
                    ].text().strip(),

                "ntfy_topic":
                    fields[
                        "ntfy_topic"
                    ].text().strip(),

                "ntfy_token":
                    fields[
                        "ntfy_token"
                    ].text(),
            }

            try:

                save_value(
                    config_path,
                    values
                )

            except Exception as error:

                QMessageBox.critical(
                    dialog,
                    "Nastavenia",
                    "Nastavenia sa nepodarilo uložiť.\n\n"
                    f"{error}"
                )

                return

            self.add_event(
                "Nastavenia uložené"
            )

            self.load_account_preview()

            save_button.setText(
                "✓   Uložené"
            )

            QTimer.singleShot(
                1200,
                lambda: save_button.setText(
                    "Uložiť"
                )
            )

        save_button.clicked.connect(
            save_settings
        )

        # ====================================================
        # VZHĽAD
        # ====================================================

        dialog.setStyleSheet("""
            QDialog {
                background: #101010;
            }

            QLabel#settingsTitle {
                color: #ffffff;
                font-size: 24px;
                font-weight: 700;
            }

            QLabel#settingsSubtitle {
                color: #777777;
                font-size: 13px;
            }

            QFrame#settingsSeparator,
            QFrame#cardSeparator {
                color: #292929;
                background: #292929;
                max-height: 1px;
            }

            QScrollArea,
            QWidget#settingsContent,
            QWidget#advancedContent {
                background: #101010;
                border: none;
            }

            QFrame#settingsCard {
                background: #171717;
                border: 1px solid #242424;
                border-radius: 12px;
            }

            QLabel#settingsSectionTitle {
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
            }

            QLabel#settingsSectionDescription {
                color: #777777;
                font-size: 11px;
            }

            QLabel#fieldLabel {
                color: #e8e8e8;
                font-size: 12px;
                font-weight: 600;
            }

            QLabel#fieldHint {
                color: #666666;
                font-size: 10px;
            }

            QLineEdit,
            QSpinBox {
                background: #101010;
                color: #ffffff;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
                padding: 5px 8px;
                min-height: 32px;
                selection-background-color: #454545;
                font-size: 11px;
            }

            QLineEdit:focus,
            QSpinBox:focus {
                border: 1px solid #666666;
            }

            QCheckBox {
                color: #dddddd;
                spacing: 7px;
                font-size: 12px;
                min-height: 32px;
            }

            QCheckBox::indicator {
                width: 17px;
                height: 17px;
                background: #101010;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }

            QCheckBox::indicator:checked {
                background: #ffffff;
                border: 1px solid #ffffff;
            }

            QPushButton {
                border-radius: 9px;
                font-size: 13px;
                font-weight: 700;
                min-height: 40px;
            }

            QPushButton#advancedButton {
                background: #171717;
                color: #dddddd;
                border: 1px solid #242424;
                border-radius: 12px;
                text-align: left;
                padding-left: 16px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton#advancedButton:hover {
                background: #202020;
                color: #ffffff;
                border: 1px solid #303030;
            }

            QPushButton#settingsSecondaryButton {
                background: #1b1b1b;
                color: #cccccc;
                border: 1px solid #2c2c2c;
            }

            QPushButton#settingsSecondaryButton:hover {
                background: #242424;
                color: #ffffff;
            }

            QPushButton#settingsPrimaryButton {
                background: #ffffff;
                color: #111111;
                border: none;
            }

            QPushButton#settingsPrimaryButton:hover {
                background: #dddddd;
            }

            QPushButton#settingsPrimaryButton:pressed {
                background: #bbbbbb;
            }
        """)

        dialog.exec()

    # ========================================================
    # UDALOSTI
    # ========================================================

    def show_events(self):

        dialog = QDialog(
            self
        )

        self.events_dialog = dialog

        dialog.setWindowTitle(
            "Udalosti"
        )

        dialog.setFixedSize(
            760,
            560
        )

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(
            10
        )

        title = QLabel(
            "Udalosti"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet("""
            color: #ffffff;
            font-size: 28px;
            font-weight: 700;
        """)

        subtitle = QLabel(
            "Záznam činnosti aplikácie"
        )

        subtitle.setAlignment(
            Qt.AlignCenter
        )

        subtitle.setStyleSheet("""
            color: #888888;
            font-size: 13px;
        """)

        separator1 = QFrame()

        separator1.setFrameShape(
            QFrame.HLine
        )

        separator1.setStyleSheet("""
            color: #303030;
        """)

        events_text = QPlainTextEdit()

        self.events_text = events_text

        events_text.setReadOnly(
            True
        )

        events_text.setTextInteractionFlags(
            Qt.TextSelectableByMouse
            | Qt.TextSelectableByKeyboard
        )

        events_text.setLineWrapMode(
            QPlainTextEdit.NoWrap
        )

        events_text.setStyleSheet("""
            QPlainTextEdit {
                color: #cccccc;
                background: #121212;
                border: 1px solid #292929;
                border-radius: 12px;
                padding: 12px;
                font-size: 12px;
                font-family: Consolas, "Courier New", monospace;
            }

            QScrollBar:vertical {
                background: #121212;
                width: 10px;
                margin: 4px;
            }

            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #555555;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar:horizontal {
                background: #121212;
                height: 10px;
                margin: 4px;
            }

            QScrollBar::handle:horizontal {
                background: #3a3a3a;
                border-radius: 5px;
                min-width: 30px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #555555;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        copy_hint = QLabel(
            "Text môžeš označiť a skopírovať pomocou Ctrl+C."
        )

        copy_hint.setAlignment(
            Qt.AlignLeft
        )

        copy_hint.setStyleSheet("""
            color: #666666;
            font-size: 10px;
        """)

        close_button = QPushButton(
            "Zavrieť"
        )

        close_button.setFixedHeight(
            42
        )

        close_button.clicked.connect(
            dialog.accept
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            8
        )

        layout.addWidget(
            separator1
        )

        layout.addSpacing(
            8
        )

        layout.addWidget(
            events_text,
            1
        )

        layout.addWidget(
            copy_hint
        )

        layout.addSpacing(
            4
        )

        layout.addWidget(
            close_button
        )

        dialog.setStyleSheet("""
            QDialog {
                background: #181818;
            }

            QPushButton {
                background: #ffffff;
                color: #111111;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #dddddd;
            }

            QPushButton:pressed {
                background: #bbbbbb;
            }
        """)

        self.refresh_events_view()

        dialog.finished.connect(
            self.clear_events_view
        )

        dialog.exec()

    # ========================================================
    # OVLÁDANIE BOČNÉHO MENU
    # ========================================================

    def toggle_menu(self):

        self.flyout.show()

        self.flyout.raise_()

        self.menu_open = not self.menu_open

        if self.menu_open:

            self.menu_button.set_open(
                True
            )

            start_x = -250
            end_x = 0

        else:

            self.menu_button.set_open(
                False
            )

            start_x = 0
            end_x = -250

        animation = QPropertyAnimation(
            self.flyout,
            b"geometry"
        )

        animation.setDuration(
            220
        )

        animation.setStartValue(
            self.flyout.geometry()
        )

        animation.setEndValue(
            self.flyout.geometry().translated(
                end_x - start_x,
                0
            )
        )

        animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        animation.start()

        self.animation = animation

    # ========================================================
    # ZATVORENIE APLIKÁCIE
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        if (
            self.stop_process is not None
            and self.stop_process.state()
            != QProcess.NotRunning
        ):

            try:

                self.stop_process.kill()

            except Exception:

                pass

        if (
            self.management_process is not None
            and self.management_process.state()
            != QProcess.NotRunning
        ):

            self.management_stopping = True

            base_path = self.get_base_path()

            management_path = (
                base_path
                / "management.py"
            )

            try:

                subprocess.Popen(
                    [
                        sys.executable,
                        str(management_path),
                        "--stop"
                    ],
                    cwd=str(
                        base_path
                    ),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(
                        subprocess,
                        "CREATE_NO_WINDOW",
                        0
                    )
                )

            except Exception:

                pass

        event.accept()

    # ========================================================
    # ZMENA VEĽKOSTI OKNA
    # ========================================================

    def resizeEvent(
        self,
        event
    ):

        super().resizeEvent(
            event
        )

        if hasattr(
            self,
            "flyout"
        ):

            x = (
                0
                if self.menu_open
                else -250
            )

            self.flyout.setGeometry(
                x,
                0,
                240,
                self.height()
            )

    # ========================================================
    # VZHĽAD BOOTOVACEJ OBRAZOVKY
    # ========================================================

    def apply_boot_styles(self):

        self.setStyleSheet("""
            QMainWindow {
                background: #101010;
            }

            QWidget#bootWidget {
                background: #101010;
            }

            QLabel#bootTitle {
                color: #ffffff;
                font-size: 42px;
                font-weight: 700;
            }

            QLabel#bootSubtitle {
                color: #777777;
                font-size: 13px;
            }

            QLabel#bootStatus {
                color: #aaaaaa;
                font-size: 12px;
            }

            QProgressBar#bootProgress {
                background: #1c1c1c;
                border: none;
                border-radius: 3px;
            }

            QProgressBar#bootProgress::chunk {
                background: #ffffff;
                border-radius: 3px;
            }
        """)

    # ========================================================
    # VZHĽAD HLAVNÉHO ROZHRANIA
    # ========================================================

    def apply_styles(self):

        self.setStyleSheet("""
            QMainWindow {
                background: #101010;
            }

            QWidget#central {
                background: #101010;
            }

            QLabel#title {
                color: #ffffff;
                font-size: 21px;
                font-weight: 600;
            }

            QLabel#subtitle {
                color: #888888;
                font-size: 12px;
            }

            QLabel#welcome {
                color: #ffffff;
                font-size: 34px;
                font-weight: 600;
            }

            QLabel#status {
                color: #7ee787;
                font-size: 13px;
            }

            QLabel#copyright {
                color: #666666;
                font-size: 10px;
            }

            QPushButton#menuButton {
                background: #1b1b1b;
                color: #ffffff;
                border: 1px solid #292929;
                border-radius: 14px;
                font-size: 21px;
            }

            QPushButton#menuButton:hover {
                background: #292929;
            }

            QFrame#infoCard {
                background: #171717;
                border: 1px solid #242424;
                border-radius: 14px;
            }

            QLabel#infoTitle {
                color: #777777;
                font-size: 11px;
                font-weight: 600;
            }

            QLabel#infoValue {
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
            }

            QLabel#pointsValue {
                color: #ffffff;
                font-size: 22px;
                font-weight: 700;
            }

            QPushButton#startButton {
                background: #ffffff;
                color: #111111;
                border: none;
                border-radius: 20px;
                font-size: 17px;
                font-weight: 700;
            }

            QPushButton#startButton:hover {
                background: #dddddd;
            }

            QPushButton#startButton:pressed {
                background: #bbbbbb;
            }

            QFrame#flyout {
                background: #181818;
                border-right: 1px solid #303030;
            }

            QLabel#flyoutTitle {
                color: #ffffff;
                font-size: 20px;
                font-weight: 600;
            }

            QPushButton#closeButton {
                background: #1b1b1b;
                color: #ffffff;
                border: 1px solid #292929;
                border-radius: 14px;
                font-size: 21px;
            }

            QPushButton#closeButton:hover {
                background: #292929;
            }

            QPushButton#flyoutButton {
                background: transparent;
                color: #d0d0d0;
                border: none;
                border-radius: 10px;
                font-size: 14px;
            }

            QPushButton#flyoutButton:hover {
                background: #292929;
                color: #ffffff;
            }

            QLabel#flyoutItemText {
                color: #d0d0d0;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton#flyoutButton:hover QLabel#flyoutItemText {
                color: #ffffff;
            }
        """)


# ============================================================
# SPUSTENIE PROGRAMU
# ============================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    app.setStyle(
        "Fusion"
    )

    window = WocaFuckOff()

    window.show()

    sys.exit(
        app.exec()
    )
