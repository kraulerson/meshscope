"""Main application window with toolbar, menus, status bar, and viewport."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QStatusBar,
    QToolBar,
)

from meshscope.core.config import load_config, save_config
from meshscope.core.exceptions import (
    MeshExportError,
    MeshLoadError,
    MeshRepairError,
    MeshTransformError,
)
from meshscope.core.mesh_analysis import analyze_mesh
from meshscope.core.mesh_exporter import check_symlink, export_mesh, get_format_warning
from meshscope.core.mesh_loader import load_mesh
from meshscope.core.mesh_repair import apply_repair, plan_repair
from meshscope.core.mesh_transform import mirror_mesh, rotate_mesh, scale_mesh
from meshscope.ui.info_panel import InfoPanel
from meshscope.ui.transform_dialog import TransformDialog
from meshscope.ui.viewport_widget import ViewportWidget
from meshscope.vtk_adapter.mesh_adapter import mesh_data_to_polydata
from meshscope.vtk_adapter.print_bed import PRINTER_PRESETS

if TYPE_CHECKING:
    from meshscope.core.mesh_document import MeshDocument

logger = logging.getLogger("meshscope.ui.main_window")

SUPPORTED_EXTENSIONS = {".stl", ".obj", ".3mf", ".ply"}
FILE_FILTER = "Mesh Files (*.stl *.obj *.3mf *.ply)"

EXPORT_FILTER = (
    "STL Files (*.stl);;OBJ Files (*.obj);;3MF Files (*.3mf);;PLY Files (*.ply)"
)

EXPORT_FILTER_TO_TYPE = {
    "STL Files (*.stl)": "stl",
    "OBJ Files (*.obj)": "obj",
    "3MF Files (*.3mf)": "3mf",
    "PLY Files (*.ply)": "ply",
}


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
        self._highlight_connected = False

        # Viewport (central widget)
        self._viewport = ViewportWidget(self)
        self.setCentralWidget(self._viewport)

        # Info panel (dock widget, left)
        self._info_panel = InfoPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._info_panel)

        # Config
        self._config = load_config()

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

        self.export_action = QAction("Export As...", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.export_action.setEnabled(False)
        self.export_action.setToolTip("Export mesh to another format")
        self.export_action.triggered.connect(self._on_export)

        self.bed_action = QAction("Bed", self)
        self.bed_action.setShortcut(QKeySequence("P"))
        self.bed_action.setCheckable(True)
        self.bed_action.setEnabled(False)
        self.bed_action.setToolTip("Toggle print bed volume overlay")
        self.bed_action.toggled.connect(self._on_bed_toggled)

        self.analyze_action = QAction("Analyze", self)
        self.analyze_action.setShortcut(QKeySequence("A"))
        self.analyze_action.setEnabled(False)
        self.analyze_action.setToolTip("Analyze mesh for printability issues")
        self.analyze_action.triggered.connect(self._on_analyze)

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_action.setEnabled(False)
        self.undo_action.setToolTip("Undo last mesh modification")
        self.undo_action.triggered.connect(self._on_undo)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        self.redo_action.setEnabled(False)
        self.redo_action.setToolTip("Redo last undone modification")
        self.redo_action.triggered.connect(self._on_redo)

        self.repair_action = QAction("Repair", self)
        self.repair_action.setShortcut(QKeySequence("R"))
        self.repair_action.setEnabled(False)
        self.repair_action.setToolTip("Repair mesh issues found by analysis")
        self.repair_action.triggered.connect(self._on_repair)

        self.transform_action = QAction("Transform", self)
        self.transform_action.setShortcut(QKeySequence("Ctrl+T"))
        self.transform_action.setEnabled(False)
        self.transform_action.setToolTip("Scale, rotate, or mirror mesh")
        self.transform_action.triggered.connect(self._on_transform)

    # --- Menus ---

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.transform_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.wireframe_action)
        view_menu.addAction(self.shading_action)
        view_menu.addSeparator()
        view_menu.addAction(self.fit_action)
        view_menu.addSeparator()
        info_toggle = self._info_panel.toggleViewAction()
        info_toggle.setShortcut(QKeySequence("I"))
        view_menu.addAction(info_toggle)

        view_menu.addSeparator()
        view_menu.addAction(self.bed_action)
        view_menu.addAction(self.analyze_action)
        view_menu.addAction(self.repair_action)

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
        self.toolbar.addAction(self.export_action)
        self.toolbar.addAction(self.undo_action)
        self.toolbar.addAction(self.redo_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.wireframe_action)
        self.toolbar.addAction(self.shading_action)
        self.toolbar.addAction(self.fit_action)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.bed_action)

        self.bed_preset_combo = QComboBox()
        self.bed_preset_combo.setAccessibleName("Print bed preset")
        self.bed_preset_combo.setEnabled(False)
        for key, preset in PRINTER_PRESETS.items():
            self.bed_preset_combo.addItem(preset["name"], key)
        self.bed_preset_combo.addItem("Custom...", "custom")
        saved_preset = self._config.get("print_bed", "preset")
        for i in range(self.bed_preset_combo.count()):
            if self.bed_preset_combo.itemData(i) == saved_preset:
                self.bed_preset_combo.setCurrentIndex(i)
                break
        self.bed_preset_combo.activated.connect(self._on_bed_preset_changed)
        self.toolbar.addWidget(self.bed_preset_combo)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.analyze_action)
        self.toolbar.addAction(self.repair_action)
        self.toolbar.addAction(self.transform_action)

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
        self._info_panel.clear_analysis()
        self._viewport.scene_manager.hide_highlights()
        self._info_panel.set_document(doc)
        self._update_undo_state()

        polydata = mesh_data_to_polydata(doc.mesh)
        self._viewport.scene_manager.display_mesh(polydata)
        self._viewport.vtk_render()

        self._set_state_success(path.name, doc.mesh.metadata.face_count)

        # Log warnings
        for warning in doc.warnings:
            logger.warning("Load warning: %s", warning)

        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

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
        self._info_panel.clear_analysis()
        self._viewport.scene_manager.clear()
        self._viewport.vtk_render()
        self.statusBar().showMessage(message)
        self._viewport.show_error(message)
        self._set_render_actions_enabled(False)

    def _set_render_actions_enabled(self, enabled: bool) -> None:
        self.wireframe_action.setEnabled(enabled)
        self.shading_action.setEnabled(enabled)
        self.fit_action.setEnabled(enabled)
        self.export_action.setEnabled(enabled)
        self.bed_action.setEnabled(enabled)
        self.bed_preset_combo.setEnabled(enabled)
        self.analyze_action.setEnabled(enabled)
        self.transform_action.setEnabled(enabled)
        self.repair_action.setEnabled(False)
        if not enabled:
            self.undo_action.setEnabled(False)
            self.redo_action.setEnabled(False)

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

    def _on_analyze(self) -> None:
        """Run mesh topology analysis."""
        if self._document is None:
            return
        try:
            analysis = analyze_mesh(self._document.mesh)
            self._document.analysis = analysis
            self._info_panel.show_analysis(analysis)

            # Connect highlight checkbox (disconnect first to avoid duplicates)
            if self._highlight_connected:
                self._info_panel.highlight_checkbox.toggled.disconnect(
                    self._on_highlight_toggled
                )
            self._info_panel.highlight_checkbox.toggled.connect(
                self._on_highlight_toggled
            )
            self._highlight_connected = True

            total_issues = (
                analysis.open_edge_count
                + analysis.non_manifold_edge_count
                + analysis.degenerate_face_count
                + analysis.hole_count
            )
            if total_issues > 0:
                plural = "s" if total_issues != 1 else ""
                self.statusBar().showMessage(
                    f"Analysis complete — {total_issues} issue{plural} found"
                )
                self._viewport.scene_manager.show_highlights(
                    analysis, self._document.mesh.vertices, self._document.mesh.faces
                )
                self._viewport.vtk_render()
            else:
                self.statusBar().showMessage("Analysis complete — no issues")
                self._viewport.scene_manager.hide_highlights()
                self._viewport.vtk_render()

            self._update_repair_state()

        except Exception as e:
            self.statusBar().showMessage(f"Analysis failed: {e}")
            logger.exception("Analysis failed")

    def _on_highlight_toggled(self, checked: bool) -> None:
        """Toggle viewport highlights on/off."""
        if (
            checked
            and self._document is not None
            and self._document.analysis is not None
        ):
            self._viewport.scene_manager.show_highlights(
                self._document.analysis,
                self._document.mesh.vertices,
                self._document.mesh.faces,
            )
        else:
            self._viewport.scene_manager.hide_highlights()
        self._viewport.vtk_render()

    def _on_undo(self) -> None:
        """Restore the previous mesh state."""
        if self._document is None or not self._document.undo_stack.can_undo():
            return

        restored = self._document.undo_stack.undo_swap(self._document.mesh)
        if restored is None:
            return

        self._document.mesh = restored
        self._document.analysis = None

        polydata = mesh_data_to_polydata(self._document.mesh)
        self._viewport.scene_manager.display_mesh(polydata, auto_fit=False)
        self._viewport.vtk_render()

        self._info_panel.set_document(self._document)
        self._info_panel.clear_analysis()
        self._viewport.scene_manager.hide_highlights()

        self._update_undo_state()
        self._update_repair_state()

        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

        self.statusBar().showMessage("Undo: mesh restored")

    def _on_redo(self) -> None:
        """Re-apply the last undone modification."""
        if self._document is None or not self._document.undo_stack.can_redo():
            return

        redone = self._document.undo_stack.redo_swap(self._document.mesh)
        if redone is None:
            return

        self._document.mesh = redone
        self._document.analysis = None

        polydata = mesh_data_to_polydata(self._document.mesh)
        self._viewport.scene_manager.display_mesh(polydata, auto_fit=False)
        self._viewport.vtk_render()

        self._info_panel.set_document(self._document)
        self._info_panel.clear_analysis()
        self._viewport.scene_manager.hide_highlights()

        self._update_undo_state()
        self._update_repair_state()

        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

        self.statusBar().showMessage("Redo: modification reapplied")

    def _update_undo_state(self) -> None:
        """Enable/disable undo and redo actions based on stack state."""
        if self._document is None:
            self.undo_action.setEnabled(False)
            self.redo_action.setEnabled(False)
            return
        self.undo_action.setEnabled(self._document.undo_stack.can_undo())
        self.redo_action.setEnabled(self._document.undo_stack.can_redo())

    def _update_repair_state(self) -> None:
        """Enable/disable repair action based on analysis results."""
        if self._document is None or self._document.analysis is None:
            self.repair_action.setEnabled(False)
            return
        a = self._document.analysis
        has_fixable = (
            a.hole_count > 0 or a.degenerate_face_count > 0 or a.open_edge_count > 0
        )
        self.repair_action.setEnabled(has_fixable)

    def _on_repair(self) -> None:
        """Run mesh repair workflow: plan -> confirm -> apply -> re-analyze."""
        if self._document is None or self._document.analysis is None:
            return

        # Plan
        try:
            plan = plan_repair(self._document.analysis, self._document.mesh)
        except Exception as e:
            self.statusBar().showMessage(f"Repair planning failed: {e}")
            logger.exception("Repair planning failed")
            return

        # Build confirmation dialog
        lines: list[str] = []
        if plan.flipped_normal_count > 0:
            lines.append(f"Fix {plan.flipped_normal_count} flipped normal(s)")
        if plan.holes_to_fill > 0:
            lines.append(f"Fill {plan.holes_to_fill} hole(s)")
        if plan.degenerate_faces_to_remove > 0:
            lines.append(f"Remove {plan.degenerate_faces_to_remove} degenerate face(s)")

        if not lines:
            self.statusBar().showMessage("No repairs needed — mesh is already clean.")
            return

        body = "The following repairs will be applied:\n\n"
        body += "\n".join(f"  \u2022 {line}" for line in lines)

        if plan.high_impact_warning and self._document.mesh.metadata.face_count > 0:
            pct = (
                abs(plan.estimated_face_delta)
                / self._document.mesh.metadata.face_count
                * 100
            )
            body += (
                f"\n\nWarning: Face count will change by {pct:.0f}%. "
                "Review results carefully."
            )

        result = QMessageBox.warning(
            self,
            "Repair Mesh",
            body,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        if result != QMessageBox.StandardButton.Ok:
            return

        # Apply
        try:
            repair_result = apply_repair(self._document.mesh, plan)
        except MeshRepairError as e:
            self.statusBar().showMessage(f"Repair failed: {e.user_message}")
            logger.error("Repair failed: %s", e.user_message)
            return
        except Exception as e:
            self.statusBar().showMessage(f"Repair failed: {e}")
            logger.exception("Repair failed")
            return

        # Check for no-op
        total_changes = (
            repair_result.normals_fixed
            + repair_result.holes_filled
            + repair_result.degenerate_faces_removed
        )
        if total_changes == 0:
            self.statusBar().showMessage("No repairs needed — mesh is already clean.")
            return

        # Push pre-repair state for undo, then replace mesh
        self._document.undo_stack.push(self._document.mesh)
        self._document.mesh = repair_result.mesh

        # Update viewport
        polydata = mesh_data_to_polydata(self._document.mesh)
        self._viewport.scene_manager.display_mesh(polydata, auto_fit=False)
        self._viewport.vtk_render()

        # Update info panel with new mesh metadata
        self._info_panel.set_document(self._document)

        # Auto re-analyze
        try:
            analysis = analyze_mesh(self._document.mesh)
            self._document.analysis = analysis
            self._info_panel.show_analysis(analysis)

            total_issues = (
                analysis.open_edge_count
                + analysis.non_manifold_edge_count
                + analysis.degenerate_face_count
                + analysis.hole_count
            )
            if total_issues > 0:
                self._viewport.scene_manager.show_highlights(
                    analysis,
                    self._document.mesh.vertices,
                    self._document.mesh.faces,
                )
            else:
                self._viewport.scene_manager.hide_highlights()
            self._viewport.vtk_render()
        except Exception:
            logger.exception("Post-repair analysis failed")

        # Update action states
        self._update_undo_state()
        self._update_repair_state()

        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

        # Status bar
        parts: list[str] = []
        if repair_result.normals_fixed > 0:
            parts.append(f"{repair_result.normals_fixed} normals fixed")
        if repair_result.holes_filled > 0:
            parts.append(f"{repair_result.holes_filled} holes filled")
        if repair_result.degenerate_faces_removed > 0:
            parts.append(
                f"{repair_result.degenerate_faces_removed} degenerate faces removed"
            )
        summary = ", ".join(parts)

        if repair_result.fully_repaired:
            self.statusBar().showMessage(f"Repair complete — {summary}")
        else:
            self.statusBar().showMessage(
                f"Repair partially complete — {summary}. "
                "Some issues remain. See analysis panel."
            )

    def _on_transform(self) -> None:
        """Open transform dialog and apply the selected transform."""
        if self._document is None:
            return

        dialog = TransformDialog(self._document.mesh.metadata.bounding_box, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        op = dialog.operation()
        try:
            if op == "scale":
                result = scale_mesh(self._document.mesh, dialog.scale_factor())
            elif op == "rotate":
                result = rotate_mesh(
                    self._document.mesh, dialog.rotate_axis(), dialog.rotate_degrees()
                )
            elif op == "mirror":
                result = mirror_mesh(self._document.mesh, dialog.mirror_axis())
            else:
                return
        except MeshTransformError as e:
            self.statusBar().showMessage(f"Transform failed: {e.user_message}")
            logger.error("Transform failed: %s", e.user_message)
            return
        except Exception as e:
            self.statusBar().showMessage(f"Transform failed: {e}")
            logger.exception("Transform failed")
            return

        # Push pre-transform state for undo
        self._document.undo_stack.push(self._document.mesh)
        self._document.mesh = result.mesh

        # Invalidate analysis
        self._document.analysis = None

        # Update viewport
        polydata = mesh_data_to_polydata(self._document.mesh)
        self._viewport.scene_manager.display_mesh(polydata, auto_fit=False)
        self._viewport.vtk_render()

        # Update info panel
        self._info_panel.set_document(self._document)
        self._info_panel.clear_analysis()
        self._viewport.scene_manager.hide_highlights()

        # Update action states
        self._update_undo_state()
        self._update_repair_state()

        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

        # Status bar
        msg = result.description
        if result.warning:
            msg += f" — {result.warning}"
        self.statusBar().showMessage(msg)

    def _on_export(self) -> None:
        """Handle Export As action."""
        if self._document is None:
            return

        path_str, selected_filter = QFileDialog.getSaveFileName(
            self, "Export As", "", EXPORT_FILTER
        )
        if not path_str:
            return

        path = Path(path_str)

        # Detect format from selected filter or file extension
        file_type = EXPORT_FILTER_TO_TYPE.get(selected_filter)
        if file_type is None:
            ext = path.suffix.lower().lstrip(".")
            file_type = ext if ext in {"stl", "obj", "3mf", "ply"} else None
        if file_type is None:
            QMessageBox.warning(
                self,
                "Export Error",
                "Could not determine export format. "
                "Use a supported extension (.stl, .obj, .3mf, .ply).",
            )
            return

        # Ensure correct extension
        expected_ext = f".{file_type}"
        if path.suffix.lower() != expected_ext:
            path = path.with_suffix(expected_ext)

        # Symlink check
        resolved = check_symlink(path)
        if resolved is not None:
            result = QMessageBox.warning(
                self,
                "Symlink Detected",
                f"Target resolves to:\n{resolved}\n\nContinue?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if result != QMessageBox.StandardButton.Ok:
                return

        # Overwrite source check
        if (
            self._document.source_path
            and path.resolve() == Path(self._document.source_path).resolve()
        ):
            result = QMessageBox.warning(
                self,
                "Overwrite Source",
                "This will overwrite the currently loaded file. Continue?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if result != QMessageBox.StandardButton.Ok:
                return

        # Format data loss warning
        warning = get_format_warning(file_type)
        if warning:
            result = QMessageBox.warning(
                self,
                "Format Warning",
                f"{warning}\n\nContinue?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if result != QMessageBox.StandardButton.Ok:
                return

        # Perform export
        try:
            export_mesh(self._document.mesh, path, file_type)
            self.statusBar().showMessage(f"Exported to {path.name}")
            logger.info("Exported to %s", path)
        except MeshExportError as e:
            QMessageBox.critical(self, "Export Error", e.user_message)
            logger.error("Export failed: %s", e.user_message)

    # --- Print bed ---

    def _on_bed_toggled(self, checked: bool) -> None:
        if checked and self._document is not None:
            dims = self._get_bed_dimensions()
            bbox = self._document.mesh.metadata.bounding_box
            overflow = self._viewport.scene_manager.show_print_bed(
                dims[0], dims[1], dims[2], bbox
            )
            if overflow:
                self.statusBar().showMessage(overflow)
            self._viewport.vtk_render()
        else:
            self._viewport.scene_manager.hide_print_bed()
            self._viewport.vtk_render()
            if self._document is not None:
                self.statusBar().showMessage(
                    f"{Path(self._document.source_path).name} — "
                    f"{self._document.mesh.metadata.face_count:,} faces"
                )

    def _on_bed_preset_changed(self, index: int) -> None:
        key = self.bed_preset_combo.itemData(index)
        if key == "custom":
            if not self._show_custom_bed_dialog():
                saved = self._config.get("print_bed", "preset")
                for i in range(self.bed_preset_combo.count()):
                    if self.bed_preset_combo.itemData(i) == saved:
                        self.bed_preset_combo.blockSignals(True)
                        self.bed_preset_combo.setCurrentIndex(i)
                        self.bed_preset_combo.blockSignals(False)
                        break
                return
            key = "custom"
        self._config.set("print_bed", "preset", key)
        save_config(self._config)
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

    def _get_bed_dimensions(self) -> tuple[int, int, int]:
        key = self.bed_preset_combo.itemData(self.bed_preset_combo.currentIndex())
        if key == "custom":
            return (
                self._config.get("print_bed", "custom_x"),
                self._config.get("print_bed", "custom_y"),
                self._config.get("print_bed", "custom_z"),
            )
        preset = PRINTER_PRESETS.get(key, PRINTER_PRESETS["ender_3"])
        return (preset["x"], preset["y"], preset["z"])

    def _show_custom_bed_dialog(self) -> bool:
        dialog = QDialog(self)
        dialog.setWindowTitle("Custom Print Volume")
        layout = QFormLayout(dialog)

        x_spin = QSpinBox()
        x_spin.setRange(1, 2000)
        x_spin.setSuffix(" mm")
        x_spin.setValue(self._config.get("print_bed", "custom_x"))
        x_spin.setAccessibleName("Bed width X in millimeters")

        y_spin = QSpinBox()
        y_spin.setRange(1, 2000)
        y_spin.setSuffix(" mm")
        y_spin.setValue(self._config.get("print_bed", "custom_y"))
        y_spin.setAccessibleName("Bed depth Y in millimeters")

        z_spin = QSpinBox()
        z_spin.setRange(1, 2000)
        z_spin.setSuffix(" mm")
        z_spin.setValue(self._config.get("print_bed", "custom_z"))
        z_spin.setAccessibleName("Bed height Z in millimeters")

        layout.addRow("Width (X):", x_spin)
        layout.addRow("Depth (Y):", y_spin)
        layout.addRow("Height (Z):", z_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False

        x_val, y_val, z_val = x_spin.value(), y_spin.value(), z_spin.value()
        if x_val > 1000 or y_val > 1000 or z_val > 1000:
            QMessageBox.warning(
                self,
                "Large Dimensions",
                "Bed size exceeds 1000mm. Verify dimensions are in millimeters.",
            )
        self._config.set("print_bed", "custom_x", x_val)
        self._config.set("print_bed", "custom_y", y_val)
        self._config.set("print_bed", "custom_z", z_val)
        self._config.set("print_bed", "preset", "custom")
        save_config(self._config)
        return True

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
