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
        assert len(actors) >= 2

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
        assert "80" in text

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
        assert "150" in text

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

    def test_z_overflow_creates_ceiling_hatching(self) -> None:
        mgr = PrintBedManager()
        bbox = BoundingBox(0, 0, 0, 100, 100, 400)  # only Z overflows
        actors = mgr.create_overflow_actors(220, 220, 250, bbox)
        assert len(actors) >= 1  # ceiling hatching actor

    def test_no_z_hatching_when_z_fits(self) -> None:
        mgr = PrintBedManager()
        bbox = BoundingBox(0, 0, 0, 300, 100, 100)  # only X overflows
        actors = mgr.create_overflow_actors(220, 220, 250, bbox)
        # Should have X floor hatching but no Z ceiling hatching
        assert len(actors) == 1
