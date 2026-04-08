# Print Bed Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a toggleable 3D print volume overlay (wireframe box + grid floor) with 5 printer presets, custom dimensions, overflow detection, and a schema-versioned preferences system.

**Architecture:** Config module (`config.py`) for preferences persistence. `PrintBedManager` creates VTK actors for grid, box, and overflow hatching. SceneManager delegates to PrintBedManager. MainWindow adds toolbar toggle + preset dropdown + menu + custom dialog.

**Tech Stack:** PySide6 (QAction, QComboBox, QDialog, QSpinBox, QMessageBox), VTK (vtkActor, vtkPolyData, vtkPolyDataMapper, vtkPoints, vtkCellArray, vtkLine), Python stdlib (json, pathlib, tempfile)

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/meshscope/core/config.py` | Schema-versioned JSON config: load, save, atomic write, recovery |
| Create | `src/meshscope/vtk_adapter/print_bed.py` | PrintBedManager: VTK actors for grid, box, overflow. Preset data. Overflow calculation. |
| Modify | `src/meshscope/vtk_adapter/scene_manager.py` | show_print_bed / hide_print_bed delegation to PrintBedManager |
| Modify | `src/meshscope/ui/main_window.py` | Bed toggle action, preset dropdown, custom dialog, menu, config integration |
| Create | `tests/unit/test_config.py` | Config load/save/recovery tests |
| Create | `tests/unit/test_print_bed.py` | PrintBedManager actor creation, overflow calculation tests |
| Modify | `tests/unit/test_scene_manager.py` | SceneManager print bed integration tests |
| Modify | `tests/ui/test_main_window.py` | MainWindow print bed UI tests |

---

### Task 1: Config module — load, save, defaults

**Files:**
- Create: `tests/unit/test_config.py`
- Create: `src/meshscope/core/config.py`

- [ ] **Step 1: Write failing tests for config**

Create `tests/unit/test_config.py`:

```python
"""Tests for application configuration persistence."""

from pathlib import Path

from meshscope.core.config import AppConfig, load_config, save_config


class TestAppConfigDefaults:
    def test_default_version(self) -> None:
        config = AppConfig()
        assert config.version == 1

    def test_default_preset(self) -> None:
        config = AppConfig()
        assert config.get("print_bed", "preset") == "ender_3"

    def test_default_custom_dimensions(self) -> None:
        config = AppConfig()
        assert config.get("print_bed", "custom_x") == 220
        assert config.get("print_bed", "custom_y") == 220
        assert config.get("print_bed", "custom_z") == 250

    def test_set_and_get(self) -> None:
        config = AppConfig()
        config.set("print_bed", "preset", "prusa_mk4")
        assert config.get("print_bed", "preset") == "prusa_mk4"


class TestConfigSaveLoad:
    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        config = AppConfig()
        config.set("print_bed", "preset", "voron_2_4")
        config_path = tmp_path / "config.json"
        save_config(config, config_path)
        loaded = load_config(config_path)
        assert loaded.get("print_bed", "preset") == "voron_2_4"

    def test_load_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "nonexistent.json"
        config = load_config(config_path)
        assert config.get("print_bed", "preset") == "ender_3"

    def test_load_corrupt_file_returns_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text("not json{{{")
        config = load_config(config_path)
        assert config.version == 1
        assert config.get("print_bed", "preset") == "ender_3"

    def test_load_wrong_version_returns_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text('{"version": 999}')
        config = load_config(config_path)
        assert config.version == 1

    def test_load_missing_keys_fills_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text('{"version": 1, "print_bed": {"preset": "bambu_x1c"}}')
        config = load_config(config_path)
        assert config.get("print_bed", "preset") == "bambu_x1c"
        assert config.get("print_bed", "custom_x") == 220

    def test_save_atomic_creates_file(self, tmp_path: Path) -> None:
        config = AppConfig()
        config_path = tmp_path / "config.json"
        save_config(config, config_path)
        assert config_path.exists()
        assert config_path.stat().st_size > 0

    def test_save_no_temp_files_left(self, tmp_path: Path) -> None:
        config = AppConfig()
        config_path = tmp_path / "config.json"
        save_config(config, config_path)
        files = list(tmp_path.iterdir())
        assert len(files) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement config module**

