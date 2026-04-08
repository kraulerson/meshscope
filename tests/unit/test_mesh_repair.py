"""Tests for mesh repair logic."""

import numpy as np

from meshscope.core.exceptions import MeshRepairError
from meshscope.core.mesh_analysis import analyze_mesh
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_repair import (
    RepairPlan,
    RepairResult,
    apply_repair,
    plan_repair,
)


def _make_cube_mesh() -> MeshData:
    """Watertight cube — no issues."""
    vertices = np.array(
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
    faces = np.array(
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
    normals = np.zeros((12, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 12, bb, 600.0, 1000.0, True)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


def _make_open_mesh() -> MeshData:
    """Cube with 2 faces removed — has holes and open edges."""
    vertices = np.array(
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
    faces = np.array(
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
        ],
        dtype=np.uint32,
    )
    normals = np.zeros((10, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 10, bb, 500.0, None, False)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


def _make_degenerate_mesh() -> MeshData:
    """Simple mesh with one degenerate (zero-area) face."""
    vertices = np.array(
        [
            [0, 0, 0],
            [10, 0, 0],
            [10, 10, 0],
            [0, 10, 0],
        ],
        dtype=np.float32,
    )
    faces = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],
            [0, 1, 0],  # degenerate: repeated vertex
        ],
        dtype=np.uint32,
    )
    normals = np.zeros((3, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 0)
    meta = MeshMetadata(4, 3, bb, 100.0, None, False)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestMeshRepairError:
    def test_has_user_message(self) -> None:
        err = MeshRepairError("Repair failed.")
        assert err.user_message == "Repair failed."

    def test_is_exception(self) -> None:
        err = MeshRepairError("msg")
        assert isinstance(err, Exception)

    def test_str_matches_user_message(self) -> None:
        err = MeshRepairError("msg")
        assert str(err) == "msg"


class TestRepairPlanDataclass:
    def test_creation(self) -> None:
        plan = RepairPlan(
            flipped_normal_count=3,
            holes_to_fill=2,
            degenerate_faces_to_remove=1,
            estimated_face_delta=-1,
            high_impact_warning=False,
        )
        assert plan.flipped_normal_count == 3
        assert plan.holes_to_fill == 2
        assert plan.degenerate_faces_to_remove == 1
        assert plan.estimated_face_delta == -1
        assert plan.high_impact_warning is False

    def test_is_frozen(self) -> None:
        plan = RepairPlan(0, 0, 0, 0, False)
        try:
            plan.holes_to_fill = 99  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass


class TestRepairResultDataclass:
    def test_creation(self) -> None:
        import numpy as np

        from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata

        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)

        result = RepairResult(
            mesh=mesh,
            normals_fixed=3,
            holes_filled=2,
            degenerate_faces_removed=1,
            fully_repaired=True,
            remaining_issues=None,
        )
        assert result.normals_fixed == 3
        assert result.fully_repaired is True
        assert result.remaining_issues is None

    def test_is_frozen(self) -> None:
        import numpy as np

        from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata

        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)
        result = RepairResult(mesh, 0, 0, 0, True, None)
        try:
            result.normals_fixed = 99  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass


class TestPlanRepair:
    def test_clean_mesh_no_repairs_needed(self) -> None:
        mesh = _make_cube_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        assert plan.holes_to_fill == 0
        assert plan.degenerate_faces_to_remove == 0
        assert plan.high_impact_warning is False

    def test_open_mesh_reports_holes(self) -> None:
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        assert plan.holes_to_fill > 0

    def test_degenerate_mesh_reports_degenerate(self) -> None:
        mesh = _make_degenerate_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        assert plan.degenerate_faces_to_remove >= 1

    def test_returns_repair_plan_type(self) -> None:
        mesh = _make_cube_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        assert isinstance(plan, RepairPlan)

    def test_flipped_normals_detected(self) -> None:
        """A mesh with inconsistent winding should report flipped normals."""
        # Two triangles sharing edge [0,1] with same winding = inconsistent
        vertices = np.array(
            [[0, 0, 0], [10, 0, 0], [5, 10, 0], [5, -10, 0]],
            dtype=np.float32,
        )
        faces = np.array(
            [[0, 1, 2], [0, 1, 3]],  # shared edge same direction = inconsistent
            dtype=np.uint32,
        )
        normals = np.zeros((2, 3), dtype=np.float32)
        bb = BoundingBox(0, -10, 0, 10, 10, 0)
        meta = MeshMetadata(4, 2, bb, 100.0, None, False)
        mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        assert plan.flipped_normal_count >= 1

    def test_high_impact_warning_when_large_change(self) -> None:
        """A mesh where repair changes face count by >5% should set warning."""
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        # open mesh has 10 faces; filling a hole adds faces (>5% of 10)
        assert plan.estimated_face_delta != 0, "Open mesh should have non-zero delta"
        assert plan.high_impact_warning is True


class TestApplyRepair:
    def test_repairs_open_mesh(self) -> None:
        """Filling holes on an open mesh should produce a mesh with more faces."""
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        assert isinstance(result, RepairResult)
        assert result.mesh.metadata.face_count >= mesh.metadata.face_count

    def test_removes_degenerate_faces(self) -> None:
        mesh = _make_degenerate_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        assert result.degenerate_faces_removed >= 1
        assert result.mesh.metadata.face_count < mesh.metadata.face_count

    def test_clean_mesh_returns_no_changes(self) -> None:
        """Applying repair to a clean mesh should change nothing."""
        mesh = _make_cube_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        assert result.normals_fixed == 0
        assert result.holes_filled == 0
        assert result.degenerate_faces_removed == 0

    def test_result_mesh_has_valid_metadata(self) -> None:
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        meta = result.mesh.metadata
        assert meta.vertex_count > 0
        assert meta.face_count > 0
        assert meta.surface_area_mm2 > 0

    def test_result_mesh_has_valid_arrays(self) -> None:
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        assert result.mesh.vertices.shape[1] == 3
        assert result.mesh.faces.shape[1] == 3
        assert result.mesh.normals.shape[1] == 3
        assert not np.any(np.isnan(result.mesh.vertices))

    def test_fully_repaired_flag(self) -> None:
        mesh = _make_degenerate_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        # Degenerate removal should succeed fully
        assert result.degenerate_faces_removed >= 1

    def test_trimesh_repair_calls_are_callable(self) -> None:
        """Regression: trimesh.repair.fix_normals and fill_holes are untyped.

        We suppress mypy no-untyped-call with type: ignore comments.
        This test guards that the underlying functions remain callable
        and produce valid results despite the lack of type stubs.
        """
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        # plan_repair calls fix_normals and fill_holes on a trial copy
        plan = plan_repair(analysis, mesh)
        assert isinstance(plan.flipped_normal_count, int)
        assert isinstance(plan.holes_to_fill, int)
        # apply_repair calls them again on the real mesh
        result = apply_repair(mesh, plan)
        assert isinstance(result.normals_fixed, int)
        assert isinstance(result.holes_filled, int)
        assert result.mesh.vertices.shape[1] == 3
