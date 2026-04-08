"""Tests for mesh transform logic."""

import numpy as np

from meshscope.core.exceptions import MeshTransformError
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_transform import (
    TransformResult,
    _recompute_metadata,
    mirror_mesh,
    rotate_mesh,
    scale_mesh,
)


class TestMeshTransformError:
    def test_has_user_message(self) -> None:
        err = MeshTransformError("Scale factor must be greater than zero.")
        assert err.user_message == "Scale factor must be greater than zero."

    def test_is_exception(self) -> None:
        err = MeshTransformError("msg")
        assert isinstance(err, Exception)

    def test_str_matches_user_message(self) -> None:
        err = MeshTransformError("msg")
        assert str(err) == "msg"


class TestTransformResultDataclass:
    def test_creation(self) -> None:
        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)

        result = TransformResult(
            mesh=mesh,
            description="Scaled by 2.0x",
            warning=None,
        )
        assert result.description == "Scaled by 2.0x"
        assert result.warning is None

    def test_is_frozen(self) -> None:
        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)
        result = TransformResult(mesh, "test", None)
        try:
            result.description = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass

    def test_with_warning(self) -> None:
        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)
        result = TransformResult(mesh, "Scaled by 20000.0x", "Model is now very large")
        assert result.warning == "Model is now very large"


def _make_cube_vertices() -> np.ndarray:
    """Unit cube 0-10mm on each axis."""
    return np.array(
        [
            [0, 0, 0],
            [10, 0, 0],
            [10, 10, 0],
            [0, 10, 0],
            [0, 0, 10],
            [10, 0, 10],
            [10, 10, 10],
            [0, 10, 10],
        ],
        dtype=np.float32,
    )


def _make_cube_faces() -> np.ndarray:
    """12 triangles forming a watertight cube."""
    return np.array(
        [
            [0, 2, 1],
            [0, 3, 2],
            [4, 5, 6],
            [4, 6, 7],
            [0, 1, 5],
            [0, 5, 4],
            [2, 3, 7],
            [2, 7, 6],
            [0, 4, 7],
            [0, 7, 3],
            [1, 2, 6],
            [1, 6, 5],
        ],
        dtype=np.uint32,
    )