Create `src/meshscope/core/config.py`:

```python
"""Schema-versioned application configuration with atomic persistence."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("meshscope.core.config")

CURRENT_SCHEMA_VERSION = 1

DEFAULT_CONFIG: dict[str, Any] = {
    "version": CURRENT_SCHEMA_VERSION,
    "print_bed": {
        "preset": "ender_3",
        "custom_x": 220,
        "custom_y": 220,
        "custom_z": 250,
    },
}


def _get_config_path() -> Path:
    """Return the default config file path."""
    from meshscope.core.logging import _get_config_dir

    config_dir = _get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Merge overlay into base, filling missing keys from base."""
    result = base.copy()
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class AppConfig:
    """Application configuration backed by a dict with schema version."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        if data is None:
            self._data = json.loads(json.dumps(DEFAULT_CONFIG))
        else:
            self._data = _deep_merge(
                json.loads(json.dumps(DEFAULT_CONFIG)), data
            )

    @property
    def version(self) -> int:
        return self._data.get("version", CURRENT_SCHEMA_VERSION)

    def get(self, section: str, key: str) -> Any:
        """Get a config value by section and key."""
        return self._data.get(section, {}).get(key)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a config value by section and key."""
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value

    def to_dict(self) -> dict[str, Any]:
        """Return the config as a plain dict for serialization."""
        return self._data


def load_config(path: Path | None = None) -> AppConfig:
    """Load config from file. Returns defaults on any error."""
    if path is None:
        path = _get_config_path()

    if not path.exists():
        logger.info("Config file not found, using defaults: %s", path)
        return AppConfig()

    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Corrupt config file, resetting to defaults: %s", e)
        return AppConfig()

    if not isinstance(data, dict):
        logger.warning("Config is not a dict, resetting to defaults")
        return AppConfig()

    version = data.get("version")
    if version != CURRENT_SCHEMA_VERSION:
        logger.warning(
            "Unknown config version %s, resetting to defaults", version
        )
        return AppConfig()

    return AppConfig(data)


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Save config to file with atomic write."""
    if path is None:
        path = _get_config_path()

    path.parent.mkdir(parents=True, exist_ok=True)

    temp_fd = None
    temp_path = None
    try:
        temp_fd, temp_path_str = tempfile.mkstemp(
            suffix=".json.tmp", dir=path.parent
        )
        os.close(temp_fd)
        temp_fd = None
        temp_path = Path(temp_path_str)

        temp_path.write_text(
            json.dumps(config.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(str(temp_path), str(path))
        temp_path = None
        logger.info("Config saved to %s", path)
    except OSError as e:
        logger.error("Failed to save config: %s", e)
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_config.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/config.py tests/unit/test_config.py
git commit -m "feat(config): add schema-versioned config with atomic persistence"
```

---

### Task 2: PrintBedManager — presets, actors, overflow

**Files:**
- Create: `tests/unit/test_print_bed.py`
- Create: `src/meshscope/vtk_adapter/print_bed.py`

- [ ] **Step 1: Write failing tests for PrintBedManager**

Create `tests/unit/test_print_bed.py`:

