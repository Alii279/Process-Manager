"""
ui/main_window.py

Application shell — a QTabWidget hosting each feature tab.
Tabs for Updates and Scheduler are stubbed; they will be
implemented in later sessions.
"""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QLabel
from PySide6.QtCore import QSize

from ui.process_tab import ProcessTab


class MainWindow(QMainWindow):
    """

    """

    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("SysManager")
        self.setMinimumSize(QSize(700, 450))

        tabs = QTabWidget()
        tabs.setObjectName("tabWidget")

        tabs.addTab(ProcessTab(), "Processes")
        tabs.addTab(QLabel("  Coming soon — Updates"), "Updates")
        tabs.addTab(QLabel("  Coming soon — Scheduler"), "Scheduler")

        self.setCentralWidget(tabs)