class TestRecomputeMetadata:
    def test_bounding_box(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        assert meta.bounding_box.min_x == 0.0
        assert meta.bounding_box.max_x == 10.0
        assert meta.bounding_box.min_y == 0.0
        assert meta.bounding_box.max_y == 10.0
        assert meta.bounding_box.min_z == 0.0
        assert meta.bounding_box.max_z == 10.0

    def test_vertex_and_face_counts(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        assert meta.vertex_count == 8
        assert meta.face_count == 12

    def test_surface_area(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        # 10mm cube: 6 faces * 100mm^2 = 600mm^2
        assert abs(meta.surface_area_mm2 - 600.0) < 0.1

    def test_volume_manifold(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        # 10mm cube: 1000mm^3
        assert meta.volume_mm3 is not None
        assert abs(meta.volume_mm3 - 1000.0) < 0.1

    def test_volume_non_manifold_is_none(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=False)
        assert meta.volume_mm3 is None


def _make_cube_mesh() -> MeshData:
    """Watertight 10mm cube for transform tests."""
    verts = _make_cube_vertices()
    faces = _make_cube_faces()
    normals = np.zeros((12, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 12, bb, 600.0, 1000.0, True)
    return MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)


class TestScaleMesh:
    def test_scale_doubles_vertices(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert result.mesh.vertices.max() == 20.0
        assert result.mesh.vertices.min() == 0.0

    def test_scale_halves_vertices(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 0.5)
        assert result.mesh.vertices.max() == 5.0

    def test_scale_updates_bounding_box(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert result.mesh.metadata.bounding_box.max_x == 20.0
        assert result.mesh.metadata.bounding_box.max_y == 20.0
        assert result.mesh.metadata.bounding_box.max_z == 20.0

    def test_scale_surface_area_scales_by_factor_squared(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 3.0)
        # 600 * 3^2 = 5400
        assert abs(result.mesh.metadata.surface_area_mm2 - 5400.0) < 1.0

    def test_scale_volume_scales_by_factor_cubed(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        # 1000 * 2^3 = 8000
        assert result.mesh.metadata.volume_mm3 is not None
        assert abs(result.mesh.metadata.volume_mm3 - 8000.0) < 1.0

    def test_scale_zero_raises(self) -> None:
        mesh = _make_cube_mesh()
        try:
            scale_mesh(mesh, 0.0)
            raise AssertionError("Should have raised MeshTransformError")
        except MeshTransformError as e:
            assert "greater than zero" in e.user_message

    def test_scale_negative_raises(self) -> None:
        mesh = _make_cube_mesh()
        try:
            scale_mesh(mesh, -1.0)
            raise AssertionError("Should have raised MeshTransformError")
        except MeshTransformError as e:
            assert "greater than zero" in e.user_message

    def test_scale_returns_transform_result(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert isinstance(result, TransformResult)
        assert "2.0" in result.description

    def test_scale_extreme_returns_warning(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 20000.0)
        assert result.warning is not None

    def test_scale_preserves_face_count(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert result.mesh.metadata.face_count == 12

    def test_scale_preserves_manifold(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert result.mesh.metadata.is_manifold is True


class TestRotateMesh:
    def test_rotate_90_z_swaps_xy(self) -> None:
        """90° CCW around Z: (10,0,0) centered=(5,-5,0) -> rot=(5,5,0) -> (10,10,0)."""
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "z", 90.0)
        # Vertex (10,0,0) should rotate to (10,10,0)
        expected = np.array([10, 10, 0], dtype=np.float32)
        dists = np.linalg.norm(result.mesh.vertices - expected, axis=1)
        assert dists.min() < 0.01, "Vertex (10,0,0) should have rotated to (10,10,0)"
        # Z coordinates unchanged by Z-axis rotation
        np.testing.assert_allclose(
            np.sort(result.mesh.vertices[:, 2]),
            np.sort(mesh.vertices[:, 2]),
            atol=1e-4,
        )

    def test_rotate_360_returns_to_original(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "x", 360.0)
        np.testing.assert_allclose(result.mesh.vertices, mesh.vertices, atol=1e-4)

    def test_rotate_180_twice_returns_to_original(self) -> None:
        mesh = _make_cube_mesh()
        result1 = rotate_mesh(mesh, "y", 180.0)
        result2 = rotate_mesh(result1.mesh, "y", 180.0)
        np.testing.assert_allclose(result2.mesh.vertices, mesh.vertices, atol=1e-4)

    def test_rotate_preserves_face_count(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "x", 45.0)
        assert result.mesh.metadata.face_count == 12

    def test_rotate_preserves_surface_area(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "z", 30.0)
        assert abs(result.mesh.metadata.surface_area_mm2 - 600.0) < 1.0

    def test_rotate_preserves_volume(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "y", 45.0)
        assert result.mesh.metadata.volume_mm3 is not None
        assert abs(result.mesh.metadata.volume_mm3 - 1000.0) < 1.0

    def test_rotate_returns_transform_result(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "x", 90.0)
        assert isinstance(result, TransformResult)
        assert "90" in result.description
        assert "X" in result.description

    def test_rotate_invalid_axis_raises(self) -> None:
        mesh = _make_cube_mesh()
        try:
            rotate_mesh(mesh, "w", 90.0)
            raise AssertionError("Should have raised MeshTransformError")
        except MeshTransformError as e:
            assert "axis" in e.user_message.lower()

    def test_rotate_normals_recomputed(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "x", 90.0)
        # Normals should be unit vectors
        norms = np.linalg.norm(result.mesh.normals, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-5)


class TestMirrorMesh:
    def test_mirror_x_negates_x_coordinates(self) -> None:
        mesh = _make_cube_mesh()
        center_x = mesh.vertices[:, 0].mean()
        result = mirror_mesh(mesh, "x")
        # Each vertex X should be reflected around center
        expected_x = 2 * center_x - mesh.vertices[:, 0]
        np.testing.assert_allclose(result.mesh.vertices[:, 0], expected_x, atol=1e-5)

    def test_mirror_y_negates_y_coordinates(self) -> None:
        mesh = _make_cube_mesh()
        center_y = mesh.vertices[:, 1].mean()
        result = mirror_mesh(mesh, "y")
        expected_y = 2 * center_y - mesh.vertices[:, 1]
        np.testing.assert_allclose(result.mesh.vertices[:, 1], expected_y, atol=1e-5)

    def test_mirror_z_negates_z_coordinates(self) -> None:
        mesh = _make_cube_mesh()
        center_z = mesh.vertices[:, 2].mean()
        result = mirror_mesh(mesh, "z")
        expected_z = 2 * center_z - mesh.vertices[:, 2]
        np.testing.assert_allclose(result.mesh.vertices[:, 2], expected_z, atol=1e-5)

    def test_mirror_reverses_face_winding(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "x")
        # Columns 1 and 2 should be swapped
        np.testing.assert_array_equal(result.mesh.faces[:, 1], mesh.faces[:, 2])
        np.testing.assert_array_equal(result.mesh.faces[:, 2], mesh.faces[:, 1])

    def test_mirror_twice_returns_to_original(self) -> None:
        mesh = _make_cube_mesh()
        result1 = mirror_mesh(mesh, "x")
        result2 = mirror_mesh(result1.mesh, "x")
        np.testing.assert_allclose(result2.mesh.vertices, mesh.vertices, atol=1e-5)
        # Face winding should be back to original after double swap
        np.testing.assert_array_equal(result2.mesh.faces, mesh.faces)

    def test_mirror_preserves_bounding_box_size(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "y")
        bb = result.mesh.metadata.bounding_box
        assert abs(bb.max_x - bb.min_x - 10.0) < 0.1
        assert abs(bb.max_y - bb.min_y - 10.0) < 0.1
        assert abs(bb.max_z - bb.min_z - 10.0) < 0.1

    def test_mirror_preserves_surface_area(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "z")
        assert abs(result.mesh.metadata.surface_area_mm2 - 600.0) < 1.0

    def test_mirror_preserves_volume(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "x")
        assert result.mesh.metadata.volume_mm3 is not None
        assert abs(result.mesh.metadata.volume_mm3 - 1000.0) < 1.0

    def test_mirror_returns_transform_result(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "x")
        assert isinstance(result, TransformResult)
        assert "X" in result.description

    def test_mirror_invalid_axis_raises(self) -> None:
        mesh = _make_cube_mesh()
        try:
            mirror_mesh(mesh, "w")
            raise AssertionError("Should have raised MeshTransformError")
        except MeshTransformError as e:
            assert "axis" in e.user_message.lower()
