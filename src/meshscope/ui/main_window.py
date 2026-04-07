"""Main application window with toolbar, menus, status bar, and viewport."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QStatusBar,
    QToolBar,
)

from meshscope.core.exceptions import MeshLoadError
from meshscope.core.mesh_loader import load_mesh
from meshscope.ui.info_panel import InfoPanel
from meshscope.ui.viewport_widget import ViewportWidget
from meshscope.vtk_adapter.mesh_adapter import mesh_data_to_polydata

if TYPE_CHECKING:
    from meshscope.core.mesh_document import MeshDocument

logger = logging.getLogger("meshscope.ui.main_window")

SUPPORTED_EXTENSIONS = {".stl", ".obj", ".3mf", ".ply"}
FILE_FILTER = "Mesh Files (*.stl *.obj *.3mf *.ply)"


class MainWindow(QMainWindow):
    """Main application window.

    Hosts the VTK viewport, toolbar, menu bar, and status bar.
    Handles file loading via dialog, drag-drop, and CLI argument.
    """

    def __init__(self, file_path: str | None = None) -> None:
        super().__init__()
        self.setWindowTitle("meshscope")
        self.resize(1280, 800)
        self.setAcceptDrops(True)

        self._document: MeshDocument | None = None
        self._is_loading = False

        # Viewport (central widget)
        self._viewport = ViewportWidget(self)
        self.setCentralWidget(self._viewport)

        # Info panel (dock widget, left)
        self._info_panel = InfoPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._info_panel)

        # Actions
        self._create_actions()

        # Menu bar
        self._create_menus()

        # Toolbar (left, vertical)
        self._create_toolbar()

        # Status bar
        status_bar = QStatusBar(self)
        status_bar.setAccessibleName("Status bar")
        self.setStatusBar(status_bar)
        self.statusBar().showMessage("Ready")

        # Load file from CLI argument
        if file_path is not None:
            self._load_file(Path(file_path))

    @property
    def viewport(self) -> ViewportWidget:
        return self._viewport

    @property
    def document(self) -> MeshDocument | None:
        return self._document

    # --- Actions ---

    def _create_actions(self) -> None:
        self.open_action = QAction("Open", self)
        self.open_action.setShortcut(QKeySequence("Ctrl+O"))
        self.open_action.setToolTip("Open mesh file")
        self.open_action.triggered.connect(self._on_open)

        self.wireframe_action = QAction("Wire", self)
        self.wireframe_action.setShortcut(QKeySequence("W"))
        self.wireframe_action.setCheckable(True)
        self.wireframe_action.setEnabled(False)
        self.wireframe_action.setToolTip("Toggle wireframe overlay")
        self.wireframe_action.toggled.connect(self._on_wireframe_toggled)

        self.shading_action = QAction("Shade", self)
        self.shading_action.setShortcut(QKeySequence("S"))
        self.shading_action.setCheckable(True)
        self.shading_action.setEnabled(False)
        self.shading_action.setToolTip("Toggle smooth shading")
        self.shading_action.toggled.connect(self._on_shading_toggled)

        self.fit_action = QAction("Fit", self)
        self.fit_action.setShortcut(QKeySequence("F"))
        self.fit_action.setEnabled(False)
        self.fit_action.setToolTip("Fit model to view")
        self.fit_action.triggered.connect(self._on_fit)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.exit_action.triggered.connect(self.close)

    # --- Menus ---

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.wireframe_action)
        view_menu.addAction(self.shading_action)
        view_menu.addSeparator()
        view_menu.addAction(self.fit_action)
        view_menu.addSeparator()
        info_toggle = self._info_panel.toggleViewAction()
        info_toggle.setShortcut(QKeySequence("I"))
        view_menu.addAction(info_toggle)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("About", self)
        about_action.setToolTip("About meshscope")
        help_menu.addAction(about_action)

    # --- Toolbar ---

    def _create_toolbar(self) -> None:
        self.toolbar = QToolBar("Main Toolbar", self)
        self.toolbar.setOrientation(Qt.Orientation.Vertical)
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolbar.setAccessibleName("Main toolbar")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolbar)

        self.toolbar.addAction(self.open_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.wireframe_action)
        self.toolbar.addAction(self.shading_action)
        self.toolbar.addAction(self.fit_action)

    # --- File loading ---

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Mesh File", "", FILE_FILTER)
        if path:
            self._load_file(Path(path))

    def _load_file(self, path: Path) -> None:
        """Load a mesh file and display it in the viewport."""
        if self._is_loading:
            return

        self._is_loading = True
        self._set_state_loading(path.name)

        try:
            doc = load_mesh(path)
        except MeshLoadError as e:
            self._set_state_error(e.user_message)
            return
        except Exception as e:
            self._set_state_error(f"Unexpected error: {e}")
            logger.exception("Unexpected error loading %s", path)
            return
        finally:
            self._is_loading = False

        self._document = doc
        self._info_panel.set_document(doc)

        polydata = mesh_data_to_polydata(doc.mesh)
        self._viewport.scene_manager.display_mesh(polydata)
        self._viewport.vtk_render()

        self._set_state_success(path.name, doc.mesh.metadata.face_count)

        # Log warnings
        for warning in doc.warnings:
            logger.warning("Load warning: %s", warning)

    # --- State management ---

    def _set_state_loading(self, filename: str) -> None:
        self.statusBar().showMessage(f"Loading {filename}...")
        self._viewport.set_state("loading")
        self._set_render_actions_enabled(False)
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

    def _set_state_success(self, filename: str, face_count: int) -> None:
        self.statusBar().showMessage(f"{filename} — {face_count:,} faces")
        self._viewport.set_state("success")
        self._set_render_actions_enabled(True)

    def _set_state_error(self, message: str) -> None:
        self._document = None
        self._info_panel.clear()
        self._viewport.scene_manager.clear()
        self._viewport.vtk_render()
        self.statusBar().showMessage(message)
        self._viewport.show_error(message)
        self._set_render_actions_enabled(False)

    def _set_render_actions_enabled(self, enabled: bool) -> None:
        self.wireframe_action.setEnabled(enabled)
        self.shading_action.setEnabled(enabled)
        self.fit_action.setEnabled(enabled)

    # --- Toolbar callbacks ---

    def _on_wireframe_toggled(self, checked: bool) -> None:
        self._viewport.scene_manager.set_wireframe_overlay(checked)
        self._viewport.vtk_render()

    def _on_shading_toggled(self, checked: bool) -> None:
        self._viewport.scene_manager.set_smooth_shading(checked)
        self._viewport.vtk_render()

    def _on_fit(self) -> None:
        self._viewport.scene_manager.fit_to_view()
        self._viewport.vtk_render()

    # --- Drag and drop ---

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    ext = Path(url.toLocalFile()).suffix.lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        event.acceptProposedAction()
                        return

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    self._load_file(path)
                    return
