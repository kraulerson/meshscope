"""VTK viewport widget with empty and error state handling."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import vtkRenderer

from meshscope.vtk_adapter.scene_manager import SceneManager

logger = logging.getLogger("meshscope.ui.viewport_widget")


class ViewportWidget(QWidget):
    """Hosts the VTK render window with empty/error state overlays.

    Wraps QVTKRenderWindowInteractor and a SceneManager. Shows a text
    prompt when no mesh is loaded, and an error message if OpenGL fails.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = "empty"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # VTK interactor widget
        self._vtk_widget = QVTKRenderWindowInteractor(self)  # type: ignore[no-untyped-call]
        layout.addWidget(self._vtk_widget)

        # Renderer
        self._renderer = vtkRenderer()
        self._renderer.SetBackground(0.149, 0.149, 0.149)  # #262626
        self._vtk_widget.GetRenderWindow().AddRenderer(self._renderer)  # type: ignore[no-untyped-call]

        # Scene manager
        self._scene_manager = SceneManager(self._renderer)

        # Empty state overlay
        self._empty_label = QLabel(self)
        self._empty_label.setText(
            "Open a file or drag one here\n\nSupports STL, OBJ, 3MF, PLY"
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            "QLabel { color: #888; font-size: 16px; background: transparent; }"
        )
        self._empty_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._empty_label.setAccessibleName("Viewport empty state prompt")

        # Initialize interactor — must happen after renderer is added
        self._vtk_widget.GetRenderWindow().Render()  # type: ignore[no-untyped-call]
        self._vtk_widget.GetRenderWindow().GetInteractor().Initialize()  # type: ignore[no-untyped-call]

    @property
    def renderer(self) -> vtkRenderer:
        return self._renderer

    @property
    def scene_manager(self) -> SceneManager:
        return self._scene_manager

    @property
    def state(self) -> str:
        return self._state

    @property
    def empty_label(self) -> QLabel:
        return self._empty_label

    @property
    def vtk_interactor(self) -> QVTKRenderWindowInteractor:
        return self._vtk_widget

    def set_state(self, state: str) -> None:
        """Set the viewport state: 'empty', 'loading', 'success', 'error'."""
        self._state = state
        if state == "success":
            self._empty_label.hide()
        elif state == "empty":
            self._empty_label.setText(
                "Open a file or drag one here\n\nSupports STL, OBJ, 3MF, PLY"
            )
            self._empty_label.show()
        elif state == "loading":
            self._empty_label.hide()

    def show_error(self, message: str) -> None:
        """Show an error message in the viewport area."""
        self._state = "error"
        self._empty_label.setText(message)
        self._empty_label.show()
        logger.error("Viewport error: %s", message)

    def vtk_render(self) -> None:
        """Trigger a VTK render."""
        self._vtk_widget.GetRenderWindow().Render()  # type: ignore[no-untyped-call]

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Reposition the overlay label on resize."""
        super().resizeEvent(event)
        self._empty_label.setGeometry(self.rect())
