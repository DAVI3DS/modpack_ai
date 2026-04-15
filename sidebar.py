from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QPushButton, QVBoxLayout


class Sidebar(QFrame):
    page_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(150)

        self._buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(12)

        items = [
            ("home", "Home"),
            ("custom_builder", "Custom Builder"),
            ("generate", "Generate"),
            ("export", "Export"),
            ("history", "History"),
            ("settings", "Settings"),
            ("about", "About"),
        ]

        for key, label in items:
            btn = QPushButton(label)
            btn.setObjectName("SidebarButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, page_key=key: self._on_click(page_key))
            layout.addWidget(btn)
            self._buttons[key] = btn

        layout.addStretch(1)
        self.set_active("home")

    def _on_click(self, key: str) -> None:
        self.set_active(key)
        self.page_selected.emit(key)

    def set_active(self, key: str) -> None:
        for k, btn in self._buttons.items():
            active = k == key
            btn.setChecked(active)
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

