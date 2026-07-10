"""Tests for mesh export functionality."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from meshscope.core.exceptions import MeshExportError
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_exporter import check_symlink, export_mesh, get_format_warning
from meshscope.core.mesh_loader import load_mesh


class TestMeshExportError:
    def test_is_exception(self) -> None:
        err = MeshExportError("test error")
        assert isinstance(err, Exception)

    def test_has_user_message(self) -> None:
        err = MeshExportError("Export failed: permission denied")
        assert err.user_message == "Export failed: permission denied"


def _make_mesh() -> MeshData:
    """Create a simple triangle MeshData for export testing."""
    vertices = np.array(
        [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
        dtype=np.float32,
    )
    faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32)
    normals = np.array([[0, 0, 1], [0, 0, 1]], dtype=np.float32)
    bb = BoundingBox(0.0, 0.0, 0.0, 10.0, 10.0, 0.0)
    meta = MeshMetadata(
        vertex_count=4,
        face_count=2,
        bounding_box=bb,
        surface_area_mm2=100.0,
        volume_mm3=None,
        is_manifold=False,
    )
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestExportMeshSTL:
    def test_export_stl_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "output.stl"
        export_mesh(_make_mesh(), out, "stl")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_export_stl_binary_format(self, tmp_path: Path) -> None:
        out = tmp_path / "output.stl"
        export_mesh(_make_mesh(), out, "stl")
        data = out.read_bytes()
        assert len(data) == 80 + 4 + 2 * 50  # 2 triangles


class TestExportMeshOBJ:
    def test_export_obj_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "output.obj"
        export_mesh(_make_mesh(), out, "obj")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_export_obj_contains_vertices(self, tmp_path: Path) -> None:
        out = tmp_path / "output.obj"
        export_mesh(_make_mesh(), out, "obj")
        content = out.read_text()
        assert "v " in content
        assert "f " in content


class TestExportMesh3MF:
    def test_export_3mf_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "output.3mf"
        export_mesh(_make_mesh(), out, "3mf")
        assert out.exists()
        assert out.stat().st_size > 0


class TestExportMeshPLY:
    def test_export_ply_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "output.ply"
        export_mesh(_make_mesh(), out, "ply")
        assert out.exists()
        assert out.stat().st_size > 0


class TestExportMeshAtomicWrite:
    def test_no_temp_file_left_on_success(self, tmp_path: Path) -> None:
        out = tmp_path / "output.stl"
        export_mesh(_make_mesh(), out, "stl")
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].name == "output.stl"

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason=(
            "needs POSIX permissions: on Windows os.chmod is ignored for "
            "directories, so the directory stays writable and the export "
            "correctly succeeds"
        ),
    )
    def test_export_to_readonly_dir_raises(self, tmp_path: Path) -> None:
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)
        out = readonly_dir / "output.stl"
        try:
            export_mesh(_make_mesh(), out, "stl")
            raise AssertionError("Should have raised MeshExportError")
        except MeshExportError as e:
            assert (
                "Cannot write" in e.user_message
                or "Permission" in e.user_message
                or "denied" in e.user_message.lower()
                or "Export failed" in e.user_message
            )
        finally:
            readonly_dir.chmod(0o755)


class TestExportMeshUnsupportedFormat:
    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        out = tmp_path / "output.xyz"
        try:
            export_mesh(_make_mesh(), out, "xyz")
            raise AssertionError("Should have raised MeshExportError")
        except MeshExportError as e:
            assert "Unsupported" in e.user_message


class TestCheckSymlink:
    def test_regular_path_returns_none(self, tmp_path: Path) -> None:
        target = tmp_path / "output.stl"
        assert check_symlink(target) is None

    def test_symlink_returns_resolved_path(self, tmp_path: Path) -> None:
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real_dir)
        target = link / "output.stl"
        resolved = check_symlink(target)
        assert resolved is not None
        assert "real" in str(resolved)


class TestGetFormatWarning:
    def test_obj_has_warning(self) -> None:
        warning = get_format_warning("obj")
        assert warning is not None
        assert "normal" in warning.lower()

    def test_stl_has_no_warning(self) -> None:
        assert get_format_warning("stl") is None

    def test_3mf_has_no_warning(self) -> None:
        assert get_format_warning("3mf") is None

    def test_ply_has_no_warning(self) -> None:
        assert get_format_warning("ply") is None


class TestExportRoundTrip:
    """Load a fixture, export to each format, reload, verify geometry preserved."""

    def test_roundtrip_stl(self, tmp_path: Path) -> None:
        doc = load_mesh(Path("tests/fixtures/valid/cube.stl"))
        out = tmp_path / "cube_export.stl"
        export_mesh(doc.mesh, out, "stl")
        reloaded = load_mesh(out)
        assert reloaded.mesh.metadata.vertex_count == doc.mesh.metadata.vertex_count
        assert reloaded.mesh.metadata.face_count == doc.mesh.metadata.face_count

    def test_roundtrip_obj(self, tmp_path: Path) -> None:
        doc = load_mesh(Path("tests/fixtures/valid/cube.stl"))
        out = tmp_path / "cube_export.obj"
        export_mesh(doc.mesh, out, "obj")
        reloaded = load_mesh(out)
        assert reloaded.mesh.metadata.face_count == doc.mesh.metadata.face_count

    def test_roundtrip_ply(self, tmp_path: Path) -> None:
        doc = load_mesh(Path("tests/fixtures/valid/cube.stl"))
        out = tmp_path / "cube_export.ply"
        export_mesh(doc.mesh, out, "ply")
        reloaded = load_mesh(out)
        assert reloaded.mesh.metadata.face_count == doc.mesh.metadata.face_count

    def test_roundtrip_3mf(self, tmp_path: Path) -> None:
        doc = load_mesh(Path("tests/fixtures/valid/cube.stl"))
        out = tmp_path / "cube_export.3mf"
        export_mesh(doc.mesh, out, "3mf")
        reloaded = load_mesh(out)
        assert reloaded.mesh.metadata.face_count == doc.mesh.metadata.face_count
