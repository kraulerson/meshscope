"""Integration tests for file loading through the UI pipeline."""

from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication

from meshscope.ui.main_window import MainWindow

from ._native_window import requires_native_window

# These tests construct MainWindow/ViewportWidget, which build a VTK render
# window from QWidget.winId(). That handle is not dereferenceable under the
# offscreen QPA plugin, so the process segfaults instead of raising.
pytestmark = requires_native_window

FIXTURES = Path(__file__).parent.parent / "fixtures"
VALID = FIXTURES / "valid"
INVALID = FIXTURES / "invalid"


@pytest.fixture()
def window(qapp: QApplication) -> MainWindow:
    w = MainWindow()
    yield w
    w.close()


class TestFileLoadingSuccess:
    def test_load_stl_displays_mesh(self, window: MainWindow) -> None:
        window._load_file(VALID / "cube.stl")
        assert window.viewport.state == "success"
        assert window.viewport.scene_manager.has_mesh is True
        assert window.document is not None
        assert window.document.mesh.metadata.face_count == 12

    def test_load_obj_displays_mesh(self, window: MainWindow) -> None:
        window._load_file(VALID / "cube.obj")
        assert window.viewport.state == "success"
        assert window.viewport.scene_manager.has_mesh is True

    def test_load_ply_displays_mesh(self, window: MainWindow) -> None:
        window._load_file(VALID / "cube.ply")
        assert window.viewport.state == "success"

    def test_load_3mf_displays_mesh(self, window: MainWindow) -> None:
        window._load_file(VALID / "cube.3mf")
        assert window.viewport.state == "success"

    def test_status_bar_shows_filename_and_count(self, window: MainWindow) -> None:
        window._load_file(VALID / "cube.stl")
        msg = window.statusBar().currentMessage()
        assert "cube.stl" in msg
        assert "12" in msg

    def test_toolbar_enabled_after_load(self, window: MainWindow) -> None:
        window._load_file(VALID / "cube.stl")
        assert window.wireframe_action.isEnabled()
        assert window.shading_action.isEnabled()
        assert window.fit_action.isEnabled()

    def test_reload_replaces_mesh(self, window: MainWindow) -> None:
        window._load_file(VALID / "cube.stl")
        window._load_file(VALID / "cube.obj")
        assert window.viewport.state == "success"
        assert "cube.obj" in window.statusBar().currentMessage()


class TestFileLoadingErrors:
    def test_corrupt_file_shows_error(self, window: MainWindow) -> None:
        window._load_file(INVALID / "corrupt.stl")
        assert window.viewport.state == "error"
        assert not window.wireframe_action.isEnabled()

    def test_missing_file_shows_error(self, window: MainWindow) -> None:
        window._load_file(Path("/nonexistent/file.stl"))
        assert window.viewport.state == "error"
        assert "not found" in window.statusBar().currentMessage().lower()

    def test_error_after_success_keeps_error_state(self, window: MainWindow) -> None:
        window._load_file(VALID / "cube.stl")
        assert window.viewport.state == "success"
        window._load_file(INVALID / "corrupt.stl")
        assert window.viewport.state == "error"
        assert not window.wireframe_action.isEnabled()

    def test_error_after_success_clears_mesh(self, window: MainWindow) -> None:
        """Previous mesh must be cleared from viewport when load fails."""
        window._load_file(VALID / "cube.stl")
        assert window.viewport.scene_manager.has_mesh is True
        window._load_file(INVALID / "corrupt.stl")
        assert window.viewport.scene_manager.has_mesh is False
        assert window.document is None


class TestCLIArgument:
    def test_file_path_loaded_on_construction(self, qapp: QApplication) -> None:
        window = MainWindow(file_path=str(VALID / "cube.stl"))
        assert window.viewport.state == "success"
        assert window.document is not None
        window.close()

    def test_invalid_path_shows_error(self, qapp: QApplication) -> None:
        window = MainWindow(file_path="/nonexistent/file.stl")
        assert window.viewport.state == "error"
        window.close()

    def test_dunder_main_module_exists(self) -> None:
        """Regression: python -m meshscope requires __main__.py."""
        import importlib.util

        spec = importlib.util.find_spec("meshscope.__main__")
        assert spec is not None, "meshscope.__main__ must exist for python -m meshscope"


class TestDragDropLoading:
    def test_drag_enter_accepts_stl(self, window: MainWindow) -> None:
        """Drag-enter with a .stl file should be accepted."""
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(VALID / "cube.stl"))])
        event = QDragEnterEvent(
            window.rect().center(),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        window.dragEnterEvent(event)
        assert event.isAccepted()

    def test_drag_enter_rejects_unsupported_format(self, window: MainWindow) -> None:
        """Drag-enter with an unsupported extension should not be accepted."""
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile("/some/file.txt")])
        event = QDragEnterEvent(
            window.rect().center(),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        window.dragEnterEvent(event)
        assert not event.isAccepted()

    def test_drop_stl_loads_mesh(self, window: MainWindow) -> None:
        """Dropping a valid .stl file should load and display it."""
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(VALID / "cube.stl"))])
        event = QDropEvent(
            window.rect().center().toPointF(),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        window.dropEvent(event)
        assert window.viewport.state == "success"
        assert window.document is not None
        assert window.document.mesh.metadata.face_count == 12