```python
"""Tests for print bed VTK actor management."""

from meshscope.core.mesh_data import BoundingBox
from meshscope.vtk_adapter.print_bed import (
    PRINTER_PRESETS,
    PrintBedManager,
    get_overflow_text,
)


class TestPrinterPresets:
    def test_ender_3_exists(self) -> None:
        assert "ender_3" in PRINTER_PRESETS
        p = PRINTER_PRESETS["ender_3"]
        assert p["x"] == 220
        assert p["y"] == 220
        assert p["z"] == 250

    def test_prusa_mk4_exists(self) -> None:
        assert "prusa_mk4" in PRINTER_PRESETS
        assert PRINTER_PRESETS["prusa_mk4"]["x"] == 250

    def test_voron_2_4_exists(self) -> None:
        assert "voron_2_4" in PRINTER_PRESETS
        assert PRINTER_PRESETS["voron_2_4"]["x"] == 350

    def test_bambu_x1c_exists(self) -> None:
        assert "bambu_x1c" in PRINTER_PRESETS
        assert PRINTER_PRESETS["bambu_x1c"]["x"] == 256

    def test_bambu_p1s_exists(self) -> None:
        assert "bambu_p1s" in PRINTER_PRESETS
        assert PRINTER_PRESETS["bambu_p1s"]["x"] == 256

    def test_all_presets_have_name_xyz(self) -> None:
        for key, preset in PRINTER_PRESETS.items():
            assert "name" in preset, f"{key} missing name"
            assert "x" in preset, f"{key} missing x"
            assert "y" in preset, f"{key} missing y"
            assert "z" in preset, f"{key} missing z"


class TestPrintBedManagerActors:
    def test_create_actors_returns_list(self) -> None:
        mgr = PrintBedManager()
        actors = mgr.create_actors(220, 220, 250)
        assert isinstance(actors, list)
        assert len(actors) >= 2  # at least grid + box

    def test_create_actors_different_sizes(self) -> None:
        mgr = PrintBedManager()
        actors_small = mgr.create_actors(100, 100, 100)
        actors_large = mgr.create_actors(350, 350, 350)
        assert len(actors_small) >= 2
        assert len(actors_large) >= 2


class TestOverflowDetection:
    def test_no_overflow_when_model_fits(self) -> None:
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        text = get_overflow_text(220, 220, 250, bbox)
        assert text is None

    def test_overflow_x_only(self) -> None:
        bbox = BoundingBox(0, 0, 0, 300, 100, 100)
        text = get_overflow_text(220, 220, 250, bbox)
        assert text is not None
        assert "X" in text
        assert "80" in text  # 300 - 220 = 80

    def test_overflow_y_only(self) -> None:
        bbox = BoundingBox(0, 0, 0, 100, 300, 100)
        text = get_overflow_text(220, 220, 250, bbox)
        assert text is not None
        assert "Y" in text

    def test_overflow_z_only(self) -> None:
        bbox = BoundingBox(0, 0, 0, 100, 100, 400)
        text = get_overflow_text(220, 220, 250, bbox)
        assert text is not None
        assert "Z" in text
        assert "150" in text  # 400 - 250 = 150

    def test_overflow_multiple_axes(self) -> None:
        bbox = BoundingBox(0, 0, 0, 300, 300, 400)
        text = get_overflow_text(220, 220, 250, bbox)
        assert text is not None
        assert "X" in text
        assert "Y" in text
        assert "Z" in text

    def test_exact_fit_no_overflow(self) -> None:
        bbox = BoundingBox(0, 0, 0, 220, 220, 250)
        text = get_overflow_text(220, 220, 250, bbox)
        assert text is None


class TestOverflowActors:
    def test_no_overflow_actors_when_fits(self) -> None:
        mgr = PrintBedManager()
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        actors = mgr.create_overflow_actors(220, 220, 250, bbox)
        assert len(actors) == 0

    def test_overflow_actors_created_when_exceeds(self) -> None:
        mgr = PrintBedManager()
        bbox = BoundingBox(0, 0, 0, 300, 300, 400)
        actors = mgr.create_overflow_actors(220, 220, 250, bbox)
        assert len(actors) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_print_bed.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement PrintBedManager**

Create `src/meshscope/vtk_adapter/print_bed.py`:

```python
"""Print bed volume visualization: grid floor, wireframe box, overflow hatching."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkLine, vtkPolyData
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

if TYPE_CHECKING:
    from meshscope.core.mesh_data import BoundingBox

PRINTER_PRESETS: dict[str, dict] = {
    "ender_3": {"name": "Ender 3", "x": 220, "y": 220, "z": 250},
    "prusa_mk4": {"name": "Prusa MK4", "x": 250, "y": 210, "z": 210},
    "voron_2_4": {"name": "Voron 2.4", "x": 350, "y": 350, "z": 350},
    "bambu_x1c": {"name": "Bambu X1 Carbon", "x": 256, "y": 256, "z": 256},
    "bambu_p1s": {"name": "Bambu P1S", "x": 256, "y": 256, "z": 256},
}

GRID_COLOR = (0.227, 0.353, 0.227)  # #3a5a3a
BOX_COLOR = (0.353, 0.541, 0.353)  # #5a8a5a
OVERFLOW_COLOR = (0.6, 0.3, 0.3)  # muted red, hatching carries meaning

GRID_SPACING_MM = 10


def get_overflow_text(
    bed_x: int, bed_y: int, bed_z: int, bbox: BoundingBox
) -> str | None:
    """Return overflow description text, or None if model fits."""
    overflows = []
    dx = bbox.size_x - bed_x
    dy = bbox.size_y - bed_y
    dz = bbox.size_z - bed_z
    if dx > 0.01:
        overflows.append(f"X +{dx:.0f}mm")
    if dy > 0.01:
        overflows.append(f"Y +{dy:.0f}mm")
    if dz > 0.01:
        overflows.append(f"Z +{dz:.0f}mm")
    if not overflows:
        return None
    return f"Exceeds volume: {', '.join(overflows)}"


class PrintBedManager:
    """Creates VTK actors for print bed volume visualization."""

    def create_actors(self, x: int, y: int, z: int) -> list[vtkActor]:
        """Create grid floor + wireframe box actors for given bed dimensions."""
        actors = []
        actors.append(self._create_grid_floor(x, y))
        actors.append(self._create_wireframe_box(x, y, z))
        return actors

    def create_overflow_actors(
        self, bed_x: int, bed_y: int, bed_z: int, bbox: BoundingBox
    ) -> list[vtkActor]:
        """Create diagonal hatching actors for overflow regions on the floor."""
        actors = []
        dx = bbox.size_x - bed_x
        dy = bbox.size_y - bed_y

        # Only create floor hatching for X/Y overflow (Z overflow is text-only)
        if dx > 0.01:
            # Hatching on +X side of bed
            actors.append(
                self._create_hatching_rect(bed_x, 0, bed_x + dx, bed_y)
            )
        if dy > 0.01:
            # Hatching on +Y side of bed
            actors.append(
                self._create_hatching_rect(0, bed_y, bed_x, bed_y + dy)
            )
        if dx > 0.01 and dy > 0.01:
            # Corner hatching
            actors.append(
                self._create_hatching_rect(bed_x, bed_y, bed_x + dx, bed_y + dy)
            )
        return actors

    def _create_grid_floor(self, x: int, y: int) -> vtkActor:
        """Create a grid of lines on the Z=0 plane at GRID_SPACING_MM intervals."""
        points = vtkPoints()
        lines = vtkCellArray()

        # X-parallel lines (along Y axis)
        nx = x // GRID_SPACING_MM + 1
        for i in range(nx):
            gx = i * GRID_SPACING_MM
            p0 = points.InsertNextPoint(gx, 0, 0)
            p1 = points.InsertNextPoint(gx, y, 0)
            line = vtkLine()
            line.GetPointIds().SetId(0, p0)
            line.GetPointIds().SetId(1, p1)
            lines.InsertNextCell(line)

        # Y-parallel lines (along X axis)
        ny = y // GRID_SPACING_MM + 1
        for i in range(ny):
            gy = i * GRID_SPACING_MM
            p0 = points.InsertNextPoint(0, gy, 0)
            p1 = points.InsertNextPoint(x, gy, 0)
            line = vtkLine()
            line.GetPointIds().SetId(0, p0)
            line.GetPointIds().SetId(1, p1)
            lines.InsertNextCell(line)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*GRID_COLOR)
        actor.GetProperty().SetLineWidth(1.0)
        return actor

    def _create_wireframe_box(self, x: int, y: int, z: int) -> vtkActor:
        """Create the 12-edge wireframe box for the print volume."""
        points = vtkPoints()
        # 8 corners of the box
        corners = [
            (0, 0, 0), (x, 0, 0), (x, y, 0), (0, y, 0),
            (0, 0, z), (x, 0, z), (x, y, z), (0, y, z),
        ]
        for c in corners:
            points.InsertNextPoint(*c)

        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # bottom
            (4, 5), (5, 6), (6, 7), (7, 4),  # top
            (0, 4), (1, 5), (2, 6), (3, 7),  # verticals
        ]

        lines = vtkCellArray()
        for i0, i1 in edges:
            line = vtkLine()
            line.GetPointIds().SetId(0, i0)
            line.GetPointIds().SetId(1, i1)
            lines.InsertNextCell(line)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*BOX_COLOR)
        actor.GetProperty().SetLineWidth(1.5)
        return actor

    def _create_hatching_rect(
        self, x0: float, y0: float, x1: float, y1: float
    ) -> vtkActor:
        """Create diagonal hatching lines in a rectangle on the Z=0 plane."""
        points = vtkPoints()
        lines = vtkCellArray()
        spacing = GRID_SPACING_MM
        width = x1 - x0
        height = y1 - y0
        diag = width + height

        i = 0
        offset = spacing
        while offset < diag:
            # Diagonal line from bottom-left to top-right direction
            # Clip to rectangle bounds
            if offset <= width:
                sx = x0 + offset
                sy = y0
            else:
                sx = x1
                sy = y0 + (offset - width)

            if offset <= height:
                ex = x0
                ey = y0 + offset
            else:
                ex = x0 + (offset - height)
                ey = y1

            p0 = points.InsertNextPoint(sx, sy, 0.01)  # slight Z offset
            p1 = points.InsertNextPoint(ex, ey, 0.01)
            line = vtkLine()
            line.GetPointIds().SetId(0, p0)
            line.GetPointIds().SetId(1, p1)
            lines.InsertNextCell(line)

            offset += spacing
            i += 1

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*OVERFLOW_COLOR)
        actor.GetProperty().SetLineWidth(1.0)
        return actor
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_print_bed.py -v`
Expected: All 16 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/vtk_adapter/print_bed.py tests/unit/test_print_bed.py
git commit -m "feat(print-bed): add PrintBedManager with presets, grid, box, and overflow"
```

---

### Task 3: SceneManager integration

**Files:**
- Modify: `tests/unit/test_scene_manager.py`
- Modify: `src/meshscope/vtk_adapter/scene_manager.py`

- [ ] **Step 1: Write failing tests for SceneManager print bed methods**

Append to `tests/unit/test_scene_manager.py`:

```python
from meshscope.core.mesh_data import BoundingBox


class TestSceneManagerPrintBed:
    def test_print_bed_not_visible_initially(self, scene_manager):
        assert scene_manager.print_bed_visible is False

    def test_show_print_bed(self, scene_manager):
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        scene_manager.show_print_bed(220, 220, 250, bbox)
        assert scene_manager.print_bed_visible is True

    def test_hide_print_bed(self, scene_manager):
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        scene_manager.show_print_bed(220, 220, 250, bbox)
        scene_manager.hide_print_bed()
        assert scene_manager.print_bed_visible is False

    def test_show_print_bed_returns_overflow_text(self, scene_manager):
        bbox = BoundingBox(0, 0, 0, 300, 100, 100)
        text = scene_manager.show_print_bed(220, 220, 250, bbox)
        assert text is not None
        assert "X" in text

    def test_show_print_bed_returns_none_when_fits(self, scene_manager):
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        text = scene_manager.show_print_bed(220, 220, 250, bbox)
        assert text is None

    def test_clear_also_hides_print_bed(self, scene_manager):
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        scene_manager.show_print_bed(220, 220, 250, bbox)
        scene_manager.clear()
        assert scene_manager.print_bed_visible is False
```

NOTE: The test file likely has a `scene_manager` fixture already. Read the existing file to find the fixture name and adapt. If not, create one using a vtkRenderer.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_scene_manager.py::TestSceneManagerPrintBed -v`
Expected: FAIL — `AttributeError: 'SceneManager' object has no attribute 'print_bed_visible'`

- [ ] **Step 3: Implement SceneManager print bed methods**

Add to `src/meshscope/vtk_adapter/scene_manager.py`:

Import at top:
```python
from meshscope.core.mesh_data import BoundingBox
from meshscope.vtk_adapter.print_bed import PrintBedManager, get_overflow_text
```

In `__init__`, add:
```python
        self._print_bed_actors: list[vtkActor] = []
        self._print_bed_manager = PrintBedManager()
        self._print_bed_visible = False
```

Add methods:
```python
    def show_print_bed(
        self, x: int, y: int, z: int, bbox: BoundingBox
    ) -> str | None:
        """Show print bed volume overlay. Returns overflow text or None."""
        self.hide_print_bed()

        actors = self._print_bed_manager.create_actors(x, y, z)
        overflow_actors = self._print_bed_manager.create_overflow_actors(
            x, y, z, bbox
        )

        self._print_bed_actors = actors + overflow_actors
        for actor in self._print_bed_actors:
            self._renderer.AddActor(actor)

        self._print_bed_visible = True
        return get_overflow_text(x, y, z, bbox)

    def hide_print_bed(self) -> None:
        """Remove all print bed actors from the scene."""
        for actor in self._print_bed_actors:
            self._renderer.RemoveActor(actor)
        self._print_bed_actors.clear()
        self._print_bed_visible = False

    @property
    def print_bed_visible(self) -> bool:
        return self._print_bed_visible
```

Update `clear()` to also hide print bed:
```python
    def clear(self) -> None:
        """Remove all mesh actors from the scene."""
        if self._mesh_actor is not None:
            self._renderer.RemoveActor(self._mesh_actor)
            self._mesh_actor = None
        if self._wireframe_actor is not None:
            self._renderer.RemoveActor(self._wireframe_actor)
            self._wireframe_actor = None
        self._wireframe_overlay_enabled = False
        self._smooth_shading_enabled = False
        self.hide_print_bed()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_scene_manager.py -v`
Expected: All tests PASS (existing + 6 new)

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/vtk_adapter/scene_manager.py tests/unit/test_scene_manager.py
git commit -m "feat(print-bed): integrate PrintBedManager into SceneManager"
```

---

### Task 4: MainWindow — bed toggle, preset dropdown, custom dialog

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Modify: `src/meshscope/ui/main_window.py`

- [ ] **Step 1: Write failing tests for MainWindow print bed integration**

Append to `tests/ui/test_main_window.py`:

```python
from PySide6.QtWidgets import QComboBox


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_main_window.py::TestMainWindowPrintBed -v`
Expected: FAIL — `AttributeError: 'MainWindow' object has no attribute 'bed_action'`

- [ ] **Step 3: Implement MainWindow print bed integration**

Modify `src/meshscope/ui/main_window.py`:

Add imports:
```python
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
from meshscope.core.config import AppConfig, load_config, save_config
from meshscope.vtk_adapter.print_bed import PRINTER_PRESETS
```

In `__init__`, after info panel setup and before `_create_actions()`:
```python
        # Config
        self._config = load_config()
```

In `_create_actions`, add after export_action:
```python
        self.bed_action = QAction("Bed", self)
        self.bed_action.setShortcut(QKeySequence("P"))
        self.bed_action.setCheckable(True)
        self.bed_action.setEnabled(False)
        self.bed_action.setToolTip("Toggle print bed volume overlay")
        self.bed_action.toggled.connect(self._on_bed_toggled)
```

In `_create_menus`, add to view_menu after info toggle:
```python
        view_menu.addSeparator()
        view_menu.addAction(self.bed_action)
```

In `_create_toolbar`, add after fit_action:
```python
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.bed_action)

        # Preset dropdown
        self.bed_preset_combo = QComboBox()
        self.bed_preset_combo.setAccessibleName("Print bed preset")
        self.bed_preset_combo.setEnabled(False)
        for key, preset in PRINTER_PRESETS.items():
            self.bed_preset_combo.addItem(preset["name"], key)
        self.bed_preset_combo.addItem("Custom...", "custom")
        # Set to saved preset
        saved_preset = self._config.get("print_bed", "preset")
        for i in range(self.bed_preset_combo.count()):
            if self.bed_preset_combo.itemData(i) == saved_preset:
                self.bed_preset_combo.setCurrentIndex(i)
                break
        self.bed_preset_combo.currentIndexChanged.connect(self._on_bed_preset_changed)
        self.toolbar.addWidget(self.bed_preset_combo)
```

In `_set_render_actions_enabled`, add:
```python
        self.bed_action.setEnabled(enabled)
        self.bed_preset_combo.setEnabled(enabled)
        if not enabled:
            self.bed_action.setChecked(False)
```

Add handler methods:
```python
    def _on_bed_toggled(self, checked: bool) -> None:
        """Toggle print bed volume overlay."""
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
        """Handle preset dropdown change."""
        key = self.bed_preset_combo.itemData(index)
        if key == "custom":
            if not self._show_custom_bed_dialog():
                # Revert to previous preset
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

        # Refresh bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

    def _get_bed_dimensions(self) -> tuple[int, int, int]:
        """Get current bed dimensions from preset or custom config."""
        key = self.bed_preset_combo.itemData(
            self.bed_preset_combo.currentIndex()
        )
        if key == "custom":
            return (
                self._config.get("print_bed", "custom_x"),
                self._config.get("print_bed", "custom_y"),
                self._config.get("print_bed", "custom_z"),
            )
        preset = PRINTER_PRESETS.get(key, PRINTER_PRESETS["ender_3"])
        return (preset["x"], preset["y"], preset["z"])

    def _show_custom_bed_dialog(self) -> bool:
        """Show custom bed size dialog. Returns True if accepted."""
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
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False

        x_val = x_spin.value()
        y_val = y_spin.value()
        z_val = z_spin.value()

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
```

Also update `_load_file` to recalculate overflow when bed is visible. After `self._set_state_success(...)`:
```python
        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_main_window.py tests/unit/test_config.py tests/unit/test_print_bed.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/meshscope/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat(print-bed): integrate bed toggle, preset dropdown, and custom dialog into MainWindow"
```

---

### Task 5: Manual smoke test and final verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run linting and type checking**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && ruff check src/meshscope/core/config.py src/meshscope/vtk_adapter/print_bed.py src/meshscope/vtk_adapter/scene_manager.py src/meshscope/ui/main_window.py && mypy src/meshscope/core/config.py src/meshscope/vtk_adapter/print_bed.py`
Expected: No errors

- [ ] **Step 3: Launch the application and visually verify**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m meshscope tests/fixtures/valid/cube.stl`

Verify:
- Bed toggle (P) shows wireframe box + grid floor
- Cube (10x10x10) fits easily in Ender 3 (220x220x250) — no overflow
- Switch to a small preset or use Custom with 5x5x5 to verify overflow hatching + status bar text
- Preset dropdown changes bed size when toggled on
- Custom... opens dialog with X/Y/Z spinboxes
- Bed hides when toggled off
- Bed disabled when no mesh loaded

- [ ] **Step 4: Record the feature**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && bash scripts/test-gate.sh --record-feature "print-bed-visualization"`

- [ ] **Step 5: Commit any final fixes if needed**
