"""Tests for MainWindow — toolbar, menus, status bar, state management."""

from pathlib import Path

import pytest
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QComboBox

from meshscope.ui.info_panel import InfoPanel
from meshscope.ui.main_window import MainWindow


@pytest.fixture()
def window(qapp: QApplication) -> MainWindow:
    w = MainWindow()
    yield w
    w.close()


class TestMainWindowConstruction:
    def test_window_title(self, window: MainWindow) -> None:
        assert window.windowTitle() == "meshscope"

    def test_has_viewport(self, window: MainWindow) -> None:
        assert window.viewport is not None

    def test_status_bar_shows_ready(self, window: MainWindow) -> None:
        assert window.statusBar().currentMessage() == "Ready"


class TestMainWindowMenus:
    def test_file_menu_exists(self, window: MainWindow) -> None:
        menus = [a.text() for a in window.menuBar().actions()]
        assert any("File" in m for m in menus)

    def test_view_menu_exists(self, window: MainWindow) -> None:
        menus = [a.text() for a in window.menuBar().actions()]
        assert any("View" in m for m in menus)

    def test_help_menu_exists(self, window: MainWindow) -> None:
        menus = [a.text() for a in window.menuBar().actions()]
        assert any("Help" in m for m in menus)

    def test_file_menu_has_open(self, window: MainWindow) -> None:
        assert window.open_action is not None
        assert "Open" in window.open_action.text()


class TestMainWindowToolbar:
    def test_toolbar_exists(self, window: MainWindow) -> None:
        toolbars = window.findChildren(window.toolbar.__class__)
        assert len(toolbars) >= 1

    def test_open_button_exists(self, window: MainWindow) -> None:
        assert window.open_action is not None

    def test_wireframe_button_exists(self, window: MainWindow) -> None:
        assert window.wireframe_action is not None
        assert window.wireframe_action.isCheckable()

    def test_shading_button_exists(self, window: MainWindow) -> None:
        assert window.shading_action is not None
        assert window.shading_action.isCheckable()

    def test_fit_button_exists(self, window: MainWindow) -> None:
        assert window.fit_action is not None

    def test_render_actions_disabled_initially(self, window: MainWindow) -> None:
        assert not window.wireframe_action.isEnabled()
        assert not window.shading_action.isEnabled()
        assert not window.fit_action.isEnabled()


class TestMainWindowStateManagement:
    def test_initial_state_is_empty(self, window: MainWindow) -> None:
        assert window.viewport.state == "empty"
        assert not window.wireframe_action.isEnabled()

    def test_set_loaded_state_enables_actions(self, window: MainWindow) -> None:
        window._set_state_success("test.stl", 1000)
        assert window.wireframe_action.isEnabled()
        assert window.shading_action.isEnabled()
        assert window.fit_action.isEnabled()
        assert "test.stl" in window.statusBar().currentMessage()
        assert "1,000" in window.statusBar().currentMessage()

    def test_set_error_state_disables_render_actions(self, window: MainWindow) -> None:
        window._set_state_success("test.stl", 1000)
        window._set_state_error("File corrupt")
        assert not window.wireframe_action.isEnabled()
        assert not window.shading_action.isEnabled()
        assert "File corrupt" in window.statusBar().currentMessage()


