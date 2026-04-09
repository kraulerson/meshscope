"""Floating overlay widget for slice plane controls.

Provides X/Y/Z preset buttons and Reset, positioned over the 3D viewport.
Only visible while slice mode is active.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Stylesheet for the overlay panel
_OVERLAY_STYLE = """
SliceOverlayWidget {
    background-color: rgba(38, 38, 38, 238);
    border: 1px solid #444;
    border-radius: 6px;
}
QLabel#title {
    color: #ccc;
    font-size: 11px;
    font-weight: bold;
}
QPushButton.preset-btn {
    background-color: #333;
    color: #ccc;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: bold;
    min-width: 24px;
}
QPushButton.preset-btn:hover {
    background-color: #444;
    border-color: #89b4fa;
}
QPushButton.preset-btn[active="true"] {
    background-color: #89b4fa;
    color: #1a1a1a;
    border-color: #89b4fa;
}
QPushButton#btn_reset {
    background-color: #333;
    color: #ccc;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 11px;
}
QPushButton#btn_reset:hover {
    background-color: #444;
    border-color: #89b4fa;
}
"""


class SliceOverlayWidget(QWidget):
    """Floating overlay for slice plane controls. Parented to viewport widget.

    Signals:
        preset_clicked(str): Emitted when X, Y, or Z button is clicked.
            Payload is 'x', 'y', or 'z'.
        reset_clicked(): Emitted when Reset button is clicked.
    """

    preset_clicked = Signal(str)
    reset_clicked = Signal()

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)
        self.setObjectName("SliceOverlayWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(_OVERLAY_STYLE)
        self.setFixedWidth(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # Title
        title = QLabel("Slice Plane")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Preset buttons row
        row = QHBoxLayout()
        row.setSpacing(4)

        self._preset_buttons: dict[str, QPushButton] = {}
        for axis in ("x", "y", "z"):
            btn = QPushButton(axis.upper())
            btn.setObjectName(f"btn_{axis}")
            btn.setProperty("class", "preset-btn")
            btn.setAccessibleName(f"Slice preset {axis.upper()} axis")
            btn.clicked.connect(
                lambda checked=False, a=axis: self.preset_clicked.emit(a)
            )
            row.addWidget(btn)
            self._preset_buttons[axis] = btn

        layout.addLayout(row)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("btn_reset")
        reset_btn.setAccessibleName("Reset slice plane to model center")
        reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(reset_btn)

        # Start hidden
        self.hide()

    def set_active_preset(self, axis: str | None) -> None:
        """Highlight the active preset button, clearing others.

        Args:
            axis: 'x', 'y', 'z' to highlight, or None to clear all.
        """
        for key, btn in self._preset_buttons.items():
            is_active = axis is not None and key == axis.lower()
            btn.setProperty("active", is_active)
            # Force stylesheet recalculation
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def show_overlay(self) -> None:
        """Show the overlay panel."""
        self.show()
        self.raise_()

    def hide_overlay(self) -> None:
        """Hide the overlay panel."""
        self.hide()
