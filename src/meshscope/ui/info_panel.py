"""Mesh Info Panel dock widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class InfoPanel(QDockWidget):
    """Dock widget displaying mesh file info, geometry, dimensions, and status."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Info", parent)
        self.setAccessibleName("Mesh Info Panel")
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Scroll area for content
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setWidget(self._scroll)

        # Main content widget
        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Placeholder label for empty state
        self._placeholder = QLabel("No mesh loaded")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setAccessibleName("No mesh loaded")
        self._layout.addWidget(self._placeholder)

        self._layout.addStretch()
        self._scroll.setWidget(self._content)

        self._is_empty = True

    @property
    def is_empty(self) -> bool:
        return self._is_empty

    def clear(self) -> None:
        """Reset panel to empty state."""
        self._placeholder.setVisible(True)
        self._is_empty = True