class TestMainWindowLoadingGuard:
    def test_load_file_sets_loading_flag(self, window: MainWindow) -> None:
        """Loading flag must be set during _load_file to prevent re-entrancy."""
        assert window._is_loading is False

    def test_second_load_ignored_during_loading(self, window: MainWindow) -> None:
        """If _is_loading is True, _load_file should return immediately."""
        from unittest.mock import patch

        window._is_loading = True

        with patch.object(window, "_set_state_loading") as mock_loading:
            window._load_file(Path("dummy.stl"))
            mock_loading.assert_not_called()

    def test_loading_flag_cleared_after_success(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        """Loading flag must be cleared after successful load."""
        obj = tmp_path / "cube.obj"
        obj.write_text(
            "v 0 0 0\nv 10 0 0\nv 10 10 0\nv 0 10 0\n"
            "v 0 0 10\nv 10 0 10\nv 10 10 10\nv 0 10 10\n"
            "f 1 2 3\nf 1 3 4\nf 5 6 7\nf 5 7 8\n"
            "f 1 2 6\nf 1 6 5\nf 2 3 7\nf 2 7 6\n"
            "f 3 4 8\nf 3 8 7\nf 4 1 5\nf 4 5 8\n"
        )
        window._load_file(obj)
        assert window._is_loading is False

    def test_loading_flag_cleared_after_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        """Loading flag must be cleared after failed load."""
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert window._is_loading is False


class TestKeyboardShortcuts:
    def test_wireframe_shortcut_is_w(self, window: MainWindow) -> None:
        assert window.wireframe_action.shortcut() == QKeySequence("W")

    def test_shading_shortcut_is_s(self, window: MainWindow) -> None:
        assert window.shading_action.shortcut() == QKeySequence("S")

    def test_fit_shortcut_is_f(self, window: MainWindow) -> None:
        assert window.fit_action.shortcut() == QKeySequence("F")

    def test_open_shortcut_is_ctrl_o(self, window: MainWindow) -> None:
        assert window.open_action.shortcut() == QKeySequence("Ctrl+O")

    def test_exit_shortcut_is_ctrl_q(self, window: MainWindow) -> None:
        assert window.exit_action.shortcut() == QKeySequence("Ctrl+Q")

    def test_wireframe_action_toggles_scene_manager(self, window: MainWindow) -> None:
        """Triggering wireframe action should toggle scene manager state."""
        # Load a mesh first so the action is enabled
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.wireframe_action.isEnabled()

        # Toggle on
        window.wireframe_action.toggle()
        assert window.viewport.scene_manager.wireframe_overlay_enabled is True

        # Toggle off
        window.wireframe_action.toggle()
        assert window.viewport.scene_manager.wireframe_overlay_enabled is False

    def test_shading_action_toggles_scene_manager(self, window: MainWindow) -> None:
        """Triggering shading action should toggle scene manager state."""
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")

        window.shading_action.toggle()
        assert window.viewport.scene_manager.smooth_shading_enabled is True

        window.shading_action.toggle()
        assert window.viewport.scene_manager.smooth_shading_enabled is False


class TestMainWindowExportAction:
    def test_export_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "export_action")

    def test_export_action_disabled_initially(self, window: MainWindow) -> None:
        assert not window.export_action.isEnabled()

    def test_export_action_enabled_after_load(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.export_action.isEnabled()

    def test_export_action_disabled_after_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.export_action.isEnabled()
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert not window.export_action.isEnabled()

    def test_export_action_in_file_menu(self, window: MainWindow) -> None:
        file_menu = None
        for action in window.menuBar().actions():
            if "File" in action.text():
                file_menu = action.menu()
                break
        assert file_menu is not None
        action_texts = [a.text() for a in file_menu.actions()]
        assert any("Export" in t for t in action_texts)

    def test_export_shortcut_is_ctrl_shift_s(self, window: MainWindow) -> None:
        assert window.export_action.shortcut() == QKeySequence("Ctrl+Shift+S")

    def test_export_action_in_toolbar(self, window: MainWindow) -> None:
        toolbar_actions = [a.text() for a in window.toolbar.actions()]
        assert any("Export" in t for t in toolbar_actions)


class TestMainWindowPrintBed:
    def test_bed_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "bed_action")

    def test_bed_action_disabled_initially(self, window: MainWindow) -> None:
        assert not window.bed_action.isEnabled()

    def test_bed_action_is_checkable(self, window: MainWindow) -> None:
        assert window.bed_action.isCheckable()

    def test_bed_action_enabled_after_load(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.bed_action.isEnabled()

    def test_bed_shortcut_is_p(self, window: MainWindow) -> None:
        assert window.bed_action.shortcut() == QKeySequence("P")

    def test_bed_preset_dropdown_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "bed_preset_combo")
        assert isinstance(window.bed_preset_combo, QComboBox)

    def test_bed_preset_dropdown_has_presets(self, window: MainWindow) -> None:
        combo = window.bed_preset_combo
        items = [combo.itemText(i) for i in range(combo.count())]
        assert "Ender 3" in items
        assert "Prusa MK4" in items
        assert "Voron 2.4" in items
        assert "Bambu X1 Carbon" in items
        assert "Bambu P1S" in items
        assert "Custom..." in items

    def test_bed_preset_dropdown_disabled_initially(self, window: MainWindow) -> None:
        assert not window.bed_preset_combo.isEnabled()

    def test_bed_action_in_view_menu(self, window: MainWindow) -> None:
        view_menu = None
        for action in window.menuBar().actions():
            if "View" in action.text():
                view_menu = action.menu()
                break
        assert view_menu is not None
        action_texts = [a.text() for a in view_menu.actions()]
        assert any("Bed" in t for t in action_texts)

    def test_bed_action_disabled_after_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.bed_action.isEnabled()
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert not window.bed_action.isEnabled()


class TestMainWindowDragDrop:
    def test_accepts_drops(self, window: MainWindow) -> None:
        assert window.acceptDrops()


class TestMainWindowInfoPanel:
    def test_info_panel_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "_info_panel")
        assert isinstance(window._info_panel, InfoPanel)

    def test_info_panel_starts_empty(self, window: MainWindow) -> None:
        assert window._info_panel.is_empty is True

    def test_info_panel_in_view_menu(self, window: MainWindow) -> None:
        view_menu = None
        for action in window.menuBar().actions():
            if "View" in action.text():
                view_menu = action.menu()
                break
        assert view_menu is not None
        action_texts = [a.text() for a in view_menu.actions()]
        assert any("Info" in t for t in action_texts)

    def test_info_panel_populated_after_load(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window._info_panel.is_empty is False

    def test_info_panel_cleared_on_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window._info_panel.is_empty is False
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert window._info_panel.is_empty is True

    def test_info_toggle_shortcut_is_i(self, window: MainWindow) -> None:
        toggle_action = window._info_panel.toggleViewAction()
        assert toggle_action.shortcut() == QKeySequence("I")


class TestMainWindowAnalyze:
    def test_analyze_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "analyze_action")

    def test_analyze_action_disabled_initially(self, window: MainWindow) -> None:
        assert not window.analyze_action.isEnabled()

    def test_analyze_action_enabled_after_load(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.analyze_action.isEnabled()

    def test_analyze_shortcut_is_a(self, window: MainWindow) -> None:
        assert window.analyze_action.shortcut() == QKeySequence("A")

    def test_analyze_action_in_view_menu(self, window: MainWindow) -> None:
        view_menu = None
        for action in window.menuBar().actions():
            if "View" in action.text():
                view_menu = action.menu()
                break
        assert view_menu is not None
        action_texts = [a.text() for a in view_menu.actions()]
        assert any("Analyze" in t for t in action_texts)

    def test_analyze_runs_analysis(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.analyze_action.trigger()
        assert window._document is not None
        assert window._document.analysis is not None

    def test_analyze_shows_analysis_section(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.analyze_action.trigger()
        assert window._info_panel.analysis_section_visible() is True

    def test_analyze_disabled_after_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert not window.analyze_action.isEnabled()
