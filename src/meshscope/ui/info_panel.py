"""Mesh Info Panel dock widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class CollapsibleSection(QWidget):
    """A section with a clickable header that toggles content visibility."""

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        *,
        expanded: bool = True,
    ) -> None:
        super().__init__(parent)
        self._expanded = expanded
        self._title = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self._header = QPushButton()
        self._header.setFlat(True)
        self._header.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self._header.clicked.connect(self.toggle)
        self._update_header_text()
        layout.addWidget(self._header)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        layout.addWidget(separator)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(10, 6, 10, 10)
        self._content.setVisible(self._expanded)
        layout.addWidget(self._content)

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    @property
    def header_button(self) -> QPushButton:
        return self._header

    @property
    def content_area(self) -> QWidget:
        return self._content

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._update_header_text()

    def _update_header_text(self) -> None:
        arrow = "\u25bc" if self._expanded else "\u25b6"
        self._header.setText(f"{arrow} {self._title.upper()}")
        state = "expanded" if self._expanded else "collapsed"
        self._header.setAccessibleName(f"{self._title} section, {state}")


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
