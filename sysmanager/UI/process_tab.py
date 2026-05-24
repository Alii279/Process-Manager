"""
ui/process_tab.py

The 'Processes' tab — lets the user kill named processes.
Phase 1 ships with a dedicated Discord button; the generic
kill-by-name flow will be added in a later session.

Squish note: every interactive widget gets a unique objectName
so Squish can locate it without coordinate-based hacks.
"""

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
)

from core.process_manager import ProcessManager, ProcessNotFoundError


# ---------------------------------------------------------------------------
# Background worker — keeps the UI responsive during process termination
# ---------------------------------------------------------------------------

class _KillWorker(QThread):
    """Runs process termination off the main thread."""

    finished = Signal(int)   # number of processes killed
    errored  = Signal(str)   # error message

    def __init__(self, manager: ProcessManager, process_name: str):
        super().__init__()
        self._manager = manager
        self._process_name = process_name

    def run(self):
        try:
            killed = self._manager.kill_by_name(self._process_name)
            self.finished.emit(killed)
        except ProcessNotFoundError as exc:
            self.errored.emit(str(exc))


# ---------------------------------------------------------------------------
# ProcessTab widget
# ---------------------------------------------------------------------------

class ProcessTab(QWidget):
    """
    UI tab for process management.

    Object names used by Squish:
        ProcessTab          — the tab widget itself
        killDiscordButton   — the main action button
        statusLabel         — result / status message
    """

    DISCORD_EXE = "Discord.exe"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProcessTab")

        self._manager = ProcessManager()
        self._worker: _KillWorker | None = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Section heading
        heading = QLabel("Process manager")
        heading.setObjectName("processHeading")
        heading.setStyleSheet("font-size: 18px; font-weight: 600;")
        root.addWidget(heading)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        root.addWidget(line)

        # Quick-action card
        card = QFrame()
        card.setObjectName("discordCard")
        card.setFrameShape(QFrame.StyledPanel)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        card_title = QLabel("Discord")
        card_title.setStyleSheet("font-size: 15px; font-weight: 500;")
        card_layout.addWidget(card_title)

        card_desc = QLabel(
            "Close all running Discord processes.\n"
            "Useful before updates or to free memory."
        )
        card_desc.setWordWrap(True)
        card_desc.setStyleSheet("color: gray;")
        card_layout.addWidget(card_desc)

        btn_row = QHBoxLayout()
        self.kill_btn = QPushButton("Close Discord")
        self.kill_btn.setObjectName("killDiscordButton")
        self.kill_btn.setFixedWidth(160)
        self.kill_btn.clicked.connect(self._on_kill_discord)
        btn_row.addWidget(self.kill_btn)
        btn_row.addStretch()
        card_layout.addLayout(btn_row)

        root.addWidget(card)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignLeft)
        root.addWidget(self.status_label)

        root.addStretch()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_kill_discord(self):
        """Triggered when the user clicks 'Close Discord'."""
        self.kill_btn.setEnabled(False)
        self.kill_btn.setText("Closing…")
        self._set_status("Working…", color="gray")

        self._worker = _KillWorker(self._manager, self.DISCORD_EXE)
        self._worker.finished.connect(self._on_kill_success)
        self._worker.errored.connect(self._on_kill_error)
        self._worker.finished.connect(self._reset_button)
        self._worker.errored.connect(self._reset_button)
        self._worker.start()

    def _on_kill_success(self, count: int):
        msg = (
            f"Done — closed {count} Discord process(es)."
            if count > 0
            else "Discord was not running."
        )
        self._set_status(msg, color="green")

    def _on_kill_error(self, message: str):
        self._set_status(f"Not found: {message}", color="orange")

    def _reset_button(self):
        self.kill_btn.setEnabled(True)
        self.kill_btn.setText("Close Discord")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, text: str, color: str = "black"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")
