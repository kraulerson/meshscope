"""Tests for load_mesh — full loading pipeline."""

from pathlib import Path

import numpy as np
import pytest

from meshscope.core.exceptions import CorruptFileError, EmptyMeshError
from meshscope.core.mesh_document import MeshDocument
from meshscope.core.mesh_loader import load_mesh

FIXTURES = Path(__file__).parent.parent / "fixtures"
VALID = FIXTURES / "valid"
INVALID = FIXTURES / "invalid"


class TestLoadMeshSuccess:
    def test_load_stl_binary(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        assert isinstance(doc, MeshDocument)
        assert doc.mesh.metadata.face_count == 12
        assert doc.mesh.metadata.vertex_count == 8
        assert doc.mesh.vertices.dtype == np.float32
        assert doc.mesh.faces.dtype == np.uint32
        assert doc.source_format == "stl"

    def test_load_stl_ascii(self) -> None:
        doc = load_mesh(VALID / "cube_ascii.stl")
        assert doc.mesh.metadata.face_count == 12
        assert doc.source_format == "stl"

    def test_load_obj(self) -> None:
        doc = load_mesh(VALID / "cube.obj")
        assert doc.mesh.metadata.face_count == 12
        assert doc.mesh.metadata.vertex_count == 8
        assert doc.source_format == "obj"

    def test_load_ply(self) -> None:
        doc = load_mesh(VALID / "cube.ply")
        assert doc.mesh.metadata.face_count == 12
        assert doc.source_format == "ply"

    def test_load_3mf(self) -> None:
        doc = load_mesh(VALID / "cube.3mf")
        assert doc.mesh.metadata.face_count == 12
        assert doc.source_format == "3mf"

    def test_bounding_box_correct(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        bb = doc.mesh.metadata.bounding_box
        assert bb.size_x == pytest.approx(10.0, abs=0.01)
        assert bb.size_y == pytest.approx(10.0, abs=0.01)
        assert bb.size_z == pytest.approx(10.0, abs=0.01)

    def test_surface_area_computed(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        # Cube 10x10x10: surface area = 6 * 100 = 600
        assert doc.mesh.metadata.surface_area_mm2 == pytest.approx(600.0, rel=0.01)

    def test_volume_computed_for_manifold(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        # Cube 10x10x10: volume = 1000
        assert doc.mesh.metadata.volume_mm3 is not None
        assert doc.mesh.metadata.volume_mm3 == pytest.approx(1000.0, rel=0.01)

    def test_manifold_status(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        assert doc.mesh.metadata.is_manifold is True

    def test_normals_shape_matches_faces(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        assert doc.mesh.normals.shape == (doc.mesh.metadata.face_count, 3)

    def test_original_mesh_preserved(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        assert np.array_equal(doc.original_mesh.vertices, doc.mesh.vertices)
        assert doc.original_mesh is not doc.mesh


class TestLoadMeshWarnings:
    def test_obj_with_materials_produces_warning(self) -> None:
        doc = load_mesh(VALID / "cube_with_materials.obj")
        assert len(doc.warnings) >= 1
        warning_text = " ".join(doc.warnings)
        assert "not supported" in warning_text.lower()

    def test_unit_mismatch_tiny_mesh(self, tmp_path: Path) -> None:
        """Mesh with all dimensions < 1mm triggers unit mismatch warning."""
        tiny_obj = tmp_path / "tiny.obj"
        tiny_obj.write_text(
            "v 0 0 0\nv 0.5 0 0\nv 0.5 0.5 0\nv 0 0.5 0\nf 1 2 3\nf 1 3 4\n"
        )
        doc = load_mesh(tiny_obj)
        warning_text = " ".join(doc.warnings)
        assert "unit mismatch" in warning_text.lower()

    def test_unit_mismatch_huge_mesh(self, tmp_path: Path) -> None:
        """Mesh with any dimension > 10,000mm triggers unit mismatch warning."""
        huge_obj = tmp_path / "huge.obj"
        huge_obj.write_text(
            "v 0 0 0\nv 20000 0 0\nv 20000 20000 0\nv 0 20000 0\nf 1 2 3\nf 1 3 4\n"
        )
        doc = load_mesh(huge_obj)
        warning_text = " ".join(doc.warnings)
        assert "unit mismatch" in warning_text.lower()

    def test_no_warning_for_normal_mesh(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        warning_text = " ".join(doc.warnings)
        assert "unit mismatch" not in warning_text.lower()


class TestLoadMeshErrors:
    def test_corrupt_stl(self) -> None:
        with pytest.raises(CorruptFileError):
            load_mesh(INVALID / "corrupt.stl")

    def test_zero_faces_stl(self) -> None:
        with pytest.raises(EmptyMeshError, match="0 faces"):
            load_mesh(INVALID / "zero_faces.stl")

    def test_bad_3mf_archive(self) -> None:
        with pytest.raises(CorruptFileError):
            load_mesh(INVALID / "bad_archive.3mf")

    def test_empty_ply(self) -> None:
        with pytest.raises((CorruptFileError, EmptyMeshError)):
            load_mesh(INVALID / "empty_file.ply")